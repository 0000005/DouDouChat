import { ref, computed } from 'vue'
import { useSessionStore, type Message } from '@/stores/session'
import { useThinkingModeStore } from '@/stores/thinkingMode'

export { type Message }

export function useChat() {
    const store = useSessionStore()
    const thinkingModeStore = useThinkingModeStore()
    const input = ref('')
    const isSubmitting = ref(false)

    // messages is computed from store
    const messages = computed(() => store.currentMessages)

    // Status: 'idle' | 'submitted' | 'streaming'
    // submitted = waiting for first content, streaming = actively receiving content
    const status = computed(() => {
        if (store.isStreaming) return 'streaming'
        if (isSubmitting.value) return 'submitted'
        return 'ready'
    })

    // Thinking mode state
    const isThinkingMode = computed(() => thinkingModeStore.isEnabled)
    const toggleThinkingMode = () => thinkingModeStore.toggle()

    const handleSubmit = async (e?: Event | any) => {
        if (e && typeof e.preventDefault === 'function') {
            e.preventDefault()
        }
        if (!input.value.trim()) return

        const content = input.value
        input.value = ''

        isSubmitting.value = true
        try {
            await store.sendMessage(content, thinkingModeStore.isEnabled)
        } catch (error) {
            console.error(error)
        } finally {
            isSubmitting.value = false
        }
    }

    return {
        messages,
        input,
        status,
        isThinkingMode,
        toggleThinkingMode,
        handleSubmit
    }
}
