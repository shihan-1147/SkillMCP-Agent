<template>
  <el-config-provider :locale="zhCn">
    <div class="app-container" :class="{ 'dark-mode': isDark }">
      <router-view />
    </div>
  </el-config-provider>
</template>

<script setup>
import { ref } from 'vue'
import zhCn from 'element-plus/dist/locale/zh-cn.mjs'

const isDark = ref(false)
</script>

<style lang="scss">
.app-container {
  width: 100%;
  height: 100vh;
  background: var(--bg-color);
}
</style>
