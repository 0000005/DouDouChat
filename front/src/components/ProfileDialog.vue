<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import {
    Dialog,
    DialogContent,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from '@/components/ui/dialog'
import { ScrollArea } from '@/components/ui/scroll-area'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import {
    Select,
    SelectContent,
    SelectItem,
    SelectTrigger,
    SelectValue,
} from '@/components/ui/select'

import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card'
import { useMemoryStore } from '@/stores/memory'
import { Plus, Edit2, Check, X, Loader2, Camera, Info, Trash2 } from 'lucide-vue-next'
import AvatarUploader from '@/components/common/AvatarUploader.vue'
import { useSettingsStore } from '@/stores/settings'
import { getStaticUrl } from '@/api/base'

const props = defineProps<{
    open: boolean
}>()

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void
}>()

const memoryStore = useMemoryStore()
const addingTopic = ref<string | null>(null) // Track which topic is being added to
const newEntryContent = ref('')
const newEntrySubTopic = ref<string | null>(null)
const editingId = ref<string | null>(null)
const editingContent = ref('')
const editingTopic = ref<string>('')
const editingSubTopic = ref<string | null>(null)
const isAvatarUploaderOpen = ref(false)
const settingsStore = useSettingsStore()

// Confirmation Dialog State
const confirmDialog = ref({
    open: false,
    title: '',
    message: '',
    onConfirm: () => { }
})

const showConfirmDialog = (title: string, message: string, onConfirm: () => void) => {
    confirmDialog.value = {
        open: true,
        title,
        message,
        onConfirm
    }
}

const handleConfirm = () => {
    confirmDialog.value.onConfirm()
    confirmDialog.value.open = false
}

const handleCancel = () => {
    confirmDialog.value.open = false
}

const userAvatar = computed({
    get: () => settingsStore.userAvatar,
    set: (val) => settingsStore.saveUserSettings(val)
})

const userAvatarDisplayUrl = computed(() =>
    getStaticUrl(settingsStore.userAvatar) || 'default_avatar.svg'
)

onMounted(async () => {
    if (props.open) {
        await initialize()
    }
})

watch(() => props.open, async (val) => {
    if (val) {
        await initialize()
    }
})

const initialize = async () => {
    await memoryStore.fetchConfig()
    await memoryStore.fetchProfiles()
    await settingsStore.fetchUserSettings()
}

const getSubTopics = (topic: string) => {
    return memoryStore.profileConfig.topics.find(t => t.topic === topic)?.sub_topics || []
}

const handleAddToTopic = async (topic: string) => {
    if (!newEntryContent.value.trim()) return
    try {
        await memoryStore.upsertProfile(null, newEntryContent.value, {
            topic,
            sub_topic: newEntrySubTopic.value || undefined
        })
        newEntryContent.value = ''
        newEntrySubTopic.value = null
        addingTopic.value = null
    } catch (error) {
        console.error('Failed to add profile:', error)
    }
}

const startAddingToTopic = (topic: string) => {
    addingTopic.value = topic
    newEntryContent.value = ''
    const subTopics = getSubTopics(topic)
    newEntrySubTopic.value = subTopics[0]?.name || null
}

const cancelAddingToTopic = () => {
    addingTopic.value = null
    newEntryContent.value = ''
    newEntrySubTopic.value = null
}

const startEdit = (id: string, content: string) => {
    editingId.value = id
    editingContent.value = content
    const profile = memoryStore.profiles.find(p => p.id === id)
    editingTopic.value = profile?.attributes.topic || ''
    editingSubTopic.value = profile?.attributes.sub_topic || null
}

const cancelEdit = () => {
    editingId.value = null
    editingContent.value = ''
    editingTopic.value = ''
    editingSubTopic.value = null
}

const saveEdit = async (id: string, topic: string) => {
    if (!editingContent.value.trim()) return
    try {
        await memoryStore.upsertProfile(id, editingContent.value, {
            topic: editingTopic.value || topic,
            sub_topic: editingSubTopic.value || undefined
        })
        editingId.value = null
        editingTopic.value = ''
        editingSubTopic.value = null
    } catch (error) {
        console.error('Failed to update profile:', error)
    }
}

const handleDelete = async (id: string) => {
    showConfirmDialog(
        '删除资料',
        '确定要删除这条资料记录吗？',
        async () => {
            try {
                await memoryStore.removeProfile(id)
            } catch (error) {
                console.error('Failed to delete profile:', error)
            }
        }
    )
}

// Custom directive for auto-focus on input
const vFocus = {
    mounted: (el: HTMLElement) => el.focus()
}
</script>

