# Epic 10 群聊自驱模式 - 后端开发文档

> 目标：自驱逻辑**与普通群聊解耦**，以独立编排与状态机驱动“头脑风暴 / 决策 / 辩论”三类模式，同时保证与现有群聊消息体系可共存。

## 1. 范围与原则

- **逻辑层解耦**：自驱不复用普通群聊的自动发言逻辑，采用独立服务与状态流。
- **消息共享**：自驱产出的消息写入群聊消息表，但必须有可识别标记（见第 5.3 节）。
- **配置不可变**：运行期间不允许修改配置，仅暂停/继续/终止。
- **Prompt 不硬编码**：所有提示词放在 `server/app/prompt/` 并用 `load_prompt` 读取。

## 1.1 现状要点（来自现有代码）

- 普通群聊 API：`server/app/api/endpoints/group_chat.py`，路径 `/api/chat/group/{group_id}/messages`。
- 普通群聊服务：`server/app/services/group_chat_service.py`
  - 使用 `chat/group_manager.txt` + few-shot 选择回复成员（`_select_speakers_by_manager`）。
  - SSE 事件：`start`、`meta_participants`、`message`、`thinking`、`tool_call`、`done` 等。
  - 该逻辑**依赖群聊上下文编排**，不适合复用到自驱模式。
- 群聊消息结构：`GroupMessage.message_type` 仅支持 `text/system/@`（见 `server/app/schemas/group.py`）。

## 2. 推荐模块拆分

### 2.1 新增服务层
- `server/app/services/group_auto_drive_service.py`
  - 负责状态机、轮次调度、上下文编排、下一发言者选择、结束条件判断
  - **不复用** `GroupChatService` 的 GroupManager 逻辑与 prompt

### 2.2 API 端点
建议新增独立 router，避免挤压 `group_chat.py`：
- `server/app/api/endpoints/group_auto_drive.py`

路由示例：
- `POST /api/group/auto-drive/start`
- `POST /api/group/auto-drive/pause`
- `POST /api/group/auto-drive/resume`
- `POST /api/group/auto-drive/stop`
- `GET /api/group/auto-drive/state`

> 若决定沿用 `group_chat.py`，仍必须保持业务逻辑完全走 `group_auto_drive_service`。

### 2.3 与普通群聊的隔离边界（Hybrid 核心）
- **上下文编排不同**：自驱是“自动轮次 + 角色定位 + 阶段控制”，普通群聊是“被动触发 + GroupManager 选人”。
- **system prompt 不同**：自驱必须使用独立 prompt 集合（辩论/头脑风暴/决策）。
- **流与状态不混用**：自驱 SSE 与普通群聊 SSE 分流，避免 `streaming` 状态互相污染。

### 2.4 方案 C（推荐）：独立编排 + 共享底层能力
目标：**自驱保持独立服务与状态机**，但复用“消息/上下文/流式输出”等底层能力，减少重复代码与回归风险。

建议抽取的共享能力（从 `group_chat_service.py` 拆出，不改变业务分流）：
1. **会话与消息持久化工具**
   - `create_group_session(group_id, session_type, title)`：显式新建会话（自驱必走，不使用 `get_or_create_session_for_group`）
   - `end_active_sessions(group_id, session_type)`：结束历史会话并标记 `ended=true`
   - `create_user_message(...)`、`create_ai_placeholder(...)`：统一写入消息并更新 `last_message_time`
2. **历史消息与成员映射**
   - `fetch_group_history(group_id, session_id, limit, before_id)`：取最近 N 条
   - `build_name_map(history_msgs)`：统一构建 `sender_id -> name`
3. **上下文编排器（Mock Tool Call）**
   - `build_group_context(rounds, name_map, self_id, current_user_msg, other_msgs, mention_result)`  
   - 允许参数化：是否注入 recall、是否注入 `get_other_members_messages`、是否注入 `is_mentioned`
   - 普通群聊：开启 recall 注入；自驱：关闭 recall 注入
4. **LLM 流式输出与持久化**
   - 统一的 `stream_and_persist(...)`：负责解析 `<think>` 标签、推送 `message/thinking/done` 事件、落库并更新 session 时间
   - `run_llm_once(...)`：组装 Agents 参数、调用模型并将结果写入 queue（由上层 service 决定 prompt 与工具集）

