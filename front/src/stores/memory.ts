import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import {
    getMemoryConfig,
    updateMemoryConfig,
    getProfiles,
    addProfile,
    updateProfile,
    deleteProfile,
    type Profile,
    type ProfileAttributes
} from '@/api/memory'
import yaml from 'js-yaml'

export interface TopicConfig {
    topic: string
    description?: string
    [key: string]: any
}

export interface MemoryConfigData {
    topics: TopicConfig[]
}

export const useMemoryStore = defineStore('memory', () => {
    const profileConfig = ref<MemoryConfigData>({ topics: [] })
    const profiles = ref<Profile[]>([])
    const isLoading = ref(false)

    const fetchConfig = async () => {
        try {
            const res = await getMemoryConfig()
            if (res.profile_config) {
                profileConfig.value = yaml.load(res.profile_config) as MemoryConfigData
            } else {
                // Fallback to defaults if empty
                profileConfig.value = {
                    topics: [
                        { topic: '基本特征', description: '姓名、年龄、职业等基础信息' },
                        { topic: '性格习惯', description: '性格特点、日常习惯等' },
                        { topic: '兴趣爱好', description: '喜欢的事物、常去的地点等' }
                    ]
                }
            }
        } catch (error) {
            console.error('Failed to fetch memory config:', error)
            // Fallback
            profileConfig.value = {
                topics: [
                    { topic: '基本特征', description: '姓名、年龄、职业等基础信息' },
                    { topic: '性格习惯', description: '性格特点、日常习惯等' },
                    { topic: '兴趣爱好', description: '喜欢的事物、常去的地点等' }
                ]
            }
        }
    }

    const saveConfig = async () => {
        try {
            const yamlStr = yaml.dump(profileConfig.value)
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

    const groupedProfiles = computed(() => {
        const groups: Record<string, Profile[]> = {}

        // Initialize groups with topics from config
        profileConfig.value.topics.forEach(t => {
            groups[t.topic] = []
        })

        // Add profiles to groups
        profiles.value.forEach(p => {
            const topic = p.attributes.topic || '其他'
            if (!groups[topic]) {
                groups[topic] = []
            }
            groups[topic].push(p)
        })

        return groups
    })

    return {
        profileConfig,
        profiles,
        isLoading,
        fetchConfig,
        saveConfig,
        fetchProfiles,
        upsertProfile,
        removeProfile,
        groupedProfiles
    }
})
