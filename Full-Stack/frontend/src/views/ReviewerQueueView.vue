<template>
  <div class="page-container">
    <el-card class="page-surface surface-hover">
      <template #header>
        <div class="header-row">
          <div>
            <strong>Reviewer Queue</strong>
            <p class="muted">Filter applications, apply transitions, and review timeline.</p>
          </div>
          <el-button type="primary" :loading="loading" @click="loadQueue">Refresh</el-button>
        </div>
      </template>

      <div class="toolbar-row toolbar">
        <el-select v-model="filters.status" placeholder="Status" clearable class="control-lg">
          <el-option label="submitted" value="submitted" />
          <el-option label="supplemented" value="supplemented" />
          <el-option label="approved" value="approved" />
          <el-option label="rejected" value="rejected" />
          <el-option label="canceled" value="canceled" />
          <el-option label="promoted_from_waitlist" value="promoted_from_waitlist" />
        </el-select>
        <el-input v-model="filters.keyword" placeholder="Search title" class="control-xl" />
        <el-button type="primary" @click="loadQueue">Search</el-button>
      </div>

      <el-table :data="queueRows" @selection-change="onSelectionChange" style="width: 100%" empty-text="No queue items found" border>
        <el-table-column type="selection" width="50" />
        <el-table-column prop="id" label="ID" width="90" />
        <el-table-column prop="title" label="Title" />
        <el-table-column prop="status" label="Status" width="220" />
        <el-table-column prop="deadline_at" label="Deadline" width="220" />
        <el-table-column label="Actions" width="420">
          <template #default="scope">
            <el-button size="small" type="success" @click="singleTransition(scope.row.id, 'approved')">Approve</el-button>
            <el-button size="small" type="danger" @click="singleTransition(scope.row.id, 'rejected')">Reject</el-button>
            <el-button size="small" type="warning" @click="singleTransition(scope.row.id, 'supplemented')">Request Correction</el-button>
            <el-button size="small" @click="loadHistory(scope.row.id)">History</el-button>
          </template>
        </el-table-column>
      </el-table>

      <div class="toolbar-row batch-panel" :class="{ stacked: isCompact }">
        <el-input v-model="batchComment" placeholder="Batch review comment" class="control-xl" />
        <el-select v-model="batchTargetStatus" class="control-lg">
          <el-option label="approved" value="approved" />
          <el-option label="rejected" value="rejected" />
          <el-option label="supplemented" value="supplemented" />
          <el-option label="canceled" value="canceled" />
          <el-option label="promoted_from_waitlist" value="promoted_from_waitlist" />
        </el-select>
        <el-button type="primary" :loading="batchLoading" @click="applyBatch">Batch Apply (max 50)</el-button>
      </div>

      <el-pagination
        class="queue-pagination"
        background
        layout="prev, pager, next"
        :current-page="filters.page"
        :page-size="filters.page_size"
        :total="Math.max(filters.page * filters.page_size, queueRows.length + (filters.page - 1) * filters.page_size)"
        @current-change="onPageChange"
      />

      <el-drawer v-model="historyVisible" title="Workflow Timeline" size="min(720px, 92%)">
        <el-timeline>
          <el-timeline-item v-for="item in workflowHistory" :key="item.id" :timestamp="item.created_at">
            <strong>{{ item.from_status }} -> {{ item.to_status }}</strong>
            <div>{{ item.comment }}</div>
            <div>Reviewer: {{ item.reviewer_id }} | Batch: {{ item.batch_ref || '-' }}</div>
          </el-timeline-item>
        </el-timeline>
      </el-drawer>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";
import { workflowApi } from "../api/endpoints";
import { notifyError, notifySuccess, notifyWarning } from "../utils/notify";

const loading = ref(false);
const batchLoading = ref(false);
const queueRows = ref<any[]>([]);
const selectedRows = ref<any[]>([]);
const filters = ref({ status: "", keyword: "", page: 1, page_size: 20 });
const batchComment = ref("Batch review action");
const batchTargetStatus = ref("approved");

const historyVisible = ref(false);
const workflowHistory = ref<any[]>([]);
const isCompact = window.matchMedia("(max-width: 900px)").matches;

const loadQueue = async () => {
  loading.value = true;
  try {
    const response = await workflowApi.queue(filters.value);
    queueRows.value = response.data.data.items || [];
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to load reviewer queue");
  } finally {
    loading.value = false;
  }
};

const onPageChange = async (page: number) => {
  filters.value.page = page;
  await loadQueue();
};

const onSelectionChange = (rows: any[]) => {
  selectedRows.value = rows;
};

const singleTransition = async (registrationId: number, targetStatus: string) => {
  try {
    await workflowApi.transition({ registration_id: registrationId, target_status: targetStatus, comment: `Reviewer set ${targetStatus}` });
    notifySuccess("Transition applied");
    await loadQueue();
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Transition failed");
  }
};

const applyBatch = async () => {
  if (selectedRows.value.length === 0) {
    notifyWarning("Select at least one registration");
    return;
  }
  if (selectedRows.value.length > 50) {
    notifyError("Batch limit is 50");
    return;
  }
  batchLoading.value = true;
  try {
    await workflowApi.batchTransition({
      registration_ids: selectedRows.value.map((r) => r.id),
      target_status: batchTargetStatus.value,
      comment: batchComment.value,
    });
    notifySuccess("Batch transition applied");
    await loadQueue();
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Batch transition failed");
  } finally {
    batchLoading.value = false;
  }
};

const loadHistory = async (registrationId: number) => {
  try {
    const response = await workflowApi.history(registrationId);
    workflowHistory.value = response.data.data.items || [];
    historyVisible.value = true;
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to load workflow history");
  }
};

onMounted(loadQueue);
</script>

<style scoped>
.header-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.toolbar { display: flex; gap: 10px; margin-bottom: 16px; }
.batch-panel { margin-top: 16px; display: flex; gap: 10px; align-items: center; }
.queue-pagination {
  margin-top: 16px;
  justify-content: flex-end;
}
.control-lg {
  width: 220px;
}
.control-xl {
  width: 340px;
}
.batch-panel.stacked {
  align-items: stretch;
}
.batch-panel.stacked > * {
  width: 100%;
}
@media (max-width: 900px) {
  .header-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .control-lg,
  .control-xl,
  .queue-pagination {
    width: 100%;
    justify-content: flex-start;
  }
}
</style>
