<script setup lang="ts">
import type { HTMLAttributes } from 'vue'
import { InputGroupTextarea } from '@/components/ui/input-group'
import { cn } from '@/lib/utils'
import { ref, watch, useAttrs } from 'vue'
import { usePromptInput } from './context'

defineOptions({
  inheritAttrs: false
})

type PromptInputTextareaProps = InstanceType<typeof InputGroupTextarea>['$props']

interface Props extends /* @vue-ignore */ PromptInputTextareaProps {
  class?: HTMLAttributes['class']
}

const props = defineProps<Props>()
const modelValue = defineModel<string>()
const attrs = useAttrs()

const { textInput, setTextInput, submitForm, addFiles, files, removeFile } = usePromptInput()
const isComposing = ref(false)

// Sync with context
watch(() => modelValue.value, (val) => {
  if (val !== undefined && val !== textInput.value) {
    setTextInput(val)
  }
}, { immediate: true })

watch(textInput, (val) => {
  if (val !== modelValue.value) {
    modelValue.value = val
  }
})

function handleKeyDown(e: KeyboardEvent) {
  // First, call parent's keydown handler if provided
  const parentOnKeydown = attrs.onKeydown as ((e: KeyboardEvent) => void) | undefined
  if (parentOnKeydown) {
    parentOnKeydown(e)
  }
  
  // If parent prevented default (e.g., for mention menu navigation), stop here
  if (e.defaultPrevented) {
    return
  }
  
  if (e.key === 'Enter') {
    if (isComposing.value || e.shiftKey)
      return
    e.preventDefault()
    submitForm()
  }

  // Remove last attachment on backspace if input is empty
  if (e.key === 'Backspace' && textInput.value === '' && files.value.length > 0) {
    const lastFile = files.value[files.value.length - 1]
    if (lastFile) {
      removeFile(lastFile.id)
    }
  }
}

function handleInput(e: Event) {
  // Call parent's input handler if provided
  const parentOnInput = attrs.onInput as ((e: Event) => void) | undefined
  if (parentOnInput) {
    parentOnInput(e)
  }
}

function handlePaste(e: ClipboardEvent) {
  const items = e.clipboardData?.items
  if (!items)
    return

  const pastedFiles: File[] = []
  for (const item of Array.from(items)) {
    if (item.kind === 'file') {
      const file = item.getAsFile()
      if (file)
        pastedFiles.push(file)
    }
  }

  if (pastedFiles.length > 0) {
    e.preventDefault()
    addFiles(pastedFiles)
  }
}

// Filter out event handlers from attrs to avoid double binding
const filteredAttrs = Object.fromEntries(
  Object.entries(attrs).filter(([key]) => !key.startsWith('on'))
)
</script>

<template>
  <InputGroupTextarea
    v-model="textInput"
    v-bind="filteredAttrs"
    :placeholder="props.placeholder ?? '输入消息...'"
    name="message"
    :class="cn('field-sizing-content max-h-48 min-h-16', props.class)"
    @keydown="handleKeyDown"
    @input="handleInput"
    @paste="handlePaste"
    @compositionstart="isComposing = true"
    @compositionend="isComposing = false"
  />
</template>