在自驱服务中仅保留**编排职责**：
- 状态机流转、轮次调度、主持人话术生成、mentions 判定
- prompt 片段选择与拼接
- 选择调用上述共享能力完成“消息入库 + 流式输出”

### 2.4.1 共享模块建议（文件结构）
建议新建一个共享模块文件，集中提供“群聊通用能力”，示例：
- `server/app/services/group_chat_shared.py`

> 原 `group_chat_service.py` 仍保留“普通群聊业务编排”（GroupManager、mentions 触发、普通会话策略），仅把“可复用底层”移至 shared 模块。

### 2.4.2 共享函数清单（建议签名）
**会话/消息持久化**
- `create_group_session(db, group_id: int, session_type: str, title: str | None) -> GroupSession`
- `end_active_sessions(db, group_id: int, session_type: str | None) -> int`
- `create_user_message(db, group_id, session_id, sender_id, content, message_type="text", mentions=None) -> GroupMessage`
- `create_ai_placeholder(db, group_id, session_id, friend_id, message_type="text") -> GroupMessage`
- `touch_session(db, session_id)`：更新 `last_message_time/update_time`

**历史/成员映射**
- `fetch_group_history(db, group_id, session_id, before_id=None, limit=15) -> List[GroupMessage]`
- `build_name_map(db, messages, default_user_name="我") -> Dict[str, str]`

**上下文编排（Mock Tool Call）**
- `split_rounds(history_msgs, self_id) -> List[Round]`
  - Round: `{ user, others[], self }`
- `build_other_members_text(others, name_map) -> str`
- `build_group_context(rounds, name_map, self_id, current_user_msg, other_msgs_text, mention_result, options) -> List[dict]`
  - `options.include_recall`、`options.inject_recall_items`
  - `options.include_get_other_members` / `options.include_is_mentioned`

**LLM 调用与流式持久化**
- `build_system_prompt(parts: dict) -> str`
  - `parts` 由上层 service 传入（auto_drive_rule / host_script / message_segment / best_practice 等）
- `build_agent_tools(...) -> List[Tool]`（根据是否启用 recall、是否启用 is_mentioned 等生成）
- `stream_llm_to_queue(...)`：负责解析 `<think>` 标签、推送 `message/thinking/done`
- `persist_final_content(db, ai_msg_id, final_content, session_id)`

### 2.4.3 自驱服务对共享模块的调用流程（示意）
1. `create_group_session(..., session_type=mode)` 强制新建会话
2. `create_user_message(...)` 保存“主持人指令”（user 角色）
3. `create_ai_placeholder(...)` 为发言人创建空消息
4. `fetch_group_history(...)` + `build_name_map(...)`
5. `split_rounds(...)` + `build_group_context(...)`
6. `build_system_prompt(...)` 拼接 auto_drive 片段
7. `build_agent_tools(...)`（不含 recall）
8. `stream_llm_to_queue(...)` → `persist_final_content(...)`

### 2.4.4 需要保留在 group_chat_service 的逻辑
- `GroupManager` 选人（`_select_speakers_by_manager`）
- 普通群聊 session 续期与超时策略（`get_or_create_session_for_group`）
- 普通群聊的 mentions 触发与多成员并行回复策略

## 3. 核心状态机

状态：
- `Idle` → `Running` → `Pausing` → `Paused` → `Ended`

关键规则：
- `Paused` 允许用户插话
- `Pausing` 表示等待当前生成结束，结束后进入 `Paused`
- 达到 `turn_limit` 后进入 `Ended`，并触发总结/判定

## 3.1 会话隔离（避免污染普通群聊）

现有 `GroupChatService.get_or_create_session_for_group` 会基于 `GroupSession.last_message_time` 自动续/分 session。  
**自驱模式启动时应强制新建会话**，避免复用普通群聊的活跃会话，从而不影响“会话超时”逻辑。

约束规则（确认版）：
- **归属关系**：自驱会话仍归属当前 `group_id`，但 `session_type` 必须为 `debate / brainstorm / decision`。
- **结束标记**：自驱流程结束（达到 turn_limit 或用户终止）时，必须将该 `GroupSession.ended = true`。
- 普通群聊只处理 `session_type = normal`。

## 4. 轮次与调度规则（后端实现）

### 4.1 轮次口径
- 头脑风暴/决策：**每位成员发言一次 = 1 轮**
- 辩论：**正反双方各完成一次发言 = 1 轮**

