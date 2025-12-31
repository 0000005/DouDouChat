"""
简化版 SSE 测试 - 只打印关键时间点和前20个chunk结构
"""
import time
import sqlite3
import httpx
import json

def get_llm_config():
    conn = sqlite3.connect("data/doudou.db")
    cursor = conn.cursor()
    cursor.execute("SELECT base_url, api_key, model_name FROM llm_configs WHERE deleted = 0 ORDER BY id DESC LIMIT 1")
    row = cursor.fetchone()
    conn.close()
    return {"base_url": row[0], "api_key": row[1], "model_name": row[2]}

def test():
    config = get_llm_config()
    url = f"{config['base_url'].rstrip('/')}/chat/completions"
    headers = {
        "Authorization": f"Bearer {config['api_key']}",
        "Content-Type": "application/json",
    }
    payload = {
        "model": config["model_name"],
        "messages": [
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": "Say hi in 5 words."},
        ],
        "stream": True,
    }
    
    print(f"Model: {config['model_name']}")
    print(f"Request start: {time.strftime('%H:%M:%S')}")
    t0 = time.perf_counter()
    
    results = []
    
    with httpx.Client(timeout=60.0) as client:
        with client.stream("POST", url, headers=headers, json=payload) as resp:
            t_conn = time.perf_counter() - t0
            print(f"Connection established: {t_conn:.3f}s")
            
            for line in resp.iter_lines():
                if not line or not line.startswith("data: "):
                    continue
                data_str = line[6:]
                if data_str == "[DONE]":
                    break
                    
                t_now = time.perf_counter() - t0
                try:
                    data = json.loads(data_str)
                    choices = data.get("choices", [])
                    if choices:
                        delta = choices[0].get("delta", {})
                        # Check what fields are in delta
                        fields = list(delta.keys())
                        content = delta.get("content", "")
                        reasoning = delta.get("reasoning_content", "")
                        
                        results.append({
                            "time": t_now,
                            "fields": fields,
                            "content": content[:20] if content else "",
                            "has_reasoning": bool(reasoning),
                        })
                except:
                    pass
    
    t_total = time.perf_counter() - t0
    
    print(f"\nTotal chunks: {len(results)}")
    print(f"Total time: {t_total:.3f}s")
    
    # Find first chunk with content
    first_content_idx = None
    for i, r in enumerate(results):
        if r["content"]:
            first_content_idx = i
            break
    
    print(f"\n=== First 15 chunks structure ===")
    for i, r in enumerate(results[:15]):
        print(f"  #{i+1} [{r['time']:.3f}s] fields={r['fields']}, content={repr(r['content'])}, reasoning={r['has_reasoning']}")
    
    if first_content_idx and first_content_idx > 15:
        print(f"\n=== First content chunk (#{first_content_idx+1}) ===")
        r = results[first_content_idx]
        print(f"  [{r['time']:.3f}s] fields={r['fields']}, content={repr(r['content'])}")
    
    print(f"\n=== Summary ===")
    print(f"  First chunk at: {results[0]['time']:.3f}s")
    if first_content_idx is not None:
        print(f"  First CONTENT chunk at: {results[first_content_idx]['time']:.3f}s (chunk #{first_content_idx+1})")
        print(f"  Chunks before content: {first_content_idx} (all reasoning)")

if __name__ == "__main__":
    test()
