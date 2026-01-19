<template>
  <div class="debug-view">
    <h1>调试面板</h1>
    <p>详细调试视图（开发中）</p>
    <el-button @click="$router.push('/')">返回控制台</el-button>
  </div>
</template>

<script setup>
</script>

<style lang="scss" scoped>
.debug-view {
  padding: 24px;
  text-align: center;
}
</style>
