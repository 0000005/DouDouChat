import asyncio
import json
from openai import AsyncOpenAI
from agents import Agent, Runner, set_default_openai_client, set_default_openai_api
from agents.items import ReasoningItem
from agents.stream_events import RunItemStreamEvent
from openai.types.responses import ResponseTextDeltaEvent

async def verify_reasoning():
    # 1. Setup API
    base_url = "https://api.z.ai/api/coding/paas/v4/"
    api_key = "xx"
    model_name = "glm-4.7"

    print(f"Connecting to {base_url} with model {model_name}...")

    client = AsyncOpenAI(
        base_url=base_url,
        api_key=api_key,
    )
    set_default_openai_client(client, use_for_tracing=False)
    set_default_openai_api("chat_completions")

    agent = Agent(
        name="AI",
        instructions="你是一个支持思维链的模型。请详细思考并回答：1+1等于几？",
        model=model_name
    )

    print("\n--- Starting Stream ---\n")

    full_content = ""
    thinking_content = ""

    try:
        result = Runner.run_streamed(agent, [{"role": "user", "content": "请开启思考模式回答：1+1等于几？"}])
        
        async for event in result.stream_events():
            # 打印事件类型
            # print(f"Event: {type(event).__name__}")
            
            if isinstance(event, RunItemStreamEvent):
                print(f"[RunItemEvent] Name: {event.name}")
                if event.name == "reasoning_item_created":
                    item = event.item
                    if isinstance(item, ReasoningItem):
                        print(f"  -> Found ReasoningItem!")
                        # Try to extract content
                        raw = item.raw_item
                        print(f"  -> Raw Item: {raw}")

            if event.type == "raw_response_event":
                if isinstance(event.data, ResponseTextDeltaEvent):
                    delta = event.data.delta
                    if delta:
                        print(delta, end="", flush=True)
                        full_content += delta
        
        print("\n\n--- Stream Finished ---")
        print(f"Full Content Length: {len(full_content)}")
        print(f"Contains <think>: {'<think>' in full_content}")

    except Exception as e:
        print(f"\nError occurred: {e}")

if __name__ == "__main__":
    asyncio.run(verify_reasoning())
