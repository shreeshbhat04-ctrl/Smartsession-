import json

filepath = r'c:\Users\shree\intern\1\Smartsession-\notebook\mediapipe_test2.ipynb'

with open(filepath, 'r', encoding='utf-8', errors='ignore') as f:
    content = f.read()

print(f"File size: {len(content)} characters")

# Try truncating at different points
for check_pos in range(5500, 4000, -100):
    test_content = content[:check_pos] + ']}' 
    try:
        data = json.loads(test_content)
        print(f'SUCCESS: Valid JSON at position {check_pos} with {len(data["cells"])} cells')
        
        with open(filepath, 'w') as f:
            f.write(test_content)
        break
    except json.JSONDecodeError as e:
        print(f'Position {check_pos}: Error - {e.msg}')
    except Exception as e:
        print(f'Position {check_pos}: {type(e).__name__}')
