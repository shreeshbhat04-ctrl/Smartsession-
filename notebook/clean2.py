import json

filepath = r'c:\Users\shree\intern\1\Smartsession-\notebook\mediapipe_test2.ipynb'

with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

# Try truncating at different points, going much earlier
for check_pos in range(4000, 1000, -200):
    test_content = content[:check_pos] + ']}' 
    try:
        data = json.loads(test_content)
        print(f'SUCCESS: Valid JSON at position {check_pos} with {len(data["cells"])} cells')
        
        with open(filepath, 'w') as f:
            f.write(test_content)
        print('File cleaned!')
        break
    except:
        if check_pos % 400 == 0:
            print(f'Still searching... position {check_pos}')
