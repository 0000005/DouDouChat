import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { useSettingsStore } from '@/stores/settings'

export const useThinkingModeStore = defineStore('thinkingMode', () => {
    const settingsStore = useSettingsStore()

    const isEnabled = computed(() => settingsStore.enableThinking)

    const toggle = async () => {
        settingsStore.enableThinking = !settingsStore.enableThinking
        await settingsStore.saveChatSettings()
    }

    const enable = async () => {
        settingsStore.enableThinking = true
        await settingsStore.saveChatSettings()
    }

    const disable = async () => {
        settingsStore.enableThinking = false
        await settingsStore.saveChatSettings()
    }

    return {
        isEnabled,
        toggle,
        enable,
        disable
    }
})
