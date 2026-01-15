完整需求（整理版）

  背景
  - 当前传给 Memobase 的 chatHistory 是全量会话（用户 + 好友/assistant 多轮）。
  - Memobase 默认抽取逻辑更像“只基于用户话语”。
  - 导致好友/assistant 内容污染用户 profile。

  目标

  - 继续使用全量会话输入。
  - 通过 prompt 约束，只记录真实用户(ROLE=user)的事实，忽略好友/assistant 自述或设定。

  要改的 prompt（仅中文）
  1. server/app/vendor/memobase_server/prompts/zh_summary_entry_chats.py
  2. server/app/vendor/memobase_server/prompts/zh_extract_profile.py
  3. server/app/vendor/memobase_server/prompts/event_tagging.py

  Few-shot 要求

  - 必须是真实多轮对话，user 与 assistant 交替多轮。
  - few-shot 不出现在 system prompt。
  - few-shot 作为“history_messages”形式出现，结构类似：

    system: 规则说明（不含 few-shot）
    user: <few-shot 输入A>
    assistant: <few-shot 输出A>
    user: <few-shot 输入B>
    assistant: <few-shot 输出B>

  约束

  - system prompt 仅放规则、格式、注意事项，不放示例对话。
  - 输出必须严格以“真实用户事实”为准，来源不明则不写入。

  实现前提（记录用）

  - 目前调用只传 system_prompt + prompt，history_messages 为空。
  - 若要满足“few-shot 不在 system prompt”，需要在调用处把 few-shot 放进 history_messages。

  测试预期结果 (Expected Results)
  
  为验证 Prompt 优化的有效性，设计了以下 8 个测试场景，覆盖不同长度和复杂度的对话。执行测试脚本 `server/tests/test_memory_extraction_complex.py` 后，请对照以下标准进行评估。

  #### 短对话场景 (< 10 轮)

  **1. scenario1_mixed (基础混合)**
  - **核心目标**: 提取基础 Profile 和爱好。
  - **Profile 应包含**:
    - 居住地: 上海 (静安区)
    - 职业: 前端开发 (头部互联网公司)
    - 爱好: 散步 (武康路)、健身 (撸铁)
  - **Event 应包含**:
    - 用户刚搬到上海静安区。
    - 用户周末喜欢去武康路散步或去健身房。

  **2. scenario2_pollution (抗干扰测试)**
  - **核心目标**: **关键测试**。确保助手的个人设定（喜欢巴赫、徒步、摄影、模拟喜马拉雅远足）**绝对不被**记入用户 Profile。
  - **Profile 应包含**:
    - 音乐偏好: 周杰伦
  - **Profile 不应包含**:
    - 巴赫、古典音乐
    - 徒步旅行、摄影 (除非用户自己提到)
    - 喜马拉雅山远足

  **3. scenario3_indirect (间接信息)**
  - **核心目标**: 虽然用户是在谈论家人，但应适当记录为用户的背景信息或事件。
  - **Event/Profile 应包含**:
    - 母亲最近感冒了。
    - 父亲身体不错，爱锻炼。
    - 老家: 苏州 (一个月回一次)。

  **4. scenario4_time (时间感知)**
  - **核心目标**: 能够根据对话时间 (2026/01/15) 推算出相对时间的具体日期。
  - **Event 应包含**:
    - [2026/01/19] 计划去北京出差，为期三天。
    - [2026/01/16] 晚间计划在静安嘉里中心与大学同学聚餐。

  #### 长对话场景 (> 10 轮)

  **5. scenario5_long_work (工作深度)**
  - **核心目标**: 提取详细职业背景。
  - **Profile 应包含**:
    - 公司: 数盈科技 (金融科技)
    - 职位: 后端开发 (Java, Python)
    - 团队规模: 8人 (核心开发组)
    - 技术栈: Spring Cloud, 微服务
    - 状态: 最近因为技术债务和新系统上线经常加班 (每天至10点)。
    - 计划: 打算 3 月份由大厂 (阿里/字节) 跳槽，目前在等年终奖。

  **6. scenario6_long_life (生活深度)**
  - **核心目标**: 提取生活、健康及情感状态。
  - **Profile 应包含**:
    - 健康: 血脂偏高
    - 居住: 上海徐汇区 (靠近徐家汇)，房租 8000/月。
    - 情感: 有女朋友 (大学同学，产品经理)，交往快两年。
    - 计划: 打算明年结婚，目前存了 30 万，考虑在嘉定或松江买房。
    - 背景: 女朋友是杭州人。

  **7. scenario7_long_hobby (兴趣深度)**
  - **核心目标**: 细粒度的兴趣画像。
  - **Profile 应包含**:
    - 电影: 喜欢科幻 (《盗梦空间》) 和悬疑 (《记忆碎片》)，刚看了《奥本海默》。
    - 习惯: 每月去 CGV 看 2-3 次电影。
    - 游戏: 主机玩家 (PS5)，玩《艾尔登法环》(觉得难)，《只狼》(通关3遍)，《原神》(氪金1万多)。
    - 摄影: 设备 Sony A7M4，喜欢拍城市风光和人像。
    - 旅游: 去过新疆、日本，计划去欧洲。

  **8. scenario8_long_mixed (综合话题)**
  - **核心目标**: 跨领域的综合信息提取。
  - **Profile 应包含**:
    - 公司: 云效科技 (企业SaaS, B轮, 估值5亿)。
    - 职位: 产品经理 (CRM模块, 带2人)。
    - 经历: 曾在腾讯微信支付工作 2 年。
    - 状态: 感觉创业公司不稳定且累，考虑回大厂。
    - 宠物: 计划养英短蓝猫，下周末去看。
    - 情感: 女朋友在美团做运营。

