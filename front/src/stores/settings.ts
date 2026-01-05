/**
 * Settings Store - 系统设置状态管理
 * 管理记忆设置（Memory Settings）相关配置
 */
import { defineStore } from 'pinia'
import { ref } from 'vue'
import * as SettingsAPI from '@/api/settings'

export const useSettingsStore = defineStore('settings', () => {
    // ===== Session 配置 =====
    // 会话过期时间（秒），默认 1800（30分钟）
    const passiveTimeout = ref<number>(1800)

    // ===== Loading 状态 =====
    const isLoading = ref(false)
    const isSaving = ref(false)

    /**
     * 从后端获取 session 分组的配置
     */
    const fetchSessionSettings = async () => {
        isLoading.value = true
        try {
            const settings = await SettingsAPI.getSettingsByGroup('session')
            if (settings.passive_timeout !== undefined) {
                passiveTimeout.value = settings.passive_timeout
            }
        } catch (error) {
            console.error('Failed to fetch session settings:', error)
            // 使用默认值，不抛出异常
        } finally {
            isLoading.value = false
        }
    }

    /**
     * 保存 session 配置到后端
     */
    const saveSessionSettings = async () => {
        isSaving.value = true
        try {
            await SettingsAPI.updateSettingsBulk('session', {
                passive_timeout: passiveTimeout.value,
            })
        } finally {
            isSaving.value = false
        }
    }

    /**
     * 将秒数转换为分钟显示
     */
    const getTimeoutInMinutes = (): number => {
        return Math.round(passiveTimeout.value / 60)
    }

    /**
     * 从分钟设置超时时间
     */
    const setTimeoutFromMinutes = (minutes: number) => {
        passiveTimeout.value = minutes * 60
    }

    return {
        // State
        passiveTimeout,
        isLoading,
        isSaving,
        // Actions
        fetchSessionSettings,
        saveSessionSettings,
        getTimeoutInMinutes,
        setTimeoutFromMinutes,
    }
})
