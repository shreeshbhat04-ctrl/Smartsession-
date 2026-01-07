import warnings
warnings.filterwarnings('ignore', category=UserWarning)
# Standard Library Imports
import math
import time as time_module
from time import time as now
from collections import deque
# Data Science & Vision Imports
import cv2
import numpy as np
import pandas as pd
import mediapipe as mp
import joblib
# MediaPipe Tasks
from mediapipe.tasks import python
from mediapipe.tasks.python import vision
# --- LANDMARK CONSTANTS ---
# Gaze & Eye Landmarks (refined landmarks)
RIGHT_IRIS_CENTER = 474      # Right iris/pupil center
LEFT_IRIS_CENTER = 468       # Left iris/pupil center  
RIGHT_EYE_INNER = 263        # Right eye inner corner (near nose)
LEFT_EYE_INNER = 362         # Left eye inner corner (near nose)
RIGHT_EYE_OUTER = 133        # Right eye outer corner
LEFT_EYE_OUTER = 33          # Left eye outer corner 
# Vertical Gaze specific
RIGHT_EYE_TOP = 386          # Upper eyelid reference
RIGHT_EYE_BOTTOM = 374       # Lower eyelid reference
# Brow Landmarks
LEFT_BROW_INNER = 107        # Left eyebrow inner point  
RIGHT_BROW_INNER = 336       # Right eyebrow inner point
# Face Contour
LEFT_FACE_CONTOUR = 234      # Left jaw/cheek extreme
RIGHT_FACE_CONTOUR = 454     # Right jaw/cheek extreme
# Mouth Landmarks
UPPER_LEFT_LIP_CORNER = 61   # Upper outer lip left corner
LOWER_RIGHT_LIP_CORNER = 291 # Lower outer lip right corner (code pairs with 61)
UPPER_INNER_LIP_CENTER = 13  # Top inner lip center
LOWER_INNER_LIP_CENTER = 14  # Bottom inner lip center
# Nose
NOSE_TIP = 1                 # Nose tip (smile reference)
# EUCLIDEAN DISTANCE FUNCTION
def euclid(p1, p2):
    return math.hypot(p1.x - p2.x, p1.y - p2.y)
# Load the trained classifier
try:
    clf = joblib.load("app/model/confusion_tree.joblib")
    print("Model loaded:", type(clf))
except Exception as e:
    print(f"Warning: Model not found. {e}")
    clf = None
# Initialize MediaPipe Face Landmarker
base_options = python.BaseOptions(
    model_asset_path="app/core/face_landmarker.task"   # Ensure this file exists
)
options = vision.FaceLandmarkerOptions(
    base_options=base_options,
    running_mode=vision.RunningMode.VIDEO,
    num_faces=1,
    output_face_blendshapes=False
)
detector = vision.FaceLandmarker.create_from_options(options)

