<template>
  <div class="chat-input">
    <el-input
      v-model="inputValue"
      type="textarea"
      :rows="1"
      :autosize="{ minRows: 1, maxRows: 4 }"
      placeholder="输入您的问题..."
      :disabled="disabled"
      @keydown.enter.exact.prevent="handleSend"
      @keydown.enter.shift.exact="handleNewLine"
    />
    <el-button
      type="primary"
      :icon="Promotion"
      :disabled="!canSend"
      :loading="disabled"
      @click="handleSend"
    >
      发送
    </el-button>
  </div>
</template>

<script setup>
import { ref, computed } from 'vue'
import { Promotion } from '@element-plus/icons-vue'

const props = defineProps({
  disabled: {
    type: Boolean,
    default: false,
  },
})

const emit = defineEmits(['send'])

const inputValue = ref('')

const canSend = computed(() => {
  return inputValue.value.trim().length > 0 && !props.disabled
})

function handleSend() {
  if (!canSend.value) return
  emit('send', inputValue.value.trim())
  inputValue.value = ''
}

function handleNewLine() {
  inputValue.value += '\n'
}
</script>

<style lang="scss" scoped>
.chat-input {
  display: flex;
  gap: 12px;
  align-items: flex-end;
  
  :deep(.el-textarea) {
    flex: 1;
    
    .el-textarea__inner {
      padding: 12px 16px;
      border-radius: 12px;
      resize: none;
      font-size: 14px;
      line-height: 1.5;
      
      &:focus {
        box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
      }
    }
  }
  
  .el-button {
    height: 44px;
    padding: 0 20px;
    border-radius: 12px;
  }
}
</style>