---

## 最新实现与优化记录 (2026/01/15)

针对原始需求中的“事实混淆”和“分类不精准”问题，我们已落地并验证了以下三大优化方案：

### 1. 显式对话标注 (Anti-Pollution Tagging)
**痛点**: LLM 在全量会话中难以区分 user 事实与 assistant 自述。
**方案**: 在 `server/app/vendor/memobase_server/utils.py` 的 `get_blob_str` 函数中，对所有 `assistant` 角色的消息进行了自动化包装。
**实现**: 每一条助手消息末尾都会强制追加标注：`【AI发言，仅供参考，不记录】`。
**效果**: 哪怕助手说“我喜欢巴赫，也喜欢徒步”，LLM 在摘要阶段能通过直观的标签立即识别并跳过，有效解决了“事实污染”问题。

### 2. 项目级自定义画像分类 (Custom Profile Strategy)
**痛点**: 默认的画像分类（如“姓名”、“年龄”）过于通用，无法满足社交沙盒（Sandbox）所需的“性格”、“兴趣”、“生活习惯”等深度描述。
**方案**: 实现了 `update_project_profile_config` 的注入机制，允许每个 Space 拥有独立的 `UserProfileTopic` 配置。
**主要分类结构**:
- **基本信息**: 姓名、所在地等。
- **职业与教育**: 学校、公司、职业目标。
- **兴趣爱好**: 运动、音乐、美食、游戏、旅游等。
- **生活习惯**: 作息、消费习惯、居住环境。
- **性格与情感**: 性格特点、心情、情感状态。
- **人际关系**: 家人、伴侣、朋友、宠物。
**效果**: 分类更精准，提取出的信息更符合“社交模拟”的语境。

### 3. 多阶段调试架构 (Debug-Oriented Infrastructure)
**痛点**: 难以观测 LLM 的原始输出（Raw Response），无法判断是 Prompt 问题还是逻辑代码 Parsing 问题。
**方案**: 重构并加强了 `server/tests/test_memory_extraction_complex.py`。
- **RAW 观测**: 修改日志记录，显式打印 LLM 的 `INPUT PROMPT` 和 `RAW MODEL OUTPUT`，无需猜测。
- **自动化流式注入**: 脚本支持一次性运行多个场景，并自动执行 Profile 注入逻辑，实现了“改 Prompt -> 跑测试 -> 看 Raw -> 验证结果”的高效闭环。

### 待后续优化方向
- **Event Tagging**: 引入更多社交维度的事件标签（例如：`Dating`, `Conflict`, `Work_Achievement`）。
- **时间推算强化**: 在 Prompt 中进一步固化针对“上周”、“大前天”等相对时间的推算逻辑模板。