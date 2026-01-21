import yaml

DEFAULT_PROFILE_CONFIG = {
    "language": "zh",
    "profile_strict_mode": True,
    "overwrite_user_profiles": [
        {
            "topic": "基本信息",
            "description": "用户姓名、年龄、性别、国籍等基础信息",
            "sub_topics": [
                {"name": "用户姓名"},
                {"name": "用户年龄", "description": "整数"},
                {"name": "性别"},
                {"name": "出生日期"},
                {"name": "国籍"},
                {"name": "民族"},
                {"name": "语言"},
            ],
        },
        {
            "topic": "联系信息",
            "description": "用户联系方式与所在地区信息",
            "sub_topics": [
                {"name": "电子邮件"},
                {"name": "电话"},
                {"name": "城市"},
                {"name": "省份"},
            ],
        },
        {
            "topic": "教育背景",
            "description": "学校、专业、毕业信息等",
            "sub_topics": [
                {"name": "学校"},
                {"name": "学位"},
                {"name": "专业"},
                {"name": "毕业年份"},
            ],
        },
        {
            "topic": "人口统计",
            "description": "婚姻与家庭结构等",
            "sub_topics": [
                {"name": "婚姻状况"},
                {"name": "子女数量"},
                {"name": "家庭收入"},
            ],
        },
        {
            "topic": "工作",
            "description": "公司、职位、技能等",
            "sub_topics": [
                {"name": "公司"},
                {"name": "职位"},
                {"name": "工作地点"},
                {"name": "参与项目"},
                {"name": "工作技能"},
            ],
        },
        {
            "topic": "兴趣爱好",
            "description": "书籍、电影、音乐、美食、运动等",
            "sub_topics": [
                {"name": "书籍"},
                {"name": "电影"},
                {"name": "音乐"},
                {"name": "美食"},
                {"name": "运动"},
            ],
        },
        {
            "topic": "生活方式",
            "description": "饮食偏好、运动习惯、健康状况等",
            "sub_topics": [
                {"name": "饮食偏好", "description": "例如：素食，纯素"},
                {"name": "运动习惯"},
                {"name": "健康状况"},
                {"name": "睡眠模式"},
                {"name": "吸烟"},
                {"name": "饮酒"},
            ],
        },
        {
            "topic": "心理特征",
            "description": "性格特点、价值观、信仰、目标等",
            "sub_topics": [
                {"name": "性格特点"},
                {"name": "价值观"},
                {"name": "信仰"},
                {"name": "动力"},
                {"name": "目标"},
            ],
        },
        {
            "topic": "人生大事",
            "description": "婚姻、搬迁、退休等",
            "sub_topics": [
                {"name": "婚姻"},
                {"name": "搬迁"},
                {"name": "退休"},
            ],
        },
    ],
}


def get_default_profile_config_yaml() -> str:
    return yaml.dump(DEFAULT_PROFILE_CONFIG, allow_unicode=True, sort_keys=False)