### 4.2 辩论顺序
- 正方先发言
- 一辩指派：按 `member_id` ASCII 升序
- 自由交锋：正A → 反A → 正B → 反B ... 固定循环

### 4.3 头脑风暴/决策调度
- 发言人由**群管理员调度**决定（后端按调度名单或调度策略执行）

## 5. 数据结构（后端侧）

### 5.1 配置（AutoDriveConfig）
- `mode`：brainstorm / decision / debate
- `topic`：模式特化字段
- `roles`：成员列表 / 正反方列表
- `turn_limit`：发言上限
- `end_action`：总结 / 胜负判定 / 两者
- `judge_id` / `summary_by`：允许用户自己或指定成员

### 5.2 运行态（AutoDriveState）
- `status` / `phase`
- `current_round` / `current_turn`
- `next_speaker_id`
- `pause_reason`（如“等待收尾”）
- `started_at` / `ended_at`

> 建议持久化到 DB（可新表）以支持断线恢复与跨端同步。

### 5.3 群聊消息标记（必须）
**不修改 `GroupMessage.message_type`**，保持现有 `text/system/@` 语义不变。  
自驱消息的识别依赖以下两处：
- `GroupSession.session_type`（`normal / debate / brainstorm / decision`）
- `GroupMessage.debate_side`（仅辩论消息填 `affirmative / negative`）

涉及改动：
- `server/app/models/group.py`（新增 `session_type` 与 `debate_side`）
- `server/app/schemas/group.py`（为 `GroupSessionRead` 增加 `session_type` 字段）
- `front/src/api/group.ts`（`GroupSessionRead` / `GroupMessageRead`）
- `front/src/types/chat.ts`（`GroupSession` / `Message`）

### 5.4 题目与正反方的保存（必须）
自驱模式的**题目信息与正反方分配不应塞进消息内容**，应作为配置持久化，便于恢复与展示。

建议新增表（示例名）：`group_auto_drive_runs`（或 `group_auto_drive_config`）：
- `id`
- `group_id`
- `session_id`（对应自驱新建的 `GroupSession`）
- `mode`：`debate / brainstorm / decision`
- `topic_json`：题目字段（按模式结构化保存）
- `roles_json`：成员角色与顺序
  - 辩论示例：`{ "affirmative": ["12","45"], "negative": ["33","81"], "order": ["12","33","45","81"] }`
  - 头脑风暴/决策示例：`{ "participants": ["12","33","45"], "dispatcher_id": "user" }`
- `turn_limit`
- `end_action`
- `judge_id` / `summary_by`
- `status` / `started_at` / `ended_at`

说明：
- **正反方保存位置**：`roles_json`（成员→阵营映射），前端按 `sender_id` 反查阵营即可。
- **题目信息保存位置**：`topic_json`（按模式字段结构化存储）。
- **消息表冗余**：在 `GroupMessage` 增加可空字段 `debate_side`（`affirmative / negative`），仅辩论消息写入，其他模式为空；

## 6. Prompt 设计与加载

目录建议：
- `server/app/prompt/auto_drive/debate_judge.txt`
- `server/app/prompt/auto_drive/summary.txt`
- `server/app/prompt/auto_drive/auto_drive_rule.txt`（自驱通用规则 + 模式差异）
- `server/app/prompt/auto_drive/group_auto_drive_message_segment_normal.txt`（单气泡、非剧场式）
- `server/app/prompt/auto_drive/host_script_brainstorm.txt`（主持人固定话术）
- `server/app/prompt/auto_drive/host_script_decision.txt`（主持人固定话术）
- `server/app/prompt/auto_drive/host_script_debate.txt`（主持人固定话术）
- `server/app/prompt/auto_drive/user_best_practice_brainstorm.txt`（头脑风暴经典方法清单）
- `server/app/prompt/auto_drive/user_best_practice_decision.txt`（决策模式经典方法清单）
- `server/app/prompt/auto_drive/user_best_practice_debate.txt`（辩论模式经典方法清单）

加载方式：
- `get_prompt("auto_drive/auto_drive_rule.txt")`
- `get_prompt("auto_drive/group_auto_drive_message_segment_normal.txt")`
- `get_prompt("auto_drive/host_script_{mode}.txt")`
- `get_prompt("auto_drive/user_best_practice_{mode}.txt")`

