# 前端开发文档 - Story 02-01: 个人资料自定义与管理

> **文档说明**: 本文档供 AI 编码助手在独立会话中执行。遵循原子化操作原则。本文档专注于前端实现，假设后端 API 已按照 `profile_customization.md` 规范就绪。

## 1. 需求全景
### 1.1 业务背景
在 WeAgentChat 中，AI 代理会自动记录对用户的印象（个人资料）。用户需要能够查看、修改这些资料，并自定义 AI 记录资料的关注维度（Schema），以增强 AI 的个性化记忆能力。

### 1.2 详细功能描述
- **入口重构**: 
    - 修改 `IconSidebar.vue` 底部。原“设置”按钮改为“更多”图标。
    - 点击“更多”弹出 Popover 菜单，包含“个人资料”和“系统设置”。
    - 点击左侧顶部头像弹出“个人资料”。
- **个人资料管理 (ProfileDialog.vue)**:
    - 弹出层展示用户现有的所有资料条目。
    - 按分类（Topic）分组显示。
    - 支持点击条目进行就地编辑。
    - 支持删除条目。
    - 支持手动添加一条资料（需选择已定义的 Topic）。
- **资料维度自定义 (SettingsDialog.vue 扩展)**:
    - 在记忆设置中增加“维度定义”区域。
    - 可视化展示分类（Accordion）。
    - 允许用户添加/删除分类及子项。
    - 前端负责将对象结构转换为 YAML 字符串提交给后端。

### 1.3 边界与异常处理
- **Schema 解析失败**: 若后端返回的 YAML 格式错误，前端应显示“无法加载配置”并初始化一个默认的基础结构（如：基本特征、习惯、偏好）。
- **空状态**: 当用户没有任何资料时，分组下显示“暂无记录，您可以尝试在此分类下手动添加”。
- **网络延迟**: 提交 YAML 或更新 Profile 时显示 Loading 状态。

### 1.4 验收标准 (Acceptance Criteria)
- [ ] 点击头像能弹出个人资料窗口。
- [ ] 资料窗口能正确读取并按 Topic 分组展示后端数据。
- [ ] 在资料窗口修改内容能成功同步到后端。
- [ ] 在系统设置中修改维度（Schema），保存后后端能接收到转换后的 YAML。
- [ ] 导航栏左下角图标变为“更多”，弹出菜单包含两个选项。

## 2. 预备工作
### 2.1 参考文档
- **shadcn-vue 组件**:
    - `Popover`: 用于左下角“更多”菜单。引入 `@/components/ui/popover`。
    - `Accordion`: 用于维度定义可视化编辑。引入 `@/components/ui/accordion`。
    - `ScrollArea`: 用于资料列表滚动。引入 `@/components/ui/scroll-area`。
- **YAML 处理**: 使用 `js-yaml` (确保项目中已安装，若未安装需添加) 进行对象与字符串的转换。

## 3. 现状分析快照
- **分析文件列表**:
    - `{项目根目录}/front/src/components/IconSidebar.vue`: 第 58-67 行定义了底部设置按钮，需要重构。
    - `{项目根目录}/front/src/components/SettingsDialog.vue`: 第 260-281 行定义了记忆设置 Tab，需要在此扩展。
    - `{项目根目录}/front/src/stores/settings.ts`: 现存 `passiveTimeout` 状态，需增加 Memory Config 和 Profiles 相关的 Store。
- **关键发现**:
    - 项目中目前没有专用于 Profile 的组件，需要新建 `ProfileDialog.vue`。
    - 现有的 `IconSidebar.vue` 第 12 行 props 只有 `activeTab`，未提供头像点击和更多菜单的控制。

## 4. 架构与逻辑设计
### 4.1 组件层次
- **App.vue**:
    - 管理 `isProfileOpen` 全局状态。
    - 引入 `ProfileDialog`。
- **IconSidebar**:
    - 顶层 Avatar 增加点击事件。
    - 底部 Settings 替换为 Popover("更多")。
- **ProfileDialog** (新):
    - **Header**: 标题“个人资料”。
    - **Content**: `ScrollArea` 包裹的分组列表。
        - **Group**: 按 `topic` 渲染卡片。
            - **Item**: 每一行资料条目，带编辑/删除按钮。
    - **Footer**: “添加条目”按钮。
- **SettingsDialog**:
    - 在“记忆设置” Tab 下增加 `ProfileSchemaBuilder` 子组件。

### 4.2 状态管理
- **useMemoryStore** (新 Store):
    - `profileConfig`: 对象结构（从 YAML 解析后的 Topic 列表）。
    - `profiles`: 资料条目数组。
    - `fetchConfig()`: 调用 `/api/memory/config`，通过 `js-yaml` 解析。
    - `saveConfig()`: 将 `profileConfig` 转换为 YAML 序列化提交。
    - `fetchProfiles()`: 调用 `/api/memory/profiles`。

