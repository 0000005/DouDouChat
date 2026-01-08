# Story 05-06: 批量内容填充 (Batch Seeding)

> Epic: 好友库 (Friend Gallery)
> Priority: High
> Points: 3

## 概述
使用脚本批量生成 160 个高质量的预置好友数据，填充 `friend_templates` 表。

## 用户故事

### US-1: 丰富的内容库
**作为** 用户，
**我希望** 第一次打开好友库时就有大量丰富角色可选，
**以便** 我能立刻开始体验。

## 功能范围

### 包含
- **种子名单策划**：整理 8 大分类（商业、科技、历史、文学、影视、动漫、游戏、明星）的 160 个角色名称列表。
- **批量生成脚本**：
  - 编写 Python 脚本 (`scripts/seed_friend_templates.py`)。
  - 循环调用 Story 05-04 的 `PersonaGeneratorService`。
  - 将生成结果存入 `friend_templates` 表。
- **人工质检**：对生成的 JSON 数据进行简单的语义检查，确保无乱码或截断。

### 不包含
- 手动逐个编写 160 个 Prompt（由 AI 完成）。

## 验收标准

- [ ] AC-1: 数据库中成功预置 160+ 个模版角色。
- [ ] AC-2: 每个分类下的角色分布相对均匀（每类约 20 个）。
- [ ] AC-3: 所有角色的 System Prompt 格式符合系统要求，且包含正确的分类标签。

## 依赖关系
- 前置：Story 05-04 (生成服务)
