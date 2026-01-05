# User Story: 个人资料自定义与管理 (Personal Data Customization & Management)

## 1. 背景与目标
在 WeAgentChat 中，AI 代理会根据对话自动提取并记录关于“人类用户”的个人资料（曾称 User Profile）。
- **结构 (Schema)**: 定义了资料的分类维度（如“基本特征”、“工作偏好”等）。存储在 `memobase` 的 `projects` 表中。
- **内容 (Data)**: AI 提取的关于用户的具体事实。存储在 `user_profiles` 表中。

**目标**:
1.  **个人资料查看/修正**: 用户可以查看 AI 对自己的所有印象，并手动修正、删除错误信息或主动添加资料。
2.  **资料维度定义**: 用户可以根据自己的偏好，自定义 AI 记录资料的关注点（如：希望 AI 多关注我的“健康习惯”）。
3.  **用户体验优化**: 所有界面和话术需与“微信”风格保持一致，使用“个人资料”而非“用户画像”等技术术语。

---

## 2. 后端开发计划 (Backend)

延续 `passive_session_memory.md` 中的设计，使用 `user_id="default_user"` 和 `space_id="default"` 作为当前默认上下文。

### 2.1 API 接口设计

#### A. 个人资料结构配置 (Schema Config)
| 方法 | 路径 | 描述 |
| :--- | :--- | :--- |
| `GET` | `/api/memory/config` | 获取当前的资料分类结构 (YAML 字符串) |
| `PUT` | `/api/memory/config` | 更新资料分类结构 (前端提交转换后的 YAML) |

#### B. 个人资料内容管理 (Content Data)
| 方法 | 路径 | 描述 |
| :--- | :--- | :--- |
| `GET` | `/api/memory/profiles` | 获取当前用户的所有资料条目 |
| `POST` | `/api/memory/profiles` | 手动添加一条个人资料 |
| `PUT` | `/api/memory/profiles/{profile_id}` | 修改单条资料的内容或分类 |
| `DELETE` | `/api/memory/profiles` | 批量删除资料条目 (Body 传 id 列表) |

### 2.2 核心逻辑实现
- **桥接层**: 在 `server/app/services/memo/bridge.py` 中重新实现并暴露 `MemoService.get_profile_config` 和 `MemoService.update_profile_config`（此前已 Revert）。
- **控制器**: 调用 `memobase_server` 的 `project.py` 和 `profile.py` 控制器。

---

## 3. 前端开发计划 (Frontend)

### 3.1 入口改造 (Entry Points)
为了符合微信交互习惯，优化现有的左侧导航栏：

1.  **左上角头像**:
    -   点击当前用户头像 -> 弹出“个人资料”窗口。
2.  **左下角“更多”菜单**:
    -   将原有的“设置”图标改为类似微信的“更多”图标。
    -   点击后弹出 Popover 菜单：
        -   **个人资料**: 打开个人资料窗口。
        -   **系统设置**: 打开原有的 `SettingsDialog.vue`。

### 3.2 资料管理界面 (Profile View/Edit)
新建 `ProfileDialog.vue` 组件，功能包括：
- **分组展示**: 按照 Schema 定义的 `topic` 进行卡片式或列表式分组。
- **即点即改**: 点击资料条目直接进入编辑状态。
- **手动添加**: 提供“添加一笔”按钮，需从已定义的 Topic/Sub-Topic 中选择。

### 3.3 记忆模型编辑器 (Visual Schema Builder)
在 `SettingsDialog.vue` 的“记忆设置”中新增“资料维度定义”：
- **可视化配置**: 使用 shadcn-vue 的 `Accordion` 展示 Topic。
- **操作项**: 允许非技术用户“添加分类”、“删除分类”、“添加子项”。
- **静默转换**: 界面操作后，前端自动将其序列化为符合 `memobase` 规范的 YAML 字符串提交给后端。

---

## 4. 任务拆解 (Task List)

### Backend
- [ ] **Bridge 重新实现**: 补全 `MemoService` 中缺少的项目配置读写接口。
- [ ] **Router 开发**: 新建 `server/app/api/endpoints/profile.py` 并注册路由。
- [ ] **单工模式适配**: 接口内部默认填充 `user_id="default_user"`。

### Frontend
- [ ] **组件开发**: 实现 `ProfileDialog.vue` 核心交互。
- [ ] **配置面板**: 在设置中开发可视化 Schema Builder 组件。
- [ ] **导航栏重构**: 实现左下角 Popover 菜单和头像点击逻辑。
- [ ] **API 联调**: 联调 Schema 写回和 Data 增删改查。
