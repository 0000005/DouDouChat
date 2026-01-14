<script setup lang="ts">
import { computed } from 'vue'
import packageJson from '../../package.json'
import { Bug, FileText } from 'lucide-vue-next'
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
} from '@/components/ui/dialog'

const props = defineProps<{
    open: boolean
}>()

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void
}>()

const isOpen = computed({
    get: () => props.open,
    set: (value) => emit('update:open', value),
})

const appVersion = packageJson.version
const githubUrl = 'https://github.com/0000005/WeChatAgent'
const releaseUrl = `${githubUrl}/releases`
const authorName = 'JerryYin'

const isElectron = computed(() => !!(window as any).WeAgentChat?.isElectron)

const handleToggleDevTools = () => {
    (window as any).WeAgentChat?.debug?.toggleDevTools()
}

const handleOpenLogs = () => {
    (window as any).WeAgentChat?.shell?.openLogs()
}
</script>

<template>
    <Dialog v-model:open="isOpen">
        <DialogContent class="sm:max-w-[420px] p-0 overflow-hidden bg-[#f7f7f7] border-none shadow-2xl">
            <DialogHeader class="px-5 py-4 bg-white border-b">
                <DialogTitle class="text-base font-medium text-center">关于 WeAgentChat</DialogTitle>
                <DialogDescription class="sr-only">版本信息与项目地址</DialogDescription>
            </DialogHeader>
            <div class="px-5 py-4 space-y-3 text-sm text-gray-700">
                <div class="flex items-center justify-between">
                    <span class="text-gray-500">软件版本</span>
                    <span class="font-medium text-gray-900">v{{ appVersion }}</span>
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-gray-500">版本更新</span>
                    <a class="text-[#07c160] hover:underline" :href="releaseUrl" target="_blank" rel="noreferrer">
                        查看更新
                    </a>
                </div>
                <div class="space-y-1">
                    <div class="text-gray-500">GitHub 地址（求 Star）</div>
                    <a class="text-[#07c160] break-all hover:underline" :href="githubUrl" target="_blank"
                        rel="noreferrer">
                        {{ githubUrl }}
                    </a>
                </div>
                <div class="flex items-center justify-between">
                    <span class="text-gray-500">作者</span>
                    <span class="font-medium text-gray-900">{{ authorName }}</span>
                </div>

                <!-- Debug Tools (Electron Only) -->
                <div v-if="isElectron" class="pt-4 mt-2 border-t border-gray-200 flex gap-3">
                    <button
                        class="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-md shadow-sm hover:bg-gray-50 hover:text-gray-900 transition-colors"
                        @click="handleToggleDevTools">
                        <Bug :size="14" />
                        调试面板
                    </button>
                    <button
                        class="flex-1 flex items-center justify-center gap-2 px-3 py-2 text-xs font-medium text-gray-600 bg-white border border-gray-200 rounded-md shadow-sm hover:bg-gray-50 hover:text-gray-900 transition-colors"
                        @click="handleOpenLogs">
                        <FileText :size="14" />
                        查看日志
                    </button>
                </div>
            </div>
        </DialogContent>
    </Dialog>
</template>
