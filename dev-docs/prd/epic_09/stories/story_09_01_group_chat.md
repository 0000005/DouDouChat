# Story 09-01: 群聊数据建模

> Epic: AI 多人群聊 (Group Chat)
> Priority: High
> Points: 3

## 概述
定义群聊的核心数据结构，包括群组信息、成员关系以及群消息记录。建立稳健的关系型数据库表结构，为多 Agent 参与的群聊功能提供持久化支持。

## 用户故事

### US-1: 数据持久化支持
**作为** 开发者，
**我希望** 建立群组、成员和消息的数据库模型，
**以便** 支持群聊功能的业务逻辑开发和数据读取。

### US-2: 数据库结构同步
**作为** 系统，
**我希望** 通过 Alembic 自动迁移数据库 Schema，
**以便** 维护数据库的版本一致性和可追溯性。

## 功能范围

### 包含
- **Group 模型 (群组表)**:
  - `id`: 群组唯一标识符 (Primary Key)。
  - `name`: 群名称。
  - `avatar`: 群头像 URL 或预设图标标识。
  - `description`: 群备注或描述，用于告知 Hidden Admin 群聊背景。
  - `owner_id`: 创建者 ID（当前用户）。
  - `auto_reply`: 布尔值，控制该群是否开启 Hidden Admin 自动调度功能（默认 `True`）。
  - `created_at`: 创建时间。
- **GroupMember 模型 (群成员表)**:
  - `id`: 成员记录标识符。
  - `group_id`: 所属群组的外键关联。
  - `member_id`: 成员唯一 ID（用户 ID 或 AI 好友 ID）。
  - `member_type`: 成员类型 (`user` 或 `friend`)，用于区分人类用户与 AI。
  - `joined_at`: 加入时间。
- **GroupMessage 模型 (群消息表)**:
  - `id`: 消息唯一标识符。
  - `group_id`: 所属群组的外键关联。
  - `sender_id`: 发送者 ID。
  - `sender_type`: 发送者类型 (`user` 或 `friend`)。
  - `content`: 消息正文内容（Markdown 或纯文本）。
  - `message_type`: 消息标记类型 (`text`, `system`, `@`)，用于指导前端渲染和后端触发。
  - `mentions`: JSON 数组，记录消息中 @ 的成员 ID 列表。
  - `created_at`: 发送时间。
- **数据库迁移**: 编写并执行 Alembic 迁移脚本，生成对应的 Alembic Version 文件。

### 不包含（后续迭代）
- 群公告历史记录表
- 群文件/多媒体资源管理模型
- 复杂的群员等级或权限模型

## 验收标准

- [ ] AC-1: 完成 `Group`, `GroupMember`, `GroupMessage` 的 SQLAlchemy 模型定义。
- [ ] AC-2: 模型通过外键正确关联，且支持关系加载（Relationship）。
- [ ] AC-3: `GroupMessage` 模型能够区分发送者是人类用户还是特定的 AI 好友。
- [ ] AC-4: 成功运行 `alembic upgrade head` 并确认数据库中表结构正确。
- [ ] AC-5: 通过单元测试验证基础的群组创建、成员添加和消息读写操作。

## 依赖关系

### 前置依赖
- 无

### 被依赖（后续）
- Story 09-02: 群组管理界面 (UI)
- Story 09-04: 群聊上下文适配