建议拼接顺序（从高到低约束）：
1. `chat/root_system_prompt.txt` 作为最外层模板
2. 人设 + 群聊成员信息（role-play-prompt）
3. `auto_drive_rule.txt`（自驱规则 + 变量信息）
4. `group_auto_drive_message_segment_normal.txt`（单气泡格式 + 发言规则）
5. `host_script_{mode}.txt`（主持人固定话术）
6. `user_best_practice_{mode}.txt`（方法论清单，可选）

约束点：
- 200 字限制为**软限制**（提示词提醒，不硬截断）
- 辩论阶段性提示（立论 / 自由交锋 / 总结）
- **自驱模式 system prompt 片段变更**：
- 仍使用 `chat/root_system_prompt.txt` 作为最外层模板
- **不使用** `chat/group_chat_rule.txt`，改为注入 `auto_drive/auto_drive_rule.txt`
- 消息格式使用 `auto_drive/group_auto_drive_message_segment_normal.txt`（单气泡、非剧场式，发言规则已统一放在此文件）
  - 主持人固定话术从 `auto_drive/host_script_*.txt` 注入（用于让成员理解“主持人话术”与阶段指令）
  - 经典方法论从 `auto_drive/user_best_practice_*.txt` 注入（可选：用于让成员理解主持人调度策略）
  - **回忆提示冲突说明**：`root_system_prompt.txt` 内含“回忆调用规范”，但自驱模式不启用 recall 工具且不注入召回内容；如需彻底规避可追加一段“自驱禁用回忆”的覆盖说明（可放在 `auto_drive_rule.txt` 末尾）

## 6.1 自驱模式上下文编排（复用普通群聊逻辑）

**原则**：复用“普通群聊的上下文编排逻辑”，但**不复用代码**。保持“Mock Tool Call + 上帝视角”的上下文结构，让自驱成员在同一语义框架中工作。
> 实现层建议使用“共享上下文编排器”（见 2.4），由自驱传入参数关闭 recall 注入。

### 6.1.1 与普通群聊的差异点（必须落地）
- **不调用 recall**：不执行 `RecallService.perform_recall`，不注入 `recall_memory` 工具与 injected_recall_messages。
- **system prompt 片段不同**：见第 6 节的文件清单与组装规则。
- **发言权仍由用户驱动**：只有被 @ 时发言；否则输出 `<CTRL:NO_REPLY>`（与普通群聊一致）。
- **主持人固定话术**：不同模式/阶段的主持人话术需长期维护，作为 prompt 片段注入（见 `host_script_*.txt`）。

### 6.1.2 上下文构造步骤（与普通群聊一致）
1. **历史轮次切分**：以“用户消息”为轮次起点，将历史消息拆为多轮：
   - 每轮包含：`user`、`others`（同轮其他成员发言）、`self`（当前成员发言）
2. **按轮次拼接 Item**（Agents item 格式）：
   - `user` 消息（主持人指令）
   - `function_call`：`get_other_members_messages`
   - `function_call_output`：输出该轮次**其他成员**发言拼接（`name: content`），无则 `(empty)`
   - `assistant`：若该轮当前成员有发言则为内容；否则为 `<CTRL:NO_REPLY>`
3. **当前轮注入**：
   - 追加当前 `user` 消息（主持人指令）
   - `get_other_members_messages` 的输出为**当前轮已发生**的其他成员发言
     - 若主持人本轮 @ 多人，且系统按顺序串行发言，则已完成的成员发言应进入该字段，未完成的仍为空
     - 顺序建议以 `roles_json.order` 为准
   - `is_mentioned` 的输出为：`被提及，需要发言` / `未被提及，不要发言`
     - 判定来源优先使用 `GroupMessage.mentions`（前端 @ 列表）
     - **主持人话术由后端生成**，应在后端构造 `mentions` 或等价判定结果
     - 若 mentions 为空，可回退用正文内的 `@昵称` 匹配（可选）
4. **工具集**：只注册 `get_other_members_messages` 与 `is_mentioned`（不含 recall 工具）。

> 关键语义：模型收到 `is_mentioned=未被提及` 时必须输出 `<CTRL:NO_REPLY>`，以保证“只有被 @ 才发言”的规则稳定生效。

