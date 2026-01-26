# Story 09-05: 群聊消息服务接口 (API & SSE)

> Epic: AI 多人群聊 (Group Chat)
> Priority: High
> Points: 8

## 概述
实现群聊消息的核心发送与接收接口。本 Story 要求**完全参考单聊接口 (`api/chat/friends/{id}/messages`) 的实现逻辑**，复用其成熟的 Prompt 构建、记忆召回 (Recall) 和流式响应处理机制。在此基础上，增加群聊特有的“多发送者区分”和“并发回复”能力。

**核心差异点**：
- 单聊是 1v1 (User vs Agent)。
- 群聊是 1vN (User vs Multiple Agents)。接口需支持根据 `@提及` (Mentions) 触发对应 Agent 的并发回复。

## 用户故事

### US-1: 群消息发送与路由
**作为** 用户，
**我希望** 在群聊中发送消息并 `@` 特定的 AI 朋友，
**以便** 只有被点名的朋友会进行回复，且回复内容符合其人设和记忆。

### US-2: 多角色并发推送 (SSE)
**作为** 前端开发者，
**我希望** 后端 SSE 接口能同时推送多位 Agent 的回复流，并通过 `sender_id` 区分每一条数据包，
**以便** 我能在界面上并行渲染不同角色的气泡和思考状态。

## 功能范围

### 1. 发送群消息接口 (Backend)
- **Endpoint**: `POST /api/chat/group/{group_id}/messages`
- **Request Body**:
  ```json
  {
    "content": "Hello @Alice @Bob",
    "mentions": [101, 102], // 被提及的 Friend IDs
    "enable_thinking": true
  }
  ```
- **核心处理流程** (参考 `chat_service.send_message_stream`):
  1.  **持久化用户消息**: 将用户发送的内容写入 `GroupMessage` 表。
  2.  **创建回复占位符**: 为每一个被 mention 的 Agent (`101`, `102`) 在 `GroupMessage` 表中预先创建一条 `role=assistant` 的空消息。
  3.  **启动并发任务**: 使用 `asyncio.create_task` 为每个 Agent 启动独立的生成任务 (类似 `_run_chat_generation_task`)。
  4.  **返回 SSE 流**: 聚合所有后台任务的事件并推送给客户端。

### 2. 任务生成逻辑 (Backend)
对于每一个被触发的 Agent，执行以下逻辑（复用单聊代码结构）：
-   **Prompt 构建**:
    -   加载 `chat/root_system_prompt.txt`。
    -   注入该 Agent 的 System Prompt (`{{role-play-prompt}}`)。
    -   注入该 Agent 的脚本表达配置 (`{{script-expression}}`)。
    -   注入当前时间 (`{{current-time}}`)。
-   **记忆召回 (Recall)**:
    -   **必须包含**：调用 `RecallService.perform_recall`，检索该 Agent 与当前 User 的相关记忆（尽管是群聊，优先检索二人关系记忆）。
    -   将召回的 Memory 片段注入 Prompt 或 Context。
-   **LLM 调用**:
    -   使用 `agents` 库 (OpenAI Wrapper) 调用模型。
    -   支持 `thinking` (思考过程) 捕获。
    -   支持 Tool Calls (如果配置了)。
-   **持久化**:
    -   流式更新 `GroupMessage` 表中的内容。

### 3. SSE 协议扩展 (Backend & Frontend)
为支持多路复用，所有 SSE 事件 (`start`, `thinking`, `message`, `done`, `error`) 的 `data` 字段中**必须**增加 `sender_id`。同时在 `start` 事件中需携带 `group_id` 以便前端校验。

**示例 SSE 响应**:
```text
event: start
data: {"group_id": 1, "sender_id": 101, "message_id": 5001, "model": "gpt-4"}

event: thinking
data: {"sender_id": 101, "delta": "I need to..."}

event: message
data: {"sender_id": 102, "delta": "Hello!"} // Agent 102 同时在回复
```

### 4. 前端调用实现 (Frontend)
-   **API 客户端封装 (`front/src/api/chat.ts` 或 `group.ts`)**:
    -   实现 `sendGroupMessageStream(groupId, message)` 方法。
    -   确保请求头和 Body 格式与后端 `POST /api/chat/group/{group_id}/messages` 对齐。
    -   使用 `fetch` + `getReader()` 实现流式读取 (参考 `sendMessageStream`)。
-   **Pinia Store 逻辑 (`front/src/stores/session.ts`)**:
    -   更新 `sendGroupMessage` Action。
    -   **并发流处理**: 在 `for await` 循环中，解析 data 中的 `sender_id`。
    -   **多 Agent 状态维护**:
        -   收到 `start` 或首个数据包时，如果本地列表中没有该 Agent 的消息占位符，动态创建一个 (ID 临时为负或使用后端返回的)。
        -   根据 `sender_id` 将 `delta` 内容追加到对应的消息对象中 (支持 `thinkingContent` 和 `content` 的并行更新)。
    -   **UI 响应**: 确保 `messagesMap[groupId]` 中的变化能实时触发 UI 更新 (Pinia 响应式)。

### 5. 接口清理
- **删除旧接口**: 删除现有的 `POST /api/group/{id}/stream` (如果有)。
- **统一入口**: 确保前端群聊组件 (`GroupChatArea.vue` 等) 切换调用新的 `POST /api/chat/group/{group_id}/messages`。

## 验收标准

- [ ] **AC-1 (API 实现)**: `POST /api/chat/group/{group_id}/messages` 能够接收消息并正确解析 `mentions` 列表。
- [ ] **AC-2 (并发生成)**: 如果用户同时 @ 了两个 Agent，后端能启动两个并行的 LLM 任务，且互不阻塞。
- [ ] **AC-3 (Prompt & Recall 复用)**: 确认群聊回复中包含了单聊的所有 Prompt 细节（时间、人设、脚本指令）以及 Memory Recall 的结果（可以通过日志验证 Recall 被调用）。
- [ ] **AC-4 (SSE 格式)**: 前端能接收到带有 `group_id` 和 `sender_id` 的 SSE 事件流，并能区分不同角色的内容片段。
- [ ] **AC-5 (前端并发渲染)**: 前端 Store 能同时维护多个 Agent 的回复状态，界面上能看到多个气泡同时在“打字”或“思考”。
- [ ] **AC-6 (清理)**: 验证旧接口 `POST /api/group/{id}/stream` 已被物理删除，且前端相关调用已全部迁移。

## 依赖关系
- 前置: Story 09-01 (群聊数据模型)
- 后续: Story 09-06 (群聊上下文适配 - 将群历史注入 Prompt)