### 4.3 交互流程
1. **Schema 编辑**:
    - 用户在设置中点击“添加分类” -> Store 中 push 一个带有默认 `topic` 的对象。
    - `Accordion` 重新渲染 -> 用户输入分类名称。
    - 点击“保存” -> 调用 `yaml.dump(profileConfig)` -> 发送 PUT 请求。
2. **资料修改**:
    - 用户点击个人资料中的某条信息 -> 输入框激活 -> 失去焦点或按回车 -> 调用 PUT 请求同步单条。

## 5. 详细变更清单
| 序号 | 操作类型 | 文件绝对路径 | 变更摘要 |
|------|----------|--------------|----------|
| 1    | 新增     | `{项目根目录}/front/src/api/memory.ts` | 新建 API 层，处理 `/api/memory/*` 接口 |
| 2    | 新增     | `{项目根目录}/front/src/stores/memory.ts` | 新建 Store，管理资料数据和 Schema 对象 |
| 3    | 新增     | `{项目根目录}/front/src/components/ProfileDialog.vue` | 新建个人资料弹窗组件 |
| 4    | 修改     | `{项目根目录}/front/src/components/IconSidebar.vue` | 头像点击事件接入，底部按钮改为 Popover |
| 5    | 修改     | `{项目根目录}/front/src/components/SettingsDialog.vue` | “记忆设置”增加可视化 Schema 编辑器逻辑 |
| 6    | 修改     | `{项目根目录}/front/src/App.vue` | 注册 ProfileDialog，协调弹窗状态 |

## 6. 分步实施指南 (Atomic Steps)

### 步骤 1: 创建 API 与 Store
- **操作文件**: `{项目根目录}/front/src/api/memory.ts`, `{项目根目录}/front/src/stores/memory.ts`
- **操作描述**:
    1. 实现 `getMemoryConfig`, `updateMemoryConfig`, `getProfiles`, `addProfile`, `updateProfile`, `deleteProfiles` (批量删除) 的 fetch 调用。
    2. Store 中定义 `profileConfig` (解析后的 YAML 对象) 和 `profiles` (条目列表)。
    3. `loadConfig` 使用 `js-yaml` 的 `load` 方法。`saveConfig` 使用 `dump` 方法。
- **验证方法**: 检查 Store 初始化是否能正确解析 YAML 字符串。

### 步骤 2: 重构 IconSidebar.vue
- **操作文件**: `{项目根目录}/front/src/components/IconSidebar.vue`
- **操作描述**:
    1. 导入 `MoreHorizontal` 图标和 `Popover` 相关组件。
    2. 为头像容器增加 `@click="emit('open-profile')"`.
    3. 底部原有按钮容器内嵌入 `<Popover>`，Trigger 为更多图标，Content 包含两个 `<Button variant="ghost">` 分别对应“个人资料”和“系统设置”。
- **验证方法**: 点击左下角图标应弹出菜单，点击头像应能触发父组件事件。

### 步骤 3: 实现 ProfileDialog.vue
- **操作文件**: `{项目根目录}/front/src/components/ProfileDialog.vue`
- **操作描述**:
    1. 使用 `Dialog` 作为基础容器。
    2. 实现计算属性 `groupedProfiles`，将后端数组按 `attributes.topic` 分组。
    3. 渲染循环：按主题遍历 -> 创建卡片 -> 列表显示条目。
    4. 每个条目增加一个 `Input` 用于就地编辑，失去焦点触发保存。
    5. 实现“添加”弹窗，提供分类下拉框。
- **验证方法**: 查看资料时，不同主题的印象应正确归类到所属卡片下。

### 步骤 4: 实现 SettingsDialog 中的 Schema Builder
- **操作文件**: `{项目根目录}/front/src/components/SettingsDialog.vue`
- **操作描述**:
    1. 在“记忆设置”区域引入 `Accordion` 组件。
    2. 遍历 `profileConfig.topics`。
    3. 每个 AccordionItem Title 为分类名，内容区显示分类下的描述（由用户编辑）。
    4. 增加“+ 添加关注分类”按钮，点击后向数组追加空对象。
- **验证方法**: 手动修改一个分类名称并保存，确认后端收到的 YAML 映射了该修改。

## 7. 验收测试
- [ ] **Test Case 1**: 能够通过左下角菜单成功打开“个人资料”。
- [ ] **Test Case 2**: 在设置中将“日常习惯”分类改为“生活点滴”，保存后重新打开设置或资料窗口，名称应已更新。
- [ ] **Test Case 3**: 删除一条“讨厌苦瓜”的资料条目，刷新后确认为空。
- [ ] **Test Case 4**: 手动增加分类“理财偏好”，资料窗口应出现该新分类的空占位标识。
