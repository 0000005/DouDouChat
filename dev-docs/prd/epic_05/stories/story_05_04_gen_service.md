# Story 05-04: AI角色生成服务 (Gen Service)

> Epic: 好友库 (Friend Gallery)
> Priority: High
> Points: 5

## 概述
专注于后端生成能力的构建。开发一个能够根据简短描述自动生成高质量、结构化 Persona 设定（System Prompt）的服务，并暴露为 API。

## 用户故事

### US-1: 智能角色建模
**作为** 系统/用户，
**我希望** 仅提供"我想创建一个像乔布斯一样的产品经理"，
**以便** 系统自动补全他的性格、语气、背景故事等复杂设定。

## 功能范围

### 包含
- **Prompt Engineering**：设计一套元 Prompt（Meta-Prompt），用于指导 LLM 生成角色设定。要素包括：基本信息、性格特征（MBTI）、语言风格、知识领域、互动模式等。
- **生成服务类**：`PersonaGeneratorService`。
- **API 接口**：`POST /api/friend-templates/generate`
  - Input: `{ "description": "xxx", "name": "optional" }`
  - Output: `{ "name": "...", "description": "...", "system_prompt": "...", "initial_message": "..." }`
- **Mock 实现**：在 LLM 不可用时提供兜底数据。

### 不包含
- 批量的数据填充（在 05-06）。
- 前端向导界面（在 05-05）。

## 验收标准

- [ ] AC-1: API 能稳定接收输入并返回 JSON 格式的 Persona 数据。
- [ ] AC-2: 生成的 System Prompt 结构完整，必须包含"角色定义"、"约束条件"等预设板块。
- [ ] AC-3: 能够处理极其简短的输入（如"猫娘"），并生成合理的扩展设定。

## 依赖关系
- 前置：Story 05-01 (DB 结构)
- 后续：Story 05-05, Story 05-06
