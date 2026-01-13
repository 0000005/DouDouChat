import os
import csv
import json
import time
import requests
from http import HTTPStatus
from dashscope import ImageSynthesis
import dashscope

# Configuration
API_KEY = "sk-fb10541ae6914de192742281dfac8d88"
CSV_PATH = r"e:\workspace\code\DouDouChat\dev-docs\temp\preset_friends_list.csv"
JSON_PATH = r"e:\workspace\code\DouDouChat\dev-docs\temp\generated_personas_text.json"
OUTPUT_DIR = r"e:\workspace\code\DouDouChat\server\static\avatars\presets"
CHECKPOINT_PATH = r"e:\workspace\code\DouDouChat\dev-docs\temp\avatar_generation_checkpoint.json"

# ONLY these characters will be generated
TARGET_NAMES = [
    '何以琛', '韩商言', '周生辰', '凌不疑', '李峋', '段嘉许', '黎深', '澹台烬', '封腾', '东华帝君', 
    '佟年', '乔晶晶', '程少商', '盛明兰', '小兰花', '朱韵', '桑稚', '许沁', '薛杉杉', '黄亦玫'
]

dashscope.api_key = API_KEY
dashscope.base_http_api_url = 'https://dashscope.aliyuncs.com/api/v1'
MAX_RETRIES = 3

def sanitize_filename(name):
    return name.replace("/", "_").replace("\\", "_").replace("·", "_").replace(" ", "_")

def generate_avatar(name, prompt):
    print(f"Generating FOCUSED avatar for: {name}...")
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
                
                filename = f"{sanitize_filename(name)}.png"
                file_path = os.path.join(OUTPUT_DIR, filename)
                
                response = requests.get(img_url, timeout=30)
                if response.status_code == 200:
                    with open(file_path, 'wb') as f:
                        f.write(response.content)
                    print(f"Successfully saved to {file_path}")
                    return f"static/avatars/presets/{filename}"
                else:
                    print(f"[{attempt+1}/{MAX_RETRIES}] Download fail: {img_url}")
            else:
                print(f"[{attempt+1}/{MAX_RETRIES}] API Error: {rsp.code} - {rsp.message}")
        except Exception as e:
            print(f"[{attempt+1}/{MAX_RETRIES}] Error: {str(e)}")
        
        if attempt < MAX_RETRIES - 1:
            time.sleep((attempt + 1) * 5)
    return None

def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    
    # Load checkpoint
    checkpoint = {}
    if os.path.exists(CHECKPOINT_PATH):
        with open(CHECKPOINT_PATH, 'r', encoding='utf-8') as f:
            checkpoint = json.load(f)
            
    # Read characters from CSV but FILTER by TARGET_NAMES
    to_process = []
    with open(CSV_PATH, mode='r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        for row in reader:
            name = row.get('name', '').strip()
            if name in TARGET_NAMES:
                to_process.append({'name': name, 'prompt': row['头像生成提示词'].strip()})
    
    print(f"Focused generation for {len(to_process)} AI personas.")
    
    for char in to_process:
        name = char['name']
        # Even in focused mode, check if somehow already done in this run
        if name in checkpoint and os.path.exists(os.path.join(OUTPUT_DIR, sanitize_filename(name) + ".png")):
            print(f"Skipping {name} (already exists)")
            continue
            
        res = generate_avatar(name, char['prompt'])
        if res:
            checkpoint[name] = res
            with open(CHECKPOINT_PATH, 'w', encoding='utf-8') as f:
                json.dump(checkpoint, f, ensure_ascii=False, indent=2)
            
            # Update main JSON immediately for these specific ones
            if os.path.exists(JSON_PATH):
                with open(JSON_PATH, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                if name in data:
                    data[name]['avatar'] = res
                    with open(JSON_PATH, 'w', encoding='utf-8') as f:
                        json.dump(data, f, ensure_ascii=False, indent=2)
            
            time.sleep(2)
        else:
            print(f"Failed all retries for {name}")
            time.sleep(5)

if __name__ == "__main__":
    main()
