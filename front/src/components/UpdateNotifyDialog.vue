<script setup lang="ts">
import {
    Dialog,
    DialogContent,
    DialogDescription,
    DialogHeader,
    DialogTitle,
    DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Download } from 'lucide-vue-next'

const props = defineProps<{
    open: boolean
    latestVersion: string
    currentVersion: string
}>()

const emit = defineEmits<{
    (e: 'update:open', value: boolean): void
    (e: 'download'): void
}>()

const handleOpenChange = (value: boolean) => {
    emit('update:open', value)
}

const handleDownload = () => {
    emit('download')
    emit('update:open', false)
}
</script>

<template>
    <Dialog :open="open" @update:open="handleOpenChange">
        <DialogContent class="sm:max-w-[400px] p-0 overflow-hidden bg-white border-none shadow-2xl">
            <DialogHeader class="px-6 py-5 bg-[#f7f7f7] border-b">
                <div class="flex items-center gap-2 text-[#07c160]">
                    <Download :size="20" stroke-width="2.5" />
                    <DialogTitle class="text-base font-semibold text-gray-900">发现新版本</DialogTitle>
                </div>
                <DialogDescription class="sr-only">有新版本可供下载</DialogDescription>
            </DialogHeader>

            <div class="px-8 py-6 flex flex-col items-center text-center space-y-4">
                <div
                    class="w-16 h-16 bg-[#07c160]/10 rounded-full flex items-center justify-center text-[#07c160] mb-2">
                    <Download :size="32" />
                </div>

                <div class="space-y-2">
                    <p class="text-gray-600">
                        WeAgentChat 有新版本可用了！
                    </p>
                    <div class="flex items-center justify-center gap-2 text-sm">
                        <span class="px-2 py-0.5 bg-gray-100 rounded text-gray-500">v{{ currentVersion }}</span>
                        <span class="text-gray-300">→</span>
                        <span class="px-2 py-0.5 bg-[#07c160]/10 rounded text-[#07c160] font-medium">v{{ latestVersion
                        }}</span>
                    </div>
                </div>

                <p class="text-xs text-gray-400 mt-2">
                    建议立即更新以体验最新功能和修复。
                </p>
            </div>

            <DialogFooter class="px-6 py-4 bg-[#f7f7f7] border-t gap-4">
                <Button variant="ghost" class="text-gray-500 hover:bg-gray-200" @click="handleOpenChange(false)">
                    以后再说
                </Button>
                <Button class="bg-[#07c160] hover:bg-[#06ae56] text-white" @click="handleDownload">
                    去下载更新
                </Button>
            </DialogFooter>
        </DialogContent>
    </Dialog>
</template>
