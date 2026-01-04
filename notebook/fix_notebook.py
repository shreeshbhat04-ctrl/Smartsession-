import json

filepath = r'c:\Users\shree\intern\1\Smartsession-\notebook\mediapipe_test2.ipynb.backup'

# Read the file with lenient error handling
with open(filepath, 'rb') as f:
    content_bytes = f.read()

# Try to decode, replacing bad bytes
content = content_bytes.decode('utf-8', errors='replace')

# Find the last valid JSON position
found = False
for end_pos in range(len(content)-1, len(content)//2, -1):
    if end_pos % 50000 == 0:
        print(f'Scanning... position {end_pos}')
    try:
        test_content = content[:end_pos] + ']}' 
        json.loads(test_content)
        print(f'Found valid JSON up to position {end_pos}')
        
        # Write the cleaned version
        cleaned = content[:end_pos] + ']}'
        with open(r'c:\Users\shree\intern\1\Smartsession-\notebook\mediapipe_test2.ipynb', 'w', encoding='utf-8') as f:
            f.write(cleaned)
        print('Notebook file cleaned and restored!')
        found = True
        break
    except:
        continue

if not found:
    print('Could not find valid JSON structure. File may be too corrupted.')
