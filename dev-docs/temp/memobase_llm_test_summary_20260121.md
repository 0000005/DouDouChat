# Memobase LLM 兼容性测试执行情况（阶段性总结）

日期：2026-01-21

## 已完成
- 新增 Memobase 多供应商 LLM 兼容性测试：`server/tests/test_memobase_llm_providers.py`
  - 使用环境变量注入各供应商 base_url / api_key / model
  - 调用 `app.vendor.memobase_server.llms.llm_complete` 做最小化请求
- 修复 Memobase OpenAI 适配层对 GPT-5 的采样参数兼容：
  - `server/app/vendor/memobase_server/llms/openai_model_llm.py`
  - GPT-5 模型会移除 `temperature/top_p`，避免 400 报错

## 测试执行
- 命令（使用 venv）：
  - `./server/venv/Scripts/python -m pytest server/tests/test_memobase_llm_providers.py -q`
- 结果：全部 7 项失败
- 失败原因：统一为 `ConnectError`，无法建立连接（未返回 HTTP 响应）
  - 典型日志：`Error in llm_complete: Connection error.`
  - 各供应商都未连通：OpenAI / Gemini / ModelScope / Minimax / Zhipu / DeepSeek

## 结论（当前阶段）
- 不是模型报错或鉴权问题，而是 Python 客户端在本环境无法连通到外部 API。
- 需要先解决网络/代理/证书/防火墙等连通性问题，再验证模型兼容性。

## 待办建议（下次恢复时）
1) 先做连通性诊断（DNS + 443 端口测试）或确认是否必须设置 `HTTP_PROXY/HTTPS_PROXY`。
2) 如需按 OpenAI 兼容接口测试，推荐确认 base_url 是否应使用：
   - Gemini：`https://generativelanguage.googleapis.com/v1beta/openai`
   - Minimax：`https://api.minimax.chat/v1`
   - Zhipu：`https://open.bigmodel.cn/api/paas/v4`
3) 重新运行 `server/tests/test_memobase_llm_providers.py` 并定位具体供应商错误。

## 变更文件
- `server/tests/test_memobase_llm_providers.py`
- `server/app/vendor/memobase_server/llms/openai_model_llm.py`
