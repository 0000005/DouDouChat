"""
Memory Extraction 调试工具

这不是一个传统的单元测试，而是一个帮助调试和优化 Prompt 的可视化工具。
运行此脚本后，您将在终端看到：
1. 发送给大模型的完整 Prompt（包含 System Prompt、Few-shot 和当前对话）
2. 大模型的原始返回结果
3. 最终提取出来的 Profile 和 Event

您可以根据输出结果，手动调整 Prompt 文件，然后再次运行测试，形成迭代优化循环。

Usage:
    cd server
    venv\\Scripts\\python tests/test_memory_extraction_complex.py
    
    # 或者运行单个场景
    venv\\Scripts\\python tests/test_memory_extraction_complex.py scenario5_long_work
"""
import os
import sys
import asyncio
import logging
import json
import uuid
import json
from pathlib import Path
from datetime import datetime

# ==============================================================================
# 环境初始化：确保能导入 app 模块
# ==============================================================================
SERVER_DIR = Path(__file__).resolve().parents[1]
if str(SERVER_DIR) not in sys.path:
    sys.path.insert(0, str(SERVER_DIR))

from app.core.config import settings
from app.services.memo import initialize_memo_sdk, MemoService
from app.vendor.memobase_server.models.blob import OpenAICompatibleMessage
from app.vendor.memobase_server.controllers.buffer import flush_buffer
from app.vendor.memobase_server.models.blob import BlobType
from app.vendor.memobase_server.env import CONFIG
from app.vendor.memobase_server.connectors import create_tables
from app.vendor.memobase_server.controllers.project import update_project_profile_config
from app.vendor.memobase_server.prompts.profile_init_utils import UserProfileTopic
from app.vendor.memobase_server.env import ProfileConfig

# ==============================================================================
# 日志配置：开启记忆系统的底层日志，显示发送给大模型的 Prompt 和返回结果
# ==============================================================================
def setup_test_logging():
    # 获取底层 prompt 追踪记录器
    prompt_logger = logging.getLogger("prompt_trace")
    prompt_logger.setLevel(logging.INFO)
    
    # 获取 Memobase 系统记录器
    mb_logger = logging.getLogger("memobase_server")
    mb_logger.setLevel(logging.INFO)
    
    # 统一输出到标准输出，方便在测试中查看
    handler = logging.StreamHandler(sys.stdout)
    formatter = logging.Formatter('%(asctime)s [%(levelname)s] %(name)s: %(message)s')
    handler.setFormatter(formatter)
    
    prompt_logger.addHandler(handler)
    mb_logger.addHandler(handler)
    
    # 禁用可能存在的其他处理器，避免重复打印
    prompt_logger.propagate = False
    mb_logger.propagate = False

    # 猴子补丁：监控 llm_complete 以便打印返回值
    from app.vendor.memobase_server import llms
    original_llm_complete = llms.llm_complete
    
    async def patched_llm_complete(*args, **kwargs):
        result = await original_llm_complete(*args, **kwargs)
        if result.ok():
            data_to_log = result.data()
            if isinstance(data_to_log, dict):
                data_to_log = json.dumps(data_to_log, ensure_ascii=False, indent=2)
            
            # 获取本次调用的 Prompt (为了调试方便，只打印最后 User 部分，防止 System Prompt 刷屏)
            user_prompt = kwargs.get('prompt', 'N/A')
            if len(str(user_prompt)) > 500:
                user_prompt = str(user_prompt)[:500] + "...(truncated)"
                
            separator = "#" * 80
            print(f"\n{separator}", flush=True)
            print(f"🧐 [DEBUG VIEW] LLM RAW INTERACTION ({kwargs.get('prompt_id', 'unknown')})", flush=True)
            print(f"{separator}", flush=True)
            print(f"👉 INPUT PROMPT (Snippet):\n{user_prompt}\n", flush=True)
            print(f"👈 RAW MODEL OUTPUT:\n{data_to_log}", flush=True)
            print(f"{separator}\n", flush=True)
            
            # 依然保留原有日志记录，以防万一
            prompt_logger.info(f"--- LLM RESPONSE ---\n{data_to_log}\n--------------------")
        else:
            print(f"\n❌ [LLM ERROR]: {result.msg()}\n")
            prompt_logger.error(f"--- LLM ERROR ---\n{result.msg()}\n-----------------")
        return result
    
    llms.llm_complete = patched_llm_complete

setup_test_logging()

# ==============================================================================
# 测试数据加载函数
# ==============================================================================
def load_scenario(name: str) -> list[OpenAICompatibleMessage]:
    """从 txt 文件加载对话数据"""
    path = SERVER_DIR / "tests" / "data" / "memory_test" / f"{name}.txt"
    messages = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line: continue
            
            # 处理带时间的格式: [2026/01/15 10:00] user: message
            time_prefix = ""
            if line.startswith("["):
                end_bracket = line.find("]")
                if end_bracket != -1:
                    time_prefix = line[:end_bracket+1] + " "
                    line = line[end_bracket+1:].strip()
            
            if line.lower().startswith("user:"):
                content = line[5:].strip()
                messages.append(OpenAICompatibleMessage(role="user", content=time_prefix + content))
            elif line.lower().startswith("assistant:"):
                content = line[10:].strip()
                messages.append(OpenAICompatibleMessage(role="assistant", content=time_prefix + content))
    return messages

