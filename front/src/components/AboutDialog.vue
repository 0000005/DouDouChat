<script setup lang="ts">
import { computed } from 'vue'
import packageJson from '../../package.json'
import { Bug, FileText, RefreshCw, CheckCircle2 } from 'lucide-vue-next'
import { useUpdateCheck } from '@/composables/useUpdateCheck'
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

const {
    latestVersion,
    isChecking,
    updateAvailable,
    error,
    checkUpdate,
    openReleases
} = useUpdateCheck()

const appVersion = packageJson.version
const githubUrl = 'https://github.com/0000005/WeChatAgent'
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
                    <div class="flex items-center gap-2">
                        <template v-if="updateAvailable">
                            <span class="text-[#07c160] font-medium animate-pulse">发现新版本 v{{ latestVersion }}</span>
                            <button class="text-[#07c160] hover:underline flex items-center gap-1"
                                @click="openReleases">
                                立即下载
                            </button>
                        </template>
                        <template v-else>
                            <button
                                class="text-[#07c160] hover:underline flex items-center gap-1 disabled:opacity-50 disabled:cursor-not-allowed"
                                :disabled="isChecking" @click="checkUpdate">
                                <RefreshCw v-if="isChecking" :size="14" class="animate-spin" />
                                <CheckCircle2 v-else-if="latestVersion && !updateAvailable && !error" :size="14" />
                                {{ isChecking ? '正在检查...' : (error ? '检查失败' : (latestVersion && !updateAvailable ?
                                    '已是最新版本' : '检查更新')) }}
                            </button>
                        </template>
                    </div>
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
