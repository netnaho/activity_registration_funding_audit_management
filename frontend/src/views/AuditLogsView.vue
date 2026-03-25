<template>
  <div class="page-container">
    <el-card class="page-surface surface-hover">
      <template #header>
        <div class="header-row">
          <div>
            <strong>Audit Logs</strong>
            <p class="muted">Trace security and business-sensitive operations.</p>
          </div>
          <div class="toolbar-row">
            <el-input v-model="keyword" placeholder="Filter action/target" class="search-input" clearable />
            <el-button type="primary" :loading="loading" @click="loadLogs">Refresh</el-button>
          </div>
        </div>
      </template>

      <el-table :data="filteredLogs" style="width: 100%" empty-text="No audit logs available" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="action" label="Action" width="220" />
        <el-table-column prop="target_type" label="Target Type" width="160" />
        <el-table-column prop="target_id" label="Target ID" width="140" />
        <el-table-column prop="created_at" label="Created At" />
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { http } from "../api/http";
import { notifyError } from "../utils/notify";

const loading = ref(false);
const logs = ref<any[]>([]);
const keyword = ref("");

const filteredLogs = computed(() => {
  const key = keyword.value.trim().toLowerCase();
  if (!key) return logs.value;
  return logs.value.filter((log) => `${log.action} ${log.target_type} ${log.target_id}`.toLowerCase().includes(key));
});

const loadLogs = async () => {
  loading.value = true;
  try {
    const response = await http.get("/api/audit/logs");
    logs.value = response.data.data.items || [];
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to load audit logs");
  } finally {
    loading.value = false;
  }
};

onMounted(loadLogs);
</script>

<style scoped>
.header-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.search-input {
  width: 260px;
}
@media (max-width: 760px) {
  .header-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .search-input {
    width: 100%;
  }
}
</style>
