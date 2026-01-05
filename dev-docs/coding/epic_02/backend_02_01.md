# 后端开发文档 - 个人资料自定义与管理 (Profile Customization)

## 1. 需求理解与澄清

### 核心需求
在 WeAgentChat 中，AI 代理会根据对话内容自动提取用户的个人资料（Profile）。本需求旨在提供一套 API，让用户能够：
1.  **管理资料结构 (Schema)**：自定义 AI 记录资料的维度（如：增加“健康习惯”分类），以 YAML 格式存储。
2.  **维护资料内容 (Content)**：手动增加、修改、删除 AI 提取的关于用户的所有事实条目。
3.  **用户一致性**：使用基于 `"default_user"` 生成的确定性 UUID (`uuid5`) 作为 `user_id`，并使用 SDK 默认的 `__root__` 作为 `space_id`。

### 关键功能点
- **YAML 配置读写**：支持获取和保存 memobase 系统中的项目配置（YAML 字符串）。
- **Profile CRUD**：提供对 `user_profiles` 表的增删改查接口。
- **桥接层补全**：在 `MemoService` (bridge.py) 中暴露底层 SDK 的相关控制器。

### 澄清事项
- **数据流向**：前端直接提交 YAML 字符串给后端，后端透传给 `memobase_server` 进行持久化，不负责在 server 端进行 YAML 解析校验（SDK 内部负责）。
- **数据隔离**：目前仅支持默认用户和默认空间，接口预留参数但内部硬编码为默认值。
- **默认上下文**：鉴于用户可能在未聊天前就访问此页面，API 需确保默认用户和空间已初始化。

## 2. Codebase 现状分析

### 现有架构
- **桥接服务 (`bridge.py`)**：已实现 `ensure_user`, `get_user_profiles`, `add_user_profiles`, `update_user_profiles` 等基础方法。
- **SDK 控制器**：底层 `memobase_server/controllers/project.py` 已提供 `get_project_profile_config_string` 和 `update_project_profile_config`。
- **数据模型**：`memobase_server/models/response.py` 中已有 `UserProfilesData`, `IdData`, `ProfileConfigData` 等 Pydantic 模型。

### 缺失部分
1.  **Bridge 缺项**：`MemoService` 缺少对 `Project` 配置（即 YAML Schema）的读写封装。
2.  **API 接入点**：尚未建立 `/api/memory/*` 系列路由。
3.  **接口适配**：SDK 接口多为批量操作，API 层需要封装成更符合前端习惯的单体或特定结构。

## 3. 代码实现思路

### 架构设计
延续 `API -> MemoService (Bridge) -> SDK Controllers` 的调用链路。

1.  **API Layer (`endpoints/profile.py`)**:
    - 路由分组：`/memory/config` (Schema管理) 和 `/memory/profiles` (数据管理)。
    - 负责 Request/Response DTO 的定义与转换。
    - 负责全局异常捕获与 HTTP 状态码映射。

2.  **Service Layer (`MemoService` in `bridge.py`)**:
    - 补全 `get_profile_config` 和 `update_profile_config` 方法。
    - 提供 `ensure_defaults` 方法，确保默认 User/Space 存在。

### 核心技术方案

#### A. 资料结构 (YAML) 交互接口
- `GET /api/memory/config`
  - response: `{ "data": { "profile_config": "yaml_string..." } }`
- `PUT /api/memory/config`
  - body: `{ "profile_config": "new_yaml_string..." }`
  - response: 200 OK

#### B. 资料内容管理接口
- `GET /api/memory/profiles`
  - response: `{ "data": { "profiles": [ ... ] } }`
- `POST /api/memory/profiles`
  - body: `ProfileCreate` (见下文 Schema)
  - logic: 内部调用 `add_user_profiles`，将单对象转为单元素列表。
- `PUT /api/memory/profiles/{profile_id}`
  - body: `ProfileUpdate` (见下文 Schema)
  - logic: 内部调用 `update_user_profiles`。
