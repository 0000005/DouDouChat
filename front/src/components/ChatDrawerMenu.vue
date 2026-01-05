<script setup lang="ts">
import { computed } from 'vue'
import { useSessionStore } from '@/stores/session'
import { useFriendStore } from '@/stores/friend'
import {
    Sheet,
    SheetContent,
    SheetHeader,
    SheetTitle,
} from '@/components/ui/sheet'
import {
    MessageSquare,
    Brain,
    Search,
    Pin,
    Trash2
} from 'lucide-vue-next'

interface MenuItem {
    id: string
    label: string
    icon: any
    danger?: boolean
    action?: () => void
}

const props = defineProps<{
    open: boolean
}>()

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void
}>()

const sessionStore = useSessionStore()
const friendStore = useFriendStore()

// 获取当前好友信息
const currentFriend = computed(() => {
    if (!sessionStore.currentFriendId) return null
    return friendStore.getFriend(sessionStore.currentFriendId)
})

const currentFriendAvatar = computed(() => {
    if (!currentFriend.value) return ''
    return `https://api.dicebear.com/7.x/bottts/svg?seed=${currentFriend.value.id}`
})

const currentFriendName = computed(() => {
    return currentFriend.value?.name || '好友'
})

// 菜单项列表
const menuItems = computed<MenuItem[]>(() => [
    {
        id: 'sessions',
        label: '会话列表',
        icon: MessageSquare,
        action: () => handleMenuClick('sessions')
    },
    {
        id: 'memories',
        label: '记忆列表',
        icon: Brain,
        action: () => handleMenuClick('memories')
    },
    {
        id: 'search',
        label: '查找聊天记录',
        icon: Search,
        action: () => handleMenuClick('search')
    },
    {
        id: 'pin',
        label: '顶置聊天',
        icon: Pin,
        action: () => handleMenuClick('pin')
    },
    {
        id: 'clear',
        label: '清空聊天记录',
        icon: Trash2,
        danger: true,
        action: () => handleMenuClick('clear')
    }
])

const handleMenuClick = (menuId: string) => {
    console.log(`Menu clicked: ${menuId}`)
    // 后续 Story 中将实现具体功能
}


const handleClose = () => {
    emit('update:open', false)
}
</script>

<template>
    <Sheet :open="open" @update:open="handleClose">
        <SheetContent side="right" class="w-[360px] sm:w-[360px] p-0 flex flex-col">
            <!-- Header: 好友信息 -->
            <SheetHeader class="drawer-header">
                <div class="friend-info">
                    <div class="friend-avatar">
                        <img v-if="currentFriendAvatar" :src="currentFriendAvatar" :alt="currentFriendName" />
                    </div>
                    <SheetTitle class="friend-name">{{ currentFriendName }}</SheetTitle>
                </div>
            </SheetHeader>

            <!-- Menu List -->
            <div class="menu-list">
                <button v-for="item in menuItems" :key="item.id" class="menu-item"
                    :class="{ 'menu-item-danger': item.danger }" @click="item.action">
                    <component :is="item.icon" :size="20" class="menu-icon" />
                    <span class="menu-label">{{ item.label }}</span>
                </button>
            </div>
        </SheetContent>
    </Sheet>
</template>

<style scoped>
/* 抽屉内容容器 */
:deep([data-radix-vue-dialog-content]) {
    max-width: 360px !important;
}

/* Header 样式 */
.drawer-header {
    display: flex;
    flex-direction: row;
    align-items: center;
    justify-content: space-between;
    padding: 20px 16px;
    border-bottom: 1px solid #e5e5e5;
    background: #f5f5f5;
}

.friend-info {
    display: flex;
    align-items: center;
    gap: 12px;
    flex: 1;
}

.friend-avatar {
    width: 48px;
    height: 48px;
    border-radius: 6px;
    overflow: hidden;
    background: #e5e5e5;
    flex-shrink: 0;
}

.friend-avatar img {
    width: 100%;
    height: 100%;
    object-fit: cover;
}

.friend-name {
    font-size: 16px;
    font-weight: 500;
    color: #333;
    margin: 0;
}


/* Menu List */
.menu-list {
    flex: 1;
    background: #fff;
    padding: 8px 0;
    overflow-y: auto;
}

.menu-item {
    width: 100%;
    display: flex;
    align-items: center;
    gap: 16px;
    padding: 14px 16px;
    border: none;
    background: transparent;
    color: #333;
    cursor: pointer;
    transition: background 0.15s;
    text-align: left;
}

.menu-item:hover {
    background: #f5f5f5;
}

.menu-item:active {
    background: #ececec;
}

.menu-icon {
    flex-shrink: 0;
    color: #666;
}

.menu-label {
    font-size: 15px;
    color: #333;
}

/* 危险操作样式 (清空聊天记录) */
.menu-item-danger .menu-label {
    color: #fa5151;
}

.menu-item-danger .menu-icon {
    color: #fa5151;
}

.menu-item-danger:hover {
    background: #fff5f5;
}

/* 移动端适配 */
@media (max-width: 640px) {
    :deep([data-radix-vue-dialog-content]) {
        max-width: 100% !important;
        width: 100% !important;
    }
}

/* Override default sheet styles */
:deep(.sheet-content) {
    padding: 0 !important;
}
</style>
