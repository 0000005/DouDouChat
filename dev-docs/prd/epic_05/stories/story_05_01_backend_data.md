# Story 05-01: 后端数据层 (Database & API)

> Epic: 好友库 (Friend Gallery)
> Priority: High
> Points: 5

## 概述
作为整个好友库的基础，本 Story 专注于构建独立的模版数据表和核心 API。我们将新建 `friend_templates` 表存储预置模版，与现有 `friends` 表物理隔离，确保架构清晰。

## 用户故事

### US-1: 模版数据存储
**作为** 系统开发者，
**我希望** 有一张独立的表存储"官方预置模版"，
**以便** 与用户的私有好友（`friends` 表）完全隔离，互不干扰。

### US-2: 模版查询与克隆 API
**作为** 前端开发者，
**我希望** 能通过 API 获取带分类、可搜索的模版列表，并能一键将模版克隆为我的好友，
**以便** 对接前端页面的展示与添加功能。

## 功能范围

### 包含
- **新建数据表**：使用 Alembic 创建 `friend_templates` 表，字段包括：
  - `id` (Integer, PK)
  - `name` (String): 角色名称。
  - `avatar` (String, Nullable): 头像 URL。
  - `description` (Text): 一句话简介。
  - `system_prompt` (Text): 完整的人格设定。
  - `initial_message` (Text, Nullable): 初次对话的开场白。
  - `tags` (JSON/Text): 分类标签，如 `["商业", "科技"]`。
  - `created_at`, `updated_at` (DateTime)。
- **查询 API**：`GET /api/friend-templates`
  - 支持分页 (`page`, `size`)。
  - 支持过滤 (`tag`) 和 模糊搜索 (`q` 匹配 name/description)。
- **克隆 API**：`POST /api/friend-templates/{id}/clone`
  - 读取指定 ID 的模版数据。
  - 在 `friends` 表中创建一条新记录，复制 name、avatar、system_prompt 等字段。
  - 返回新创建的 Friend 对象。
- **直接创建 API**：`POST /api/friend-templates/create-friend`
  - 用于保存 AI 生成的好友（Story 05-05 使用），独立于现有 `friends` 相关接口。
  - 输入：`{ name, avatar?, description, system_prompt, initial_message? }`
  - 输出：新创建的 Friend 对象（已写入 `friends` 表）。

### 不包含
- 用户自定义模版的上传接口（暂不支持用户投稿到公共库）。
- 批量生成脚本（移至 Story 05-06）。

## 验收标准

- [ ] AC-1: 成功应用数据库迁移，`friend_templates` 表创建成功，现有 `friends` 表不受影响。
- [ ] AC-2: `GET /friend-templates` 接口能正确按 tag 过滤数据，支持中文关键字搜索。
- [ ] AC-3: `clone` 接口成功后，`friends` 表中新增一条记录，且数据与模版一致。
- [ ] AC-4: `POST /api/friend-templates/create-friend` 能正常创建非模版来源的好友。

## 依赖关系
- 前置：无（基于 Epic-01 现有 `friends` 表结构）
- 后续：所有前端 Story (05-02 ~ 05-05), Story 05-06 (批量填充)
