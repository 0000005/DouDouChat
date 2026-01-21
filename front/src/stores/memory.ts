import { defineStore } from 'pinia'
import { ref, computed, reactive } from 'vue'
import {
    getMemoryConfig,
    updateMemoryConfig,
    getProfiles,
    addProfile,
    updateProfile,
    deleteProfile,
    deleteProfiles,
    type Profile,
    type ProfileAttributes
} from '@/api/memory'
import yaml from 'js-yaml'

/**
 * Topic configuration for UI display.
 * Maps to Memobase UserProfileTopic structure.
 */
export interface TopicConfig {
    topic: string
    description?: string
    sub_topics?: Array<{ name: string; description?: string }>
    isUnconfigured?: boolean
}

/**
 * Memory config data structure.
 * Uses overwrite_user_profiles to match Memobase ProfileConfig format.
 */
export interface MemobaseProfileConfig {
    overwrite_user_profiles?: TopicConfig[]
    additional_user_profiles?: TopicConfig[]
    profile_strict_mode?: boolean
    language?: 'en' | 'zh'
}

// Default topics that match Memobase's zh_user_profile_topics.py
const DEFAULT_TOPICS: TopicConfig[] = [
    {
        topic: '基本信息',
        description: '用户姓名、年龄、性别、国籍等基础信息',
        sub_topics: [
            { name: '用户姓名' },
            { name: '用户年龄', description: '整数' },
            { name: '性别' },
            { name: '出生日期' },
            { name: '国籍' },
            { name: '民族' },
            { name: '语言' },
        ]
    },
    {
        topic: '联系信息',
        description: '用户联系方式与所在地区信息',
        sub_topics: [
            { name: '电子邮件' },
            { name: '电话' },
            { name: '城市' },
            { name: '省份' },
        ]
    },
    {
        topic: '教育背景',
        description: '学校、专业、毕业信息等',
        sub_topics: [
            { name: '学校' },
            { name: '学位' },
            { name: '专业' },
            { name: '毕业年份' },
        ]
    },
    {
        topic: '人口统计',
        description: '婚姻与家庭结构等',
        sub_topics: [
            { name: '婚姻状况' },
            { name: '子女数量' },
            { name: '家庭收入' },
        ]
    },
    {
        topic: '工作',
        description: '公司、职位、技能等',
        sub_topics: [
            { name: '公司' },
            { name: '职位' },
            { name: '工作地点' },
            { name: '参与项目' },
            { name: '工作技能' },
        ]
    },
    {
        topic: '兴趣爱好',
        description: '书籍、电影、音乐、美食、运动等',
        sub_topics: [
            { name: '书籍' },
            { name: '电影' },
            { name: '音乐' },
            { name: '美食' },
            { name: '运动' },
        ]
    },
    {
        topic: '生活方式',
        description: '饮食偏好、运动习惯、健康状况等',
        sub_topics: [
            { name: '饮食偏好', description: '例如：素食，纯素' },
            { name: '运动习惯' },
            { name: '健康状况' },
            { name: '睡眠模式' },
            { name: '吸烟' },
            { name: '饮酒' },
        ]
    },
    {
        topic: '心理特征',
        description: '性格特点、价值观、信仰、目标等',
        sub_topics: [
            { name: '性格特点' },
            { name: '价值观' },
            { name: '信仰' },
            { name: '动力' },
            { name: '目标' },
        ]
    },
    {
        topic: '人生大事',
        description: '婚姻、搬迁、退休等',
        sub_topics: [
            { name: '婚姻' },
            { name: '搬迁' },
            { name: '退休' },
        ]
    },
]