<template>
    <Dialog :open="open" @update:open="emit('update:open', $event)">
        <DialogContent
            class="max-w-2xl h-[80vh] flex flex-col p-0 overflow-hidden rounded-2xl border border-[#e6e6e6] bg-[linear-gradient(180deg,#f7f7f7_0%,#f0f1f3_100%)] shadow-[0_20px_60px_-20px_rgba(0,0,0,0.35)]">
            <DialogHeader class="p-3 bg-white/90 backdrop-blur border-b border-[#ededed] shrink-0">
                <DialogTitle class="text-base font-semibold text-center text-[#111] tracking-wide">个人资料</DialogTitle>
            </DialogHeader>

            <!-- Avatar Section -->
            <div
                class="flex flex-col items-center py-4 bg-[linear-gradient(180deg,#ffffff_0%,#f7f7f7_100%)] border-b border-[#ededed] shrink-0">
                <div class="relative group cursor-pointer" @click="isAvatarUploaderOpen = true">
                    <img :src="userAvatarDisplayUrl"
                        class="w-24 h-24 rounded-xl object-cover border border-[#e5e7eb] shadow-[0_8px_20px_-12px_rgba(0,0,0,0.35)] bg-gray-50 ring-2 ring-[#07c160]/20" />
                    <div
                        class="absolute inset-0 bg-black/35 rounded-xl opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity backdrop-blur-[2px]">
                        <Camera class="text-white w-7 h-7" stroke-width="1.5" />
                    </div>
                </div>
                <div class="mt-2 text-xs text-gray-500">点击更换头像</div>
            </div>

            <!-- Tip Message -->
            <div class="px-6 py-2 shrink-0 bg-[#f8fff9] border-b border-[#e7f7ed]">
                <div class="flex items-center gap-2 text-[#07c160]/90">
                    <Info class="w-3.5 h-3.5" />
                    <p class="text-[11px] font-medium">
                        提示：个人资料由 AI 随聊天进程自动更新；如需调整分类与子主题，请到「记忆设置」中修改。
                    </p>
                </div>
            </div>


            <ScrollArea class="flex-1 p-3">
                <div class="space-y-4">
                    <div v-if="memoryStore.isLoading && memoryStore.profiles.length === 0"
                        class="flex justify-center py-8">
                        <Loader2 class="w-8 h-8 animate-spin text-gray-400" />
                    </div>

                    <template v-else>
                        <Card v-for="topic in memoryStore.displayTopics" :key="topic.topic"
                            class="border border-[#ebecef] bg-white shadow-[0_10px_24px_-16px_rgba(0,0,0,0.35)] overflow-hidden mb-3 rounded-xl">
                            <CardHeader class="bg-[#fafafa] py-2 px-3 border-b border-[#efefef]">
                                <CardTitle
                                    class="text-sm font-semibold text-[#2b2f33] flex items-center justify-between">
                                    <div class="flex items-center gap-2">
                                        <span>{{ topic.topic }}</span>
                                        <span v-if="topic.isUnconfigured"
                                            class="text-[11px] px-1.5 py-0.5 rounded-full bg-amber-50 text-amber-600 border border-amber-200">
                                            未配置
                                        </span>
                                    </div>
                                    <div class="flex items-center gap-2">
                                        <span class="text-xs font-normal text-gray-400 mr-2">{{ topic.description
                                        }}</span>
                                        <Button size="icon" variant="ghost"
                                            class="h-7 w-7 text-[#07c160] hover:text-[#06ad55] hover:bg-[#e9f8ef]"
                                            :disabled="topic.isUnconfigured" @click="startAddingToTopic(topic.topic)">
                                            <Plus class="h-4 w-4" />
                                        </Button>
                                    </div>
                                </CardTitle>
                            </CardHeader>
                            <CardContent class="p-0 bg-white">
                                <!-- Add new entry form for this topic -->
                                <div v-if="addingTopic === topic.topic"
                                    class="p-2.5 border-b border-gray-100 bg-[#f6f7f8]">
                                    <div class="flex items-center gap-2">
                                        <Select v-if="getSubTopics(topic.topic).length" v-model="newEntrySubTopic">
                                            <SelectTrigger class="h-8 w-[140px] bg-white text-xs focus:ring-[#07c160]">
                                                <SelectValue placeholder="选择子主题" />
                                            </SelectTrigger>
                                            <SelectContent>
                                                <SelectItem v-for="st in getSubTopics(topic.topic)" :key="st.name"
                                                    :value="st.name">
                                                    {{ st.name }}
                                                </SelectItem>
                                            </SelectContent>
                                        </Select>
                                        <Input v-model="newEntryContent" placeholder="输入资料内容..."
                                            class="h-8 text-sm flex-1 bg-white focus-visible:ring-[#07c160]"
                                            @keyup.enter="handleAddToTopic(topic.topic)"
                                            @keyup.esc="cancelAddingToTopic" v-focus />
                                        <Button size="icon" variant="ghost" class="h-8 w-8 text-[#07c160]"
                                            @click="handleAddToTopic(topic.topic)">
                                            <Check class="h-4 w-4" />
                                        </Button>
                                        <Button size="icon" variant="ghost" class="h-8 w-8 text-gray-400"
                                            @click="cancelAddingToTopic">
                                            <X class="h-4 w-4" />
                                        </Button>
                                    </div>
                                </div>
                                <div v-if="memoryStore.groupedProfiles[topic.topic]?.length === 0 && addingTopic !== topic.topic"
                                    class="p-4 text-center text-sm text-gray-400">
                                    暂无记录
                                </div>
                                <div v-else class="divide-y divide-gray-100">
                                    <div v-for="profile in memoryStore.groupedProfiles[topic.topic]" :key="profile.id"
                                        class="group flex items-start gap-3 p-2.5 hover:bg-[#f7f8f9] transition-colors">
                                        <div class="flex-1">
                                            <div v-if="editingId === profile.id" class="flex items-center gap-2">
                                                <div class="flex items-center gap-2 w-full">
                                                    <Select v-model="editingTopic">
                                                        <SelectTrigger
                                                            class="h-8 w-[140px] bg-white text-xs focus:ring-[#07c160]">
                                                            <SelectValue placeholder="选择分类" />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem v-for="t in memoryStore.profileConfig.topics"
                                                                :key="t.topic" :value="t.topic">
                                                                {{ t.topic }}
                                                            </SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                    <Select v-if="getSubTopics(editingTopic).length"
                                                        v-model="editingSubTopic">
                                                        <SelectTrigger
                                                            class="h-8 w-[140px] bg-white text-xs focus:ring-[#07c160]">
                                                            <SelectValue placeholder="选择子主题" />
                                                        </SelectTrigger>
                                                        <SelectContent>
                                                            <SelectItem v-for="st in getSubTopics(editingTopic)"
                                                                :key="st.name" :value="st.name">
                                                                {{ st.name }}
                                                            </SelectItem>
                                                        </SelectContent>
                                                    </Select>
                                                    <Input v-model="editingContent"
                                                        class="h-8 text-sm bg-white focus-visible:ring-[#07c160] flex-1"
                                                        @keyup.enter="saveEdit(profile.id, topic.topic)"
                                                        @keyup.esc="cancelEdit" v-focus />
                                                </div>
                                                <Button size="icon" variant="ghost" class="h-8 w-8 text-[#07c160]"
                                                    @click="saveEdit(profile.id, topic.topic)">
                                                    <Check class="h-4 w-4" />
                                                </Button>

                                                <Button size="icon" variant="ghost" class="h-8 w-8 text-gray-400"
                                                    @click="cancelEdit">
                                                    <X class="h-4 w-4" />
                                                </Button>
                                            </div>
                                            <div v-else
                                                class="text-sm text-gray-700 leading-relaxed whitespace-pre-wrap">
                                                {{ profile.content }}
                                                <span v-if="profile.attributes.sub_topic"
                                                    class="ml-2 text-[11px] text-gray-400">#{{
                                                        profile.attributes.sub_topic }}</span>
                                            </div>
                                        </div>

                                        <div v-if="editingId !== profile.id" class="flex items-center gap-1 shrink-0">
                                            <Button size="icon" variant="ghost"
                                                class="h-8 w-8 text-gray-400 hover:text-[#07c160]"
                                                @click="startEdit(profile.id, profile.content)">
                                                <Edit2 class="h-4 w-4" />
                                            </Button>
                                            <Button size="icon" variant="ghost"
                                                class="h-8 w-8 text-red-500 hover:text-red-600"
                                                @click="handleDelete(profile.id)">
                                                <Trash2 class="h-4 w-4 text-red-500" color="#ef4444" />
                                            </Button>
                                        </div>
                                    </div>
                                </div>
                            </CardContent>
                        </Card>
                    </template>
                </div>
            </ScrollArea>

            <div class="p-3 bg-white border-t border-[#ededed] shrink-0">
                <div
                    class="flex items-center justify-between text-xs text-gray-500 bg-[#f7f8f9] rounded-xl border border-[#e6e8eb] px-3 py-2.5">
                    <span>分类与子主题需在「记忆设置」中维护</span>
                </div>
            </div>

            <DialogFooter class="hidden">
                <!-- Prevent default footer -->
            </DialogFooter>
        </DialogContent>
    </Dialog>

    <!-- Confirmation Dialog -->
    <Dialog :open="confirmDialog.open" @update:open="(val) => confirmDialog.open = val">
        <DialogContent
            class="sm:max-w-md rounded-2xl border border-[#e6e6e6] shadow-[0_18px_50px_-20px_rgba(0,0,0,0.35)]">
            <DialogHeader class="pb-2">
                <DialogTitle class="text-base font-semibold text-[#111]">{{ confirmDialog.title }}</DialogTitle>
            </DialogHeader>
            <div class="py-4">
                <p class="text-sm text-gray-600 whitespace-pre-line">{{ confirmDialog.message }}</p>
            </div>
            <DialogFooter class="flex gap-2">
                <Button variant="outline" @click="handleCancel">取消</Button>
                <Button class="bg-red-600 hover:bg-red-700" @click="handleConfirm">确认删除</Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>

    <AvatarUploader v-if="isAvatarUploaderOpen" :initial-image="userAvatar || undefined" title="设置个人头像"
        @update:image="(url) => userAvatar = url" @close="isAvatarUploaderOpen = false" />
</template>

<style scoped>
:deep(.lucide) {
    stroke-width: 1.5;
}
</style>
