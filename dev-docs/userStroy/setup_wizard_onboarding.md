# Story: 初次安装配置引导 (Onboarding Setup Wizard)

## 1. 需求详情 (Requirement Details)

### 1.1 背景
WeAgentChat 作为一个高度依赖大模型的社交沙盒应用，LLM（用于对话和推理）和 Embedding（用于长期记忆）是其核心基础设施。
目前，如果用户没有在设置中配置这些参数，应用会因为 API 调用失败而无法正常工作。为了提升“开箱即用”的体验，我们需要在用户**首次安装并启动应用**时，提供一个简洁、 premium 的引导流程。

### 1.2 目标
- **自动检测**：启动时自动判断核心配置是否缺失。
- **低门槛引导**：通过对话式或分步式的 UI，引导用户填入 API 信息。
- **即时校验**：在保存前强制或推荐进行“连接测试”，确保配置有效。
- **无缝转场**：配置完成后，平滑进入主聊天界面。

---

## 2. 用户故事 (User Stories)

### US-1: 首次运行检测
**作为** 一名新用户，
**我希望** 在我第一次打开应用时，系统能告诉我需要配置模型，
**以便于** 我不会因为看到一堆 API 错误而感到困惑。

### US-2: 核心模型配置引导
**作为** 用户，
**我希望** 能够通过一个简单的向导，分步输入我的大模型和向量模型参数，
**以便于** 快速完成复杂的设置，而不必去翻找侧边栏的深层菜单。

---

## 3. 功能范围 (Functional Scope)

### 3.1 后端逻辑 (Backend Support)
- **配置状态接口**：提供一个简单的接口（或扩展现有的 `/api/health`），返回当前系统的配置完备度（LLM 是否已配，Embedding 是否已配）。
- **配置初始化**：确保系统在无配置状态下仍能启动核心服务（如 API 路由器），但拦截需要 LLM 的请求并返回特定的异常提示。

### 3.2 前端交互 (Frontend Onboarding)
- **强制拦截器**：
    - 在 `App.vue` 或 `router` 层面检查配置状态。
    - 如果配置缺失，弹出全屏或半透遮罩的 `SetupWizard` 组件。
- **分步配置 UI (Stepper)**：
    - **Step 1: 欢迎语**。介绍 WeAgentChat 的特性（私人、AI 社交）。
    - **Step 2: LLM 配置**。集成 Base URL, API Key, Model Name 的输入，并包含一个明显的“测试连接”按钮。
    - **Step 3: Embedding 配置**。选择提供商（OpenAI, Jina, Ollama 等），输入 Key 和模型。
    - **Step 4: 完成**。执行保存并触发后端配置重载（Reload SDK）。

---

## 4. 验收标准 (Acceptance Criteria)

- [ ] **AC-1**: 数据库中 `llm_configs` 或 `embedding_settings` 为空时，应用启动必须自动进入引导。
- [ ] **AC-2**: 引导界面必须符合“微信绿”或 premium 简约审美，避免给用户技术门槛过高的压力。
- [ ] **AC-3**: 每一阶段的“测试”反馈必须及时，如果测试失败，应给出明确的错误提示（如：API Key 无效、网络连接不可达）。
- [ ] **AC-4**: 用户点击“保存并开始使用”后，引导界面应带有平滑动画消失，并立即加载好友列表。
- [ ] **AC-5**: 在已配置状态下，再次打开应用不应出现引导流程。

---

## 5. 技术依赖与参考

- **现有 API**: 
    - `POST /api/llm/config/test`
    - `POST /api/embedding/test`
    - `PUT /api/llm/config`
    - `POST /api/embedding/`
- **组件库**: 使用 `ai-elements-vue` 的 `loader` 或自定义的 `Stepper` 逻辑结合 `shadcn-vue` 弹窗。
- **状态管理**: 基于现有的 `llm.ts` 和 `embedding.ts` Pinia Stores 进行扩展。

---

## 6. 排期建议
- **优先级**: P0 (阻塞级 feature)
- **预估工时**: 2d (前端 1.5d, 后端 0.5d)