- `DELETE /api/memory/profiles`
  - body: `{ "profile_ids": ["uuid1", "uuid2"] }` (批量删除)
  - logic: 内部调用 `delete_user_profiles`。

#### C.异常处理策略
- **`MemoServiceException`**: 统一捕获并在 API 层转化为 HTTP 400 (Bad Request)，例如 YAML 格式错误。
- **`NOT_FOUND`**: 如果 SDK 返回 Code 404，API 层转化为 HTTP 404。
- **初始化检查**: 所有 API 调用前，若遇到 "User not found" 错误，应考虑是否需要自动调用 `ensure_user`。

### 变更规划

#### 1. 新增 API Schemas (`server/app/schemas/memory.py`)
```python
class ProfileAttributes(BaseModel):
    topic: str
    sub_topic: str

class ProfileCreate(BaseModel):
    content: str
    attributes: ProfileAttributes

class ProfileUpdate(BaseModel):
    content: str
    attributes: Optional[ProfileAttributes] = None # 传 None 表示不修改分类

class ConfigUpdate(BaseModel):
    profile_config: str

class BatchDeleteRequest(BaseModel):
    profile_ids: list[str]
```

#### 2. 修改 `server/app/services/memo/bridge.py`
- 新增 `get_profile_config` (封装 `project.get_project_profile_config_string`)。
- 新增 `update_profile_config` (封装 `project.update_project_profile_config`)。
- 确保 `ensure_user` 逻辑健壮。

#### 3. 新增 `server/app/api/endpoints/profile.py`
- 实现上述设计的 API 接口。

#### 4. 修改 `server/app/api/api.py`
- 注册新路由。

## 4. 开发实施指南

### 步骤 1: 定义数据模型 (Schema)
在 `server/app/schemas/memory.py` 中定义前端交互所需的 Pydantic 模型。
> **注意**: 尽量复用 `app.vendor.memobase_server.models.response` 中的 Native Model，如果 Native Model 过于复杂或不符合前端需求，则定义新的 Schema 并进行映射。目前看 Native Model 较为底层，建议定义专门的 View Model。

### 步骤 2: 完善 Bridge 服务
在 `server/app/services/memo/bridge.py` 中：
1.  **引入 Project Controller**:
    ```python
    from app.vendor.memobase_server.controllers.project import (
        get_project_profile_config_string, 
        update_project_profile_config
    )
    from app.vendor.memobase_server.models.response import ProfileConfigData
    ```
2.  **实现 Config 方法**:
    ```python
    @classmethod
    async def get_profile_config(cls, space_id: str) -> ProfileConfigData:
        # 实现逻辑...
    
    @classmethod
    async def update_profile_config(cls, space_id: str, config: str) -> None:
        # 实现逻辑...
    ```

### 步骤 3: 实现 API 端点
在 `server/app/api/endpoints/profile.py` 中：
1.  **硬编码上下文**:
    # 使用针对 Memobase SDK 优化的确定性上下文 (来自 app.services.memo.constants)
    DEFAULT_USER = "str(uuid5(...))" 
    DEFAULT_SPACE = "__root__"
2.  **自动初始化**:
    在 `get_profiles` 接口开始处，先调用 `await MemoService.ensure_user(DEFAULT_USER, DEFAULT_SPACE)`，确保用户存在，防止返回 404。
3.  **接口实现**:
    - `POST /api/memory/profiles`: 接收 `ProfileCreate` -> 构造列表 -> `MemoService.add_user_profiles`。
    - `PUT /api/memory/profiles/{id}`: 接收 `ProfileUpdate` -> 构造参数 -> `MemoService.update_user_profiles`。

### 步骤 4: 路由注册与验证
1.  修改 `server/app/api/api.py` 包含新路由。
2.  **验证 Checklist**:
    - [ ] `GET /api/memory/config` 返回默认 YAML。
    - [ ] `PUT /api/memory/config` 修改 YAML 后，再次 GET 能获取新值。
    - [ ] `POST /api/memory/profiles` 能添加数据，且在 `GET` 列表中可见。
    - [ ] `DELETE` 能成功移除数据。