def list_scenarios() -> list[str]:
    """列出所有可用的测试场景"""
    path = SERVER_DIR / "tests" / "data" / "memory_test"
    path = SERVER_DIR / "tests" / "data" / "memory_test"
    return [f.stem for f in path.glob("*.txt")]

async def initialize_test_profiles(space_id: str):
    """注入测试用的 Profile 结构（更符合社交场景）"""
    print(f"\n[Setup] 🔧 Injecting custom profile topics for space: {space_id}...")
    
    custom_profiles = [
        UserProfileTopic(
            "基本信息",
            sub_topics=["姓名", "年龄", "性别", "所在地", "家乡", "语言"]
        ),
        UserProfileTopic(
            "职业与教育",
            sub_topics=["职业", "公司", "学校", "专业", "工作状态", "职业目标"]
        ),
        UserProfileTopic(
            "兴趣爱好",
            sub_topics=["运动", "音乐", "电影", "阅读", "游戏", "旅游", "美食"]
        ),
        UserProfileTopic(
            "生活习惯",
            sub_topics=["作息", "饮食偏好", "消费习惯", "居住环境"]
        ),
        UserProfileTopic(
            "性格与情感",
            sub_topics=["性格特点", "当前心情", "压力源", "情感状态"]
        ),
        UserProfileTopic(
            "人际关系",
            sub_topics=["家人", "伴侣", "朋友", "同事", "宠物"]
        ),
        UserProfileTopic(
            "重要经历",
            sub_topics=["过去", "近期计划", "长远目标"]
        )
    ]
    
    # 手动将 UserProfileTopic 对象转换为字典，确保 sub_topics 正确序列化
    # 避免 direct json.dumps 失败
    overwrite_config = []
    for p in custom_profiles:
        p_dict = {
            "topic": p.topic,
            "description": p.description,
            "sub_topics": []
        }
        for st in p.sub_topics:
            # st 是 SubTopic Pydantic Model 或者字典
            if hasattr(st, "model_dump"):
                p_dict["sub_topics"].append(st.model_dump(exclude_none=True))
            elif hasattr(st, "__dict__"):
                p_dict["sub_topics"].append(st.__dict__)
            else:
                 p_dict["sub_topics"].append(st)
        overwrite_config.append(p_dict)

    # 构造 ProfileConfig 对象并序列化为 JSON 字符串
    config = ProfileConfig(overwrite_user_profiles=overwrite_config)
    config_str = json.dumps(config.__dict__, default=lambda o: o.__dict__)

    await update_project_profile_config(
        space_id, 
        profile_config=config_str
    )
    print("[Setup] ✅ Custom profiles injected.")

# ==============================================================================
# 核心执行函数
# ==============================================================================
async def run_extraction_cycle(user_id: str, space_id: str, scenario_name: str):
    """
    执行一个完整的提取周期：载入数据 -> 插入 -> 手动触发提取 -> 打印结果
    
    这个函数不做任何断言，只打印结果供人工判断。
    """
    print("\n" + "="*80)
    print(f">>> SCENARIO: {scenario_name}")
    print("="*80)
    
    messages = load_scenario(scenario_name)
    print(f"\n[Step 0] Loaded {len(messages)} messages from {scenario_name}.txt")
    print("-" * 40)
    for i, msg in enumerate(messages):
        role_display = "👤 USER" if msg.role == "user" else "🤖 ASSISTANT"
        print(f"  {i+1:02d}. {role_display}: {msg.content[:60]}{'...' if len(msg.content) > 60 else ''}")
    print("-" * 40)
    
    # 1. 插入对话到缓冲区
    await MemoService.ensure_user(user_id, space_id)
    await MemoService.insert_chat(user_id, space_id, messages)
    print(f"\n[Step 1] ✅ Inserted {len(messages)} messages to buffer.")
    
    # 2. 手动触发缓冲区刷新（提取记忆）
    print(f"\n[Step 2] 🔄 Triggering buffer flush (LLM processing)...")
    print("         (Watch for 'memobase_llm_prompt' logs below)")
    print("-" * 40)
    
    p = await flush_buffer(user_id, space_id, BlobType.chat)
    
    print("-" * 40)
    if not p.ok():
        print(f"\n[Error] ❌ Flush failed: {p.msg()}")
        return
    print(f"\n[Step 3] ✅ LLM Processing Complete.")
    
    # 3. 获取提取出来的 Profile 和 Events
    profiles = await MemoService.get_user_profiles(user_id, space_id)
    events = await MemoService.get_recent_memories(user_id, space_id, topk=50)
    
    # 4. 打印 Profile 结果
    print("\n" + "="*80)
    print("📋 EXTRACTED PROFILES (User Attributes)")
    print("="*80)
    if profiles.profiles:
        for i, p in enumerate(profiles.profiles):
            topic = p.attributes.get('topic', 'N/A')
            sub_topic = p.attributes.get('sub_topic', 'N/A')
            print(f"  {i+1:02d}. [{topic}/{sub_topic}]")
            print(f"      Content: {p.content}")
            print(f"      Updated: {p.updated_at}")
            print()
    else:
        print("  (No profiles extracted)")
    
    # 5. 打印 Event 结果
    print("\n" + "="*80)
    print("📅 EXTRACTED EVENTS (User Activities/Facts)")
    print("="*80)
    if events.gists:
        for i, g in enumerate(events.gists):
            gist_data = g.gist_data if isinstance(g.gist_data, dict) else g.gist_data.model_dump()
            summary = gist_data.get('summary', gist_data.get('content', 'N/A'))
            print(f"  {i+1:02d}. {summary}")
            print(f"      Created: {g.created_at}")
            print()
    else:
        print("  (No events extracted)")
    
    print("\n" + "="*80)
    print(f">>> END OF SCENARIO: {scenario_name}")
    print("="*80 + "\n")
    
    return profiles, events


