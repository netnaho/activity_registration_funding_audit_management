<template>
  <div class="page-header">
    <div>
      <h2 class="title">{{ title }}</h2>
      <p v-if="subtitle" class="subtitle">{{ subtitle }}</p>
    </div>
    <div class="actions">
      <slot />
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string; subtitle?: string }>();
</script>

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 12px;
  margin-bottom: 14px;
  flex-wrap: wrap;
}
.title {
  margin: 0;
  font-size: 1.35rem;
  letter-spacing: 0.1px;
}
.subtitle {
  margin: 6px 0 0;
  color: #5a6680;
}
.actions {
  display: flex;
  gap: 8px;
  flex-wrap: wrap;
}
</style>
