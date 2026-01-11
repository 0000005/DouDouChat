<script setup lang="ts">
import { ref, watch, computed } from 'vue'
import { useFriendStore } from '@/stores/friend'
import { useSessionStore } from '@/stores/session'
import { UserPlus, Camera } from 'lucide-vue-next'
import { getStaticUrl } from '@/api/base'
import AvatarUploader from '@/components/common/AvatarUploader.vue'
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogDescription,
  DialogFooter,
} from '@/components/ui/dialog'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Textarea } from '@/components/ui/textarea'
import { Switch } from '@/components/ui/switch'
import { Label } from '@/components/ui/label'

const props = defineProps<{
  open: boolean
  mode: 'add' | 'edit'
  friendId?: number | null
}>()

const emit = defineEmits<{
  (e: 'update:open', val: boolean): void
  (e: 'success', friend: any): void
}>()

const friendStore = useFriendStore()
const sessionStore = useSessionStore()

const isSubmitting = ref(false)
const isAvatarUploaderOpen = ref(false)

const form = ref({
  name: '',
  description: '',
  system_prompt: '',
  avatar: '',
  script_expression: true,
})

const isOpen = computed({
  get: () => props.open,
  set: (val) => emit('update:open', val)
})

const resetForm = () => {
  form.value = {
    name: '',
    description: '',
    system_prompt: '',
    avatar: '',
    script_expression: true,
  }
}

const loadFriendData = () => {
  if (props.mode === 'edit' && props.friendId) {
    const friend = friendStore.getFriend(props.friendId)
    if (friend) {
      form.value = {
        name: friend.name,
        description: friend.description || '',
        system_prompt: friend.system_prompt || '',
        avatar: friend.avatar || '',
        script_expression: friend.script_expression ?? true,
      }
    }
  } else {
    resetForm()
  }
}

watch(() => props.open, (newVal) => {
  if (newVal) {
    loadFriendData()
  }
})

const handleAvatarUploaded = (url: string) => {
  form.value.avatar = url
}

const isFormValid = computed(() => {
  return form.value.name.trim() && 
         form.value.description.trim() && 
         form.value.system_prompt.trim()
})

const handleConfirm = async () => {
  if (!isFormValid.value) return

  isSubmitting.value = true
  try {
    if (props.mode === 'add') {
      const createdFriend = await friendStore.addFriend({
        name: form.value.name.trim(),
        description: form.value.description.trim() || undefined,
        system_prompt: form.value.system_prompt.trim() || undefined,
        is_preset: false,
        avatar: form.value.avatar || undefined,
        script_expression: form.value.script_expression
      })
      emit('success', createdFriend)
      sessionStore.selectFriend(createdFriend.id)
    } else if (props.mode === 'edit' && props.friendId) {
      const updatedFriend = await friendStore.updateFriend(props.friendId, {
        name: form.value.name.trim(),
        description: form.value.description.trim() || null,
        system_prompt: form.value.system_prompt.trim() || null,
        avatar: form.value.avatar || null,
        script_expression: form.value.script_expression
      })
      emit('success', updatedFriend)
    }
    isOpen.value = false
  } catch (e) {
    console.error(`Failed to ${props.mode} friend:`, e)
  } finally {
    isSubmitting.value = false
  }
}
</script>
<template>
  <Dialog v-model:open="isOpen">
    <DialogContent class="sm:max-w-[500px] friend-compose-dialog">
      <DialogHeader>
        <DialogTitle>{{ mode === 'add' ? '新增好友' : '编辑好友' }}</DialogTitle>
        <DialogDescription>
          {{ mode === 'add' ? '创建一个新的 AI 好友，设置其名称和人格特征。' : '修改 AI 好友的名称和人格特征。' }}
        </DialogDescription>
      </DialogHeader>

      <!-- Avatar Upload Section -->
      <div class="flex flex-col items-center py-4 shrink-0">
        <div class="relative group cursor-pointer" @click="isAvatarUploaderOpen = true">
          <div
            class="w-20 h-20 rounded-lg border border-gray-200 shadow-sm bg-gray-50 flex items-center justify-center overflow-hidden">
            <img v-if="form.avatar" :src="getStaticUrl(form.avatar)" class="w-full h-full object-cover" />
            <UserPlus v-else class="text-gray-300 w-8 h-8" />
          </div>
          <div
            class="absolute inset-0 bg-black/40 rounded-lg opacity-0 group-hover:opacity-100 flex items-center justify-center transition-opacity backdrop-blur-[1px]">
            <Camera class="text-white w-6 h-6" stroke-width="1.5" />
          </div>
        </div>
        <div class="mt-2 text-xs text-gray-500">{{ mode === 'add' ? '点击设置头像' : '点击更换头像' }}</div>
      </div>

      <div class="dialog-form">
        <div class="form-group">
          <label for="friend-name" class="form-label">好友名称 <span class="required">*</span></label>
          <Input id="friend-name" v-model="form.name" :placeholder="mode === 'add' ? '请输入好友名称，如：小助手、知心姐姐' : '请输入好友名称'"
            class="form-input" />
        </div>

        <div class="form-group">
          <label for="friend-description" class="form-label">好友描述 <span class="required">*</span></label>
          <Input id="friend-description" v-model="form.description" placeholder="简短描述这个好友的特点" class="form-input" />
        </div>

        <div class="form-group">
          <label for="friend-system-prompt" class="form-label">系统提示词 <span class="required">*</span></label>
          <Textarea id="friend-system-prompt" v-model="form.system_prompt"
            placeholder="设置这个好友的人格特征和行为准则，例如：你是一个温暖友善的朋友，喜欢倾听和给出建设性意见..." class="form-textarea" :rows="5" />
          <p class="form-hint">系统提示词决定了 AI 好友的人格和回复风格</p>
        </div>

        <div class="flex items-center justify-between p-3 bg-gray-50 rounded-lg border border-gray-100 mt-2">
          <div class="space-y-0.5">
            <Label for="script-expression" class="text-sm font-medium">剧本式表达</Label>
            <p class="text-[11px] text-gray-500">让 AI 的回复包含动作、神态等环境描写</p>
          </div>
          <Switch id="script-expression" v-model="form.script_expression" />
        </div>
      </div>

      <DialogFooter>
        <Button variant="outline" @click="isOpen = false" :disabled="isSubmitting">取消</Button>
        <Button @click="handleConfirm" :disabled="!isFormValid || isSubmitting" class="confirm-btn">
          {{ isSubmitting ? (mode === 'add' ? '创建中...' : '保存中...') : (mode === 'add' ? '创建好友' : '保存修改') }}
        </Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>

  <!-- Avatar Uploader -->
  <AvatarUploader v-if="isAvatarUploaderOpen" :title="mode === 'add' ? '设置好友头像' : '更换好友头像'"
    :initial-image="form.avatar ? getStaticUrl(form.avatar) : undefined" @update:image="handleAvatarUploaded"
    @close="isAvatarUploaderOpen = false" />
</template>

<style scoped>
.dialog-form {
  display: flex;
  flex-direction: column;
  gap: 16px;
  padding: 8px 0;
}

.form-group {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.form-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.form-label .required {
  color: #dc2626;
}

.form-input {
  font-size: 14px;
}

.form-textarea {
  font-size: 14px;
  resize: none;
  min-height: 100px;
}

.form-hint {
  font-size: 12px;
  color: #888;
  margin: 0;
}

.confirm-btn {
  background: #07c160;
}

.confirm-btn:hover:not(:disabled) {
  background: #06ad56;
}

.confirm-btn:disabled {
  background: #a0a0a0;
  cursor: not-allowed;
}
</style>