async def main():
    """主入口函数"""
    sys.stdout.reconfigure(encoding='utf-8')

    # ==========================================================================
    # 配置测试环境的 LLM (基于用户每提供的 GLM-4.7 配置)
    # ==========================================================================
    settings.MEMOBASE_LLM_API_KEY = "4dce12de026450fe6d485bdff7847cde.pVqEddmkBZjdBSs6"
    settings.MEMOBASE_LLM_BASE_URL = "https://api.z.ai/api/coding/paas/v4"
    settings.MEMOBASE_BEST_LLM_MODEL = "glm-4.7"
    
    # 同时也设置环境变量，确保底层库能读到
    os.environ["MEMOBASE_LLM_API_KEY"] = settings.MEMOBASE_LLM_API_KEY
    os.environ["MEMOBASE_LLM_BASE_URL"] = settings.MEMOBASE_LLM_BASE_URL
    os.environ["MEMOBASE_BEST_LLM_MODEL"] = settings.MEMOBASE_BEST_LLM_MODEL

    # 检查 API KEY
    if not settings.MEMOBASE_LLM_API_KEY:
        print("❌ ERROR: MEMOBASE_LLM_API_KEY not set in environment.")
        print("Please set it in .env or as environment variable.")
        sys.exit(1)
    
    # 初始化 SDK
    print("\n🚀 Initializing Memobase SDK with real LLM...")
    await initialize_memo_sdk()
    create_tables()
    print("✅ SDK Initialized.\n")
    
    # 确定要运行的场景
    available_scenarios = list_scenarios()
    print(f"📂 Available scenarios: {', '.join(available_scenarios)}")
    
    # 命令行参数指定场景
    if len(sys.argv) > 1:
        selected = [s for s in sys.argv[1:] if s in available_scenarios]
        if not selected:
            print(f"❌ No valid scenarios specified. Available: {available_scenarios}")
            sys.exit(1)
    else:
        # 默认运行所有场景
        selected = available_scenarios
    
    print(f"🎯 Running scenarios: {', '.join(selected)}\n", flush=True)
    
    # 使用唯一的 user_id 避免污染
    user_id = str(uuid.uuid4())
    space_id = "__root__"
    
    print(f"👤 Test User ID: {user_id}", flush=True)
    print(f"🏠 Test Space ID: {space_id}", flush=True)
    
    # 注入自定义 Profile 结构
    await initialize_test_profiles(space_id)
    
    # 依次运行每个场景
    for scenario in sorted(selected):
        print(f"DEBUG: Entering loop for {scenario}", flush=True)
        try:
            await run_extraction_cycle(user_id, space_id, scenario)
        except Exception as e:
            print(f"\n❌ Error in scenario {scenario}: {e}", flush=True)
            import traceback
            traceback.print_exc()
    
    print("\n" + "="*80, flush=True)
    print("🏁 ALL SCENARIOS COMPLETE", flush=True)
    print("="*80, flush=True)
    print("\nNow you can review the results above and adjust your prompts in:", flush=True)
    print("  - server/app/vendor/memobase_server/prompts/zh_summary_entry_chats.py", flush=True)
    print("  - server/app/vendor/memobase_server/prompts/zh_extract_profile.py", flush=True)
    print("  - server/app/vendor/memobase_server/prompts/event_tagging.py", flush=True)
    print("\nThen run this script again to see the effect of your changes.", flush=True)

if __name__ == "__main__":
    asyncio.run(main())
