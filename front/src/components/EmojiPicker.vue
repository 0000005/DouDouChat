<script setup lang="ts">
import { Smile, Heart, ThumbsUp } from 'lucide-vue-next'
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover'
import { ScrollArea } from '@/components/ui/scroll-area'
import { ref, computed } from 'vue'

const emit = defineEmits(['select'])
const isOpen = ref(false)

const emojiGroups = [
    {
        id: 'smileys',
        name: '表情',
        icon: Smile,
        emojis: ['😀', '😁', '😂', '🤣', '😃', '😄', '😅', '😆', '😉', '😊', '😋', '😎', '😍', '😘', '🥰', '😗', '😙', '😚', '☺️', '🙂', '🤗', '🤩', '🤔', '🤨', '😐', '😑', '😶', '🙄', '😏', '😣', '😥', '😮', '🤐', '😯', '😪', '😫', '🥱', '😴', '😌', '😛', '😜', '😝', '🤤', '😒', '😓', '😔', '😕', '🙃', '🤑', '😲', '☹️', '🙁', '😖', '😞', '😟', '😤', '😢', '😭', '😦', '😧', '😨', '😩', '🤯', '😬', '😰', '😱', '🥵', '🥶', '😳', '🤪', '😵', '🥴', '😠', '😡', '🤬', '😷', '🤒', '🤕', '🤢', '🤮', '🤧', '😇', '🥳', '🥺', '🤠', '🤡', '🤥', '🤫', '🤭', '🧐', '🤓', '👿', '😈', '👹', '👺', '💀', '👻', '👽', '🤖', '💩']
    },
    {
        id: 'gestures',
        name: '手势',
        icon: ThumbsUp,
        emojis: ['👋', '🤚', '🖐️', '✋', '🖖', '👌', '🤌', '🤏', '✌️', '🤞', '🤟', '🤘', '🤙', '👈', '👉', '👆', '🖕', '👇', '☝️', '👍', '👎', '✊', '👊', '🤛', '🤜', '👏', '🙌', '👐', '🤲', '🤝', '🙏', '💪', '🦾']
    },
    {
        id: 'hearts',
        name: '心形',
        icon: Heart,
        emojis: ['❤️', '🧡', '💛', '💚', '💙', '💜', '🖤', '🤍', '🤎', '💔', '❣️', '💕', '💞', '💓', '💗', '💖', '💘', '💝', '💟']
    }
]

const activeTab = ref(emojiGroups[0].id)

const currentGroup = computed(() => {
    return emojiGroups.find(g => g.id === activeTab.value) || emojiGroups[0]
})

const selectEmoji = (emoji: string) => {
    emit('select', emoji)
    isOpen.value = false
}
</script>

<template>
    <Popover v-model:open="isOpen">
        <PopoverTrigger as-child>
            <slot>
                <button class="toolbar-btn" title="表情">
                    <Smile :size="22" />
                </button>
            </slot>
        </PopoverTrigger>
        <PopoverContent class="w-[325px] p-0 shadow-2xl border border-gray-100 rounded-xl overflow-hidden" align="start"
            side="top" :side-offset="12">
            <div class="emoji-picker-container bg-white flex flex-col h-[420px]">
                <!-- Header -->
                <div class="px-4 py-3 border-b border-gray-50 bg-white flex items-center justify-between">
                    <h4 class="font-bold text-sm text-gray-800 tracking-tight">选择表情</h4>
                </div>

                <!-- Tab Bar -->
                <div class="flex border-b border-gray-50 bg-gray-50/30 p-1.5 gap-1.5">
                    <button v-for="group in emojiGroups" :key="group.id"
                        class="flex-1 flex items-center justify-center py-1.5 rounded-md transition-all duration-300 relative border border-transparent"
                        :class="activeTab === group.id ? 'bg-white shadow-sm border-gray-100' : 'hover:bg-white/50'"
                        @click="activeTab = group.id">
                        <span class="text-xs font-medium transition-colors duration-300"
                            :class="activeTab === group.id ? 'text-green-600' : 'text-gray-500 hover:text-gray-700'">
                            {{ group.name }}
                        </span>
                    </button>
                </div>

                <!-- Emoji Content -->
                <ScrollArea class="flex-1">
                    <div class="p-3">
                        <div class="grid grid-cols-7 gap-1">
                            <button v-for="emoji in currentGroup.emojis" :key="emoji"
                                class="h-10 w-10 flex items-center justify-center hover:bg-gray-50 rounded-lg text-2xl transition-all duration-300 ease-out hover:scale-125 active:scale-90 hover:shadow-sm"
                                @click="selectEmoji(emoji)">
                                {{ emoji }}
                            </button>
                        </div>
                    </div>
                </ScrollArea>

                <!-- Footer / Indicator -->
                <div class="px-4 py-2 border-t border-gray-50 bg-gray-50/30 flex items-center justify-center">
                    <div class="flex gap-1.5 items-center">
                        <div v-for="group in emojiGroups" :key="group.id"
                            class="h-1 rounded-full transition-all duration-300"
                            :class="activeTab === group.id ? 'w-4 bg-green-500' : 'w-1 bg-gray-200'"></div>
                    </div>
                </div>
            </div>
        </PopoverContent>
    </Popover>
</template>

<style scoped>
.toolbar-btn {
    padding: 6px;
    border: none;
    background: transparent;
    color: #666;
    cursor: pointer;
    border-radius: 4px;
    transition: all 0.15s ease-in-out;
}

.toolbar-btn:hover {
    background: #e5e5e5;
    color: #333;
    transform: scale(1.05);
}

.toolbar-btn:active {
    transform: scale(0.95);
}

/* 隐藏滚动条 */
:deep(.scroll-area-viewport) {
    scrollbar-width: none;
    -ms-overflow-style: none;
}

:deep(.scroll-area-viewport)::-webkit-scrollbar {
    display: none;
}
</style>
