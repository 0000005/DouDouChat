import os
import csv
import json
import time
import requests
from pathlib import Path
from http import HTTPStatus
from urllib.parse import urlparse, unquote
from dashscope import ImageSynthesis
import dashscope

# Configuration
API_KEY = "sk-fb10541ae6914de192742281dfac8d88"
CSV_PATH = r"e:\workspace\code\DouDouChat\dev-docs\temp\preset_friends_list.csv"
JSON_PATH = r"e:\workspace\code\DouDouChat\dev-docs\temp\generated_personas_text.json"
OUTPUT_DIR = r"e:\workspace\code\DouDouChat\server\static\avatars\presets"
CHECKPOINT_PATH = r"e:\workspace\code\DouDouChat\dev-docs\temp\avatar_generation_checkpoint.json"

dashscope.api_key = API_KEY
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'

def sanitize_filename(name):
    """Sanitize name for filename use."""
    return name.replace("/", "_").replace("\\", "_").replace("·", "_").replace(" ", "_")

def load_checkpoint():
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {}

def save_checkpoint(checkpoint):
    with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
        json.dump(checkpoint, f, ensure_ascii=False, indent=2)

MAX_RETRIES = 3

def generate_avatar(name, prompt):
    print(f"Generating avatar for: {name}...")
    for attempt in range(MAX_RETRIES):
        try:
            rsp = ImageSynthesis.call(
                model="qwen-image-plus",
                prompt=prompt,
                n=1,
                size='1024*1024',
                prompt_extend=True,
                watermark=False
            )
            
            if rsp.status_code == HTTPStatus.OK:
                result = rsp.output.results[0]
                img_url = result.url
                
                # Save image
                file_ext = ".png"
                filename = f"{sanitize_filename(name)}{file_ext}"
                file_path = os.path.join(OUTPUT_DIR, filename)
                
                response = requests.get(img_url, timeout=30)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f"Successfully saved to {file_path}")
                    return f"static/avatars/presets/{filename}"
                else:
                    print(f"[{attempt+1}/{MAX_RETRIES}] Failed to download image from {img_url}")
            else:
                print(f"[{attempt+1}/{MAX_RETRIES}] API Error: {rsp.code} - {rsp.message}")
                
        except Exception as e:
            print(f"[{attempt+1}/{MAX_RETRIES}] Error during generation for {name}: {str(e)}")
        
        if attempt < MAX_RETRIES - 1:
            wait_time = (attempt + 1) * 5
            print(f"Waiting {wait_time}s before retrying...")
            time.sleep(wait_time)
            
    return None

def main():
    # Ensure output directory exists
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load data
    checkpoint = load_checkpoint()
    
    # Read CSV
    characters = []
    with open(CSV_PATH, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            if row.get('name') and row.get('头像生成提示词'):
                characters.append({
                    'name': row['name'].strip(),
                    'prompt': row['头像生成提示词'].strip()
                })
    
    print(f"Total characters to process: {len(characters)}")
    
    # Process
    success_count = 0
    for i, char in enumerate(characters):
        name = char['name']
        if name in checkpoint and os.path.exists(os.path.join(OUTPUT_DIR, os.path.basename(checkpoint[name]))):
            print(f"[{i+1}/{len(characters)}] Skipping {name} (already done)")
            continue
            
        avatar_path = generate_avatar(name, char['prompt'])
        if avatar_path:
            checkpoint[name] = avatar_path
            save_checkpoint(checkpoint)
            success_count += 1
            # Rate limiting / Sleep avoid overwhelming
            time.sleep(2) 
        else:
            print(f"[{i+1}/{len(characters)}] Failed to generate avatar for {name}")
            time.sleep(5) # Longer wait on failure
            
    # Update main JSON file
    if os.path.exists(JSON_PATH):
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            persona_data = json.load(f)
        
        updated_count = 0
        for name, avatar_rel_path in checkpoint.items():
            if name in persona_data:
                persona_data[name]['avatar'] = avatar_rel_path
                updated_count += 1
        
        with open(JSON_PATH, 'w', encoding='utf-8') as f:
            json.dump(persona_data, f, ensure_ascii=False, indent=2)
        
        print(f"Updated {updated_count} personas in {JSON_PATH}")
    else:
        print(f"Warning: {JSON_PATH} not found, couldn't update.")

    print(f"Finished. Successfully generated {success_count} new avatars.")

if __name__ == "__main__":
    main()
