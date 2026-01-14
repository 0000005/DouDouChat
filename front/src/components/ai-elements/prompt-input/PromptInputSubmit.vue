<script setup lang="ts">
// import type { InputGroupButtonVariants } from '@/components/ui/input-group'
import type { ChatStatus } from 'ai'
import type { HTMLAttributes } from 'vue'
import { InputGroupButton } from '@/components/ui/input-group'
import { cn } from '@/lib/utils'
import { CornerDownLeftIcon, Loader2Icon, XIcon } from 'lucide-vue-next'
import { computed } from 'vue'

type InputGroupButtonProps = InstanceType<typeof InputGroupButton>['$props']

interface Props extends /* @vue-ignore */ InputGroupButtonProps {
  class?: HTMLAttributes['class']
  status?: ChatStatus
  variant?: InputGroupButtonProps['variant']
  size?: InputGroupButtonProps['size']
  disabled?: boolean
}

const props = withDefaults(defineProps<Props>(), {
  variant: 'default',
  size: 'icon-sm',
  disabled: false,
})

const icon = computed(() => {
  if (props.status === 'submitted' || props.status === 'streaming') {
    return Loader2Icon
  }
  else if (props.status === 'error') {
    return XIcon
  }
  return CornerDownLeftIcon
})

const iconClass = computed(() => {
  if (props.status === 'submitted' || props.status === 'streaming') {
    return 'size-4 animate-spin'
  }
  return 'size-4'
})

const isDisabled = computed(() => {
  return props.disabled || props.status === 'streaming' || props.status === 'submitted'
})

const { status, size, variant, disabled, class: _, ...restProps } = props
</script>

<template>
  <InputGroupButton aria-label="Submit" :class="cn(props.class)" :size="size" :variant="variant" type="submit"
    :disabled="isDisabled" v-bind="restProps">
    <slot>
      <component :is="icon" :class="iconClass" />
    </slot>
  </InputGroupButton>
</template>