class StudentIntegrityMonitor:
    def __init__(self, detector=detector, clf=clf, gaze_limit=4.5):
        self.detector = detector
        self.clf = clf
        self.gaze_limit = gaze_limit  # seconds before flagging "looking away"
        self.look_away_st = None  
        self.pred_buffer = deque(maxlen=7)  # smoothing buffer for ML predictions
        self.frame_count = 0
        self.last_timestamp_ms = 0  
    # FEATURE EXTRACTION METHODS 
    def analyze_frame(self, image_bytes: bytes):
    # decode bytes → OpenCV frame
        np_arr = np.frombuffer(image_bytes, np.uint8)
        frame = cv2.imdecode(np_arr, cv2.IMREAD_COLOR)

        if frame is None:
                 return {
                 "state": "No Frame",
                    "score": 0,
                     "gaze": "CENTER"
        }

        state, label, gaze, feats = self.process(frame)

        return {
                    "state": state,
                    "label": label,
                    "gaze": gaze,
                    "score": feats.get("brow", 0) if feats else 0,
                    "features": feats
                }

    def browratio(self, lm):
        return euclid(lm[LEFT_BROW_INNER], lm[RIGHT_BROW_INNER]) / euclid(lm[LEFT_FACE_CONTOUR], lm[RIGHT_FACE_CONTOUR])
    def mouthfeature(self, lm):
        left, right = lm[UPPER_LEFT_LIP_CORNER], lm[LOWER_RIGHT_LIP_CORNER]
        top, bottom = lm[UPPER_INNER_LIP_CENTER], lm[LOWER_INNER_LIP_CENTER]
        nose = lm[NOSE_TIP]
        facewidth = euclid(lm[LEFT_FACE_CONTOUR], lm[RIGHT_FACE_CONTOUR])
        if facewidth == 0: return 0, 0, 0
        mouth_w = euclid(left, right) / facewidth
        mouth_open = euclid(top, bottom) / facewidth
        smile_up = (nose.y - (left.y + right.y) / 2) / facewidth
        return mouth_w, mouth_open, smile_up
    def headroll(self, lm):
        L, R = lm[LEFT_FACE_CONTOUR], lm[RIGHT_FACE_CONTOUR]
        return math.degrees(math.atan2(R.y - L.y, R.x - L.x))
    #  DETECTION METHODS 
    def is_happy(self, lm):
        left = lm[UPPER_LEFT_LIP_CORNER]
        right = lm[LOWER_RIGHT_LIP_CORNER]
        top = lm[UPPER_INNER_LIP_CENTER]
        bottom = lm[LOWER_INNER_LIP_CENTER]
        face_l = lm[LEFT_FACE_CONTOUR]
        face_r = lm[RIGHT_FACE_CONTOUR]
        facewidth = euclid(face_l, face_r)
        if facewidth == 0:
            return False    
        mouthwidth = euclid(left, right) / facewidth
        mouthopen = euclid(top, bottom) / facewidth
        smileup = ((left.y + right.y) / 2 - lm[NOSE_TIP].y) / facewidth
        return (
            (mouthwidth > 0.33 and mouthopen > 0.02) or
            smileup < -0.3
        )
    def get_vertical_gaze(self, lm):
        iris = lm[RIGHT_IRIS_CENTER]
        upper = lm[RIGHT_EYE_TOP]
        lower = lm[RIGHT_EYE_BOTTOM]    
        eye_height = euclid(upper, lower)
        if eye_height == 0:
            return "CENTER"
        ratio = euclid(iris, upper) / eye_height
        if ratio < 0.35:
            return "UP"
        elif ratio > 0.65:
            return "DOWN"
        return "CENTER"
    def get_gaze(self, landmarks):
        # Horizontal 
        iris = landmarks[RIGHT_IRIS_CENTER]
        inner = landmarks[RIGHT_EYE_INNER]
        outer = landmarks[LEFT_EYE_INNER] 
        eye_width = euclid(inner, outer)
        gaze_h = "CENTER"
        if eye_width != 0:
            ratio_h = euclid(iris, inner) / eye_width
            if ratio_h < 0.2:
                gaze_h = "RIGHT"
            elif ratio_h > 0.8:
                gaze_h = "LEFT"     
        #  Vertical 
        gaze_v = self.get_vertical_gaze(landmarks)
        # Merge 
        if gaze_h != "CENTER":
            return gaze_h
        if gaze_v != "CENTER":
            return gaze_v
        return "CENTER"
    def brow_confusion_rule(self, landmarks):
        #Rule-based confusion detection using brow position
        brow_l = landmarks[LEFT_BROW_INNER]
        brow_r = landmarks[RIGHT_BROW_INNER]
        face_l = landmarks[LEFT_FACE_CONTOUR]
        face_r = landmarks[RIGHT_FACE_CONTOUR]
        facewidth = euclid(face_l, face_r)
        if facewidth == 0:
            return False, 0.0   
        brow_dist = euclid(brow_l, brow_r)
        ratio = brow_dist / facewidth
        Brow_confusion = 0.15  # threshold
        return ratio < Brow_confusion, ratio
    def predict(self, lm):
        #ML prediction for confusion
        if self.clf is None:
            return 0, {} # Fallback if model not loaded
        brow = self.browratio(lm)
        mouth_w, mouth_open, smile_up = self.mouthfeature(lm)
        head_roll_abs = abs(self.headroll(lm)) 
        X = pd.DataFrame(
            [[brow, mouth_w, mouth_open, smile_up, head_roll_abs]],
            columns=self.clf.feature_names_in_
        )
        pred = self.clf.predict(X)[0]  # 1=>confused, 0=>not confused
        return pred, {
            "brow": brow,
            "smile_up": smile_up,
            "roll": head_roll_abs
        }
    def smooth_prediction(self, pred):
        #Smooth ML predictions using majority voting over 7 frames
        self.pred_buffer.append(pred)
        return sum(self.pred_buffer) >= (len(self.pred_buffer) // 2 + 1)
    # processing each frame
    def process(self, frame):
        self.frame_count += 1
        current_time_ms = int(time_module.time() * 1000)
        if current_time_ms <= self.last_timestamp_ms:
            timestamp_ms = self.last_timestamp_ms + 1
        else:
            timestamp_ms = current_time_ms
        self.last_timestamp_ms = timestamp_ms
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        mp_image = mp.Image(
            image_format=mp.ImageFormat.SRGB,
            data=rgb
        )
        result = self.detector.detect_for_video(mp_image, timestamp_ms)
        gaze = "CENTER"
        feats = {}
        #  INTEGRITY CHECKS 
        if not result.face_landmarks:
            return "No Face", "No Face", gaze, feats  
        if len(result.face_landmarks) > 1:
            return "Multiple Faces", "Alert", gaze, feats 
        landmarks = result.face_landmarks[0]
        # GAZE (INTEGRITY+TIME)
        gaze = self.get_gaze(landmarks)
        if gaze != "CENTER":
            if self.look_away_st is None:
                self.look_away_st = now()
            elif now() - self.look_away_st > self.gaze_limit:
                return "Looking Away", "Alert", gaze, feats
        else:
            self.look_away_st = None
        # ---- CONFUSION (ML FIRST + SMOOTHING) ----
        pred, feats = self.predict(landmarks)
        confused = self.smooth_prediction(pred)
        if confused:
            return "Confused", "Confused", gaze, feats
        #  CONFUSION 
        rule_confused, ratio = self.brow_confusion_rule(landmarks)
        if rule_confused or ratio < 0.05:
            return "Confused", "Confused", gaze, feats
        # HAPPY(RULE-BASEDOVERRIDE)
        if self.is_happy(landmarks):
            return "Happy", "Happy", gaze, feats
        # DEFAULT 
        return "Focused", "Focused", gaze, feats