export const useMemoryStore = defineStore('memory', () => {
    // Internal state: uses Memobase's expected format
    const _config = ref<MemobaseProfileConfig>({ overwrite_user_profiles: [] })
    const profiles = ref<Profile[]>([])
    const isLoading = ref(false)

    /**
     * Reactive accessor for topics - provides compatibility with UI components.
     * This is the array that UI components should use for v-model binding.
     */
    const profileConfig = reactive({
        get topics(): TopicConfig[] {
            return _config.value.overwrite_user_profiles || []
        },
        set topics(val: TopicConfig[]) {
            _config.value.overwrite_user_profiles = val
        },
        get strictMode(): boolean {
            return _config.value.profile_strict_mode ?? true
        },
        set strictMode(val: boolean) {
            _config.value.profile_strict_mode = val
        }
    })

    const normalizeTopics = (topics: TopicConfig[]) => topics.map(t => ({
        ...t,
        sub_topics: t.sub_topics || []
    }))

    const fetchConfig = async () => {
        try {
            const res = await getMemoryConfig()
            if (res.profile_config) {
                const parsed = yaml.load(res.profile_config) as MemobaseProfileConfig
                // Handle both old format (topics) and new format (overwrite_user_profiles)
                if (parsed.overwrite_user_profiles) {
                    _config.value = {
                        ...parsed,
                        overwrite_user_profiles: normalizeTopics(parsed.overwrite_user_profiles),
                        profile_strict_mode: parsed.profile_strict_mode ?? true
                    }
                } else if ((parsed as any).topics) {
                    // Migration from old format
                    _config.value = {
                        overwrite_user_profiles: normalizeTopics((parsed as any).topics),
                        profile_strict_mode: true
                    }
                } else {
                    _config.value = { overwrite_user_profiles: [...DEFAULT_TOPICS], profile_strict_mode: true }
                }
            } else {
                // Fallback to defaults if empty
                _config.value = { overwrite_user_profiles: [...DEFAULT_TOPICS], profile_strict_mode: true }
            }
        } catch (error) {
            console.error('Failed to fetch memory config:', error)
            // Fallback
            _config.value = { overwrite_user_profiles: [...DEFAULT_TOPICS], profile_strict_mode: true }
        }
    }

    const saveConfig = async () => {
        try {
            // Ensure all topics have sub_topics field
            const configToSave: MemobaseProfileConfig = {
                overwrite_user_profiles: (_config.value.overwrite_user_profiles || []).map(t => ({
                    topic: t.topic,
                    description: t.description,
                    sub_topics: t.sub_topics || []
                })),
                profile_strict_mode: _config.value.profile_strict_mode ?? true,
                language: _config.value.language
            }
            const yamlStr = yaml.dump(configToSave)
            await updateMemoryConfig(yamlStr)
        } catch (error) {
            console.error('Failed to save memory config:', error)
            throw error
        }
    }

    const fetchProfiles = async () => {
        isLoading.value = true
        try {
            const res = await getProfiles()
            profiles.value = res.profiles
        } catch (error) {
            console.error('Failed to fetch profiles:', error)
        } finally {
            isLoading.value = false
        }
    }

    const upsertProfile = async (id: string | null, content: string, attributes: ProfileAttributes) => {
        try {
            if (id) {
                await updateProfile(id, content, attributes)
            } else {
                await addProfile(content, attributes)
            }
            await fetchProfiles()
        } catch (error) {
            console.error('Failed to upsert profile:', error)
            throw error
        }
    }

    const removeProfile = async (id: string) => {
        try {
            await deleteProfile(id)
            await fetchProfiles()
        } catch (error) {
            console.error('Failed to delete profile:', error)
            throw error
        }
    }

    const removeProfiles = async (ids: string[]) => {
        if (ids.length === 0) return
        try {
            await deleteProfiles(ids)
            // Do not refresh here, let the caller decide
        } catch (error) {
            console.error('Failed to delete profiles:', error)
            throw error
        }
    }

    const groupedProfiles = computed(() => {
        const groups: Record<string, Profile[]> = {}

        // Initialize groups with topics from config
        // Note: profileConfig is reactive, access .topics directly (not .value.topics)
        profileConfig.topics.forEach((t: TopicConfig) => {
            groups[t.topic] = []
        })

        // Add profiles to groups
        profiles.value.forEach(p => {
            const topic = p.attributes.topic || '其他'

            // Direct match: if the topic is already configured, add to it
            if (groups[topic] !== undefined) {
                groups[topic].push(p)
            } else {
                // Dynamic group: create a new group for topics not in config
                // This ensures we don't hide any profile data
                if (!groups[topic]) {
                    groups[topic] = []
                }
                groups[topic].push(p)
            }
        })

        return groups
    })

    const displayTopics = computed(() => {
        const configured = profileConfig.topics
        const configuredSet = new Set(configured.map(t => t.topic))
        const extraTopics = Object.keys(groupedProfiles.value).filter(t => !configuredSet.has(t))
        const extra = extraTopics.map(topic => ({ topic, description: '未配置主题', sub_topics: [], isUnconfigured: true }))
        return [...configured, ...extra]
    })

    const includeTopicFromProfiles = async (topic: string) => {
        if (profileConfig.topics.some(t => t.topic === topic)) return
        const subTopicSet = new Set<string>()
        profiles.value.forEach(p => {
            if (p.attributes.topic === topic && p.attributes.sub_topic) {
                subTopicSet.add(p.attributes.sub_topic)
            }
        })
        const sub_topics = Array.from(subTopicSet).map(name => ({ name }))
        profileConfig.topics.push({ topic, description: '', sub_topics })
        await saveConfig()
    }

    return {
        profileConfig,
        profiles,
        isLoading,
        fetchConfig,
        saveConfig,
        fetchProfiles,
        upsertProfile,
        removeProfile,
        removeProfiles,
        groupedProfiles,
        displayTopics,
        includeTopicFromProfiles
    }
})
