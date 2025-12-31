import { defineStore } from 'pinia'
import { ref, watch } from 'vue'

const STORAGE_KEY = 'doudou-thinking-mode'

export const useThinkingModeStore = defineStore('thinkingMode', () => {
    // Initialize from localStorage
    const stored = localStorage.getItem(STORAGE_KEY)
    const isEnabled = ref<boolean>(stored !== null ? JSON.parse(stored) : false)

    // Persist to localStorage when changed
    watch(isEnabled, (newValue) => {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(newValue))
    })

    const toggle = () => {
        isEnabled.value = !isEnabled.value
    }

    const enable = () => {
        isEnabled.value = true
    }

    const disable = () => {
        isEnabled.value = false
    }

    return {
        isEnabled,
        toggle,
        enable,
        disable
    }
})