### 6.1.3 伪造 Tool Call 示例（与普通群聊对齐）
```
system prompt:
- 人设（root_system_prompt.txt）
- 单气泡消息格式规范（group_auto_drive_message_segment_normal.txt）
- 自驱规则（auto_drive_rule.txt）
- 主持人话术（host_script_*.txt）

--- 第一轮会话 ---
user: 辩题是… 先由正方 @张三 陈述核心观点
assistant(李四): (tool_call) get_other_members_messages()
(tool_result) 张三：我认为工作压力太大就应该辞职。
assistant(李四): <CTRL:NO_REPLY>

--- 第二轮会话 ---
user: 反方 @李四 请陈述核心观点
assistant(李四): (tool_call) is_mentioned()
(tool_result) 被提及，需要发言
assistant(李四): 我认为不应该辞职……
```

## 7. 与群聊消息体系的连接

- 自驱生成消息写入群聊消息表
- 使用第 5.3 节的**持久化标记**，保证历史消息可识别
- 插话消息仍按普通用户消息保存
- 自驱消息与普通消息**混排展示**，“开始/结束分割线”由 **`GroupSession` 的创建/结束** 生成，不新增 system 消息、不改写 `GroupMessage.message_type`。
- 后端负责**多表关联查询**（`GroupMessage` + `GroupSession`），在返回消息列表时附带必要的 `session_type`/`debate_side` 等信息，前端不做关联计算。

## 8. SSE 事件设计

**强约束：自驱 SSE 的事件与数据格式必须完全遵循普通群聊 SSE 协议**  
只能在此基础上**新增事件或新增字段**，**不得修改**已有事件名与既有字段结构，确保兼容性。

新增事件（可选）：
- `auto_drive_state`：运行态更新
- `auto_drive_message`：自驱消息（单气泡）
- `auto_drive_error`：终止或异常原因

前端只订阅，不做业务判断。

> 建议独立 SSE 路由（如 `/api/group/auto-drive/stream`），避免与 `/api/chat/group/{id}/messages` 的事件混流。

## 9. 插话与 @ 规则

- **插话永远允许**
- 插话 `@` 成员：立即触发被 @ 成员回复（不打乱主序列）
- 用户点击“继续”：回到原顺序继续

## 10. 异常与保护

- LLM 超时：进入 `Paused` 并提示原因
- 成员离开：不中断当前运行，仅记录系统提示
- 配置变更：运行中拒绝修改并返回错误码

## 11. 测试建议

- 状态机流转（Running → Pausing → Paused → Running → Ended）
- 轮次计数口径校验（讨论/辩论）
- 固定顺序与一辩指派
- 插话与 @ 回复的优先级
- 断线恢复后状态一致性

## 12. 实施计划（两阶段）

### 阶段一：抽公共层 + 改造普通群聊
目标：**不引入自驱功能**，先把 `group_chat_service` 中可复用的底层能力抽象到共享模块，并完成普通群聊的回归验证。
- 新增 `server/app/services/group_chat_shared.py`（或等价命名）
- 从 `group_chat_service.py` 抽出：
  - 会话/消息持久化工具
  - 历史与成员映射
  - 上下文编排器（Mock Tool Call）
  - LLM 流式输出与持久化
- `group_chat_service.py` 改为调用共享层（功能行为保持不变）
- 回归验证：普通群聊的 SSE 事件顺序、消息拆分、mentions 触发、GroupManager 选人均应保持一致

#### 阶段一回归用例清单（建议）
1. **基础对话流**：用户发言 → AI 回复 → `start/message/done` 顺序一致
2. **mentions 触发**：@ 指定成员时，只该成员回复；mentions 列表与输出一致
3. **GroupManager 选人**：无 @ 时仍可选人，且返回成员在群内
4. **消息拆分**：普通群聊仍按 `message_segment_*` 规则多段输出
5. **thinking 流**：开启思考模式时，`thinking` 事件仍按原逻辑出现
6. **工具事件**：`tool_call/tool_result` 与 `recall_*` 事件顺序保持一致
7. **会话续期**：30 分钟内复用 session，超时自动新建
8. **多成员并行**：多 AI 回复时仍能交错输出并正确持久化
9. **异常回退**：LLM 配置缺失、群不存在等错误事件仍按旧规范返回

### 阶段二：实现自驱功能
目标：在共享层基础上实现 `group_auto_drive_service.py` 与对应 API/SSE，不影响普通群聊。
- 新增自驱服务与状态机（见第 2.1、3、6.1 节）
- 自驱 prompt 拼接与主持人话术注入
- 自驱 API 与 SSE 接入（独立路由）
- 断线恢复与运行态持久化（若启用 DB）
