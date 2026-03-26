<template>
  <div class="page-container">
    <el-card class="page-surface surface-hover admin-hero" style="margin-bottom: 14px">
      <h2 style="margin: 0">Admin Control Center</h2>
      <p class="muted" style="margin-top: 6px">Backup, recovery, policy management, alerts, and exports.</p>
    </el-card>

    <el-row :gutter="16">
      <el-col :md="12" :xs="24">
        <el-card class="page-surface surface-hover">
          <template #header>Backup & Recovery</template>
          <div class="toolbar-row">
            <el-button type="primary" :loading="backupCreating" @click="createBackup">Create Backup</el-button>
            <el-button :loading="backupLoading" @click="loadBackups">Refresh</el-button>
          </div>
          <el-table :data="backups" style="width: 100%; margin-top: 12px" border empty-text="No backups created yet">
            <el-table-column prop="id" label="ID" width="70" />
            <el-table-column prop="backup_type" label="Type" width="90" />
            <el-table-column prop="status" label="Status" width="110" />
            <el-table-column label="Recover" width="120">
              <template #default="scope">
                <el-button size="small" type="danger" @click="recoverBackup(scope.row.id)">Recover</el-button>
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>

      <el-col :md="12" :xs="24">
        <el-card class="page-surface surface-hover">
          <template #header>Whitelist Policy</template>
          <el-form label-width="120px" label-position="top">
            <el-form-item label="Policy Name"><el-input v-model="policyForm.policy_name" /></el-form-item>
            <el-form-item label="Scope Rule"><el-input v-model="policyForm.scope_rule" type="textarea" :rows="3" /></el-form-item>
            <el-button type="primary" :loading="policySaving" @click="createPolicy">Save Policy</el-button>
          </el-form>
          <el-divider />
          <el-button :loading="loadingSettings" @click="loadSettings">Refresh Settings</el-button>
          <pre class="settings-block">{{ JSON.stringify(settingsData, null, 2) }}</pre>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="page-surface surface-hover" style="margin-top: 16px">
      <template #header>Alerts and Metrics</template>
      <el-button type="primary" :loading="recomputeLoading" @click="recomputeMetrics">Recompute Metrics</el-button>
      <el-button style="margin-left: 8px" :loading="loadingAlerts" @click="loadAlerts">Refresh Alerts</el-button>
      <el-table :data="alerts" style="width: 100%; margin-top: 12px" border empty-text="No active alerts">
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="alert_type" label="Type" width="180" />
        <el-table-column prop="severity" label="Severity" width="120" />
        <el-table-column prop="message" label="Message" />
        <el-table-column prop="is_resolved" label="Resolved" width="100">
          <template #default="scope">{{ scope.row.is_resolved ? "Yes" : "No" }}</template>
        </el-table-column>
        <el-table-column label="Action" width="110">
          <template #default="scope">
            <el-button size="small" @click="resolveAlert(scope.row.id)" :disabled="scope.row.is_resolved">Resolve</el-button>
          </template>
        </el-table-column>
      </el-table>
    </el-card>

    <el-card class="page-surface surface-hover" style="margin-top: 16px">
      <template #header>Exports</template>
      <el-space wrap>
        <el-button :loading="exportingType === 'reconciliation'" @click="exportReport('reconciliation')">Reconciliation CSV</el-button>
        <el-button :loading="exportingType === 'audit'" @click="exportReport('audit')">Audit CSV</el-button>
        <el-button :loading="exportingType === 'compliance'" @click="exportReport('compliance')">Compliance CSV</el-button>
        <el-button :loading="exportingType === 'whitelist'" @click="exportReport('whitelist')">Whitelist CSV</el-button>
      </el-space>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import { alertsApi, backupApi, metricsApi, reportsApi } from "../api/endpoints";
import { http } from "../api/http";
import { notifyError, notifySuccess } from "../utils/notify";

const backupCreating = ref(false);
const backupLoading = ref(false);
const loadingAlerts = ref(false);
const recomputeLoading = ref(false);
const policySaving = ref(false);
const loadingSettings = ref(false);
const exportingType = ref("");

const backups = ref<any[]>([]);
const alerts = ref<any[]>([]);
const settingsData = ref<any>({});

const policyForm = ref({ policy_name: "", scope_rule: "" });

const loadBackups = async () => {
  backupLoading.value = true;
  try {
    const response = await backupApi.list();
    backups.value = response.data.data.items || [];
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to load backups");
  } finally {
    backupLoading.value = false;
  }
};

const createBackup = async () => {
  backupCreating.value = true;
  try {
    await backupApi.create();
    notifySuccess("Backup created");
    await loadBackups();
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to create backup");
  } finally {
    backupCreating.value = false;
  }
};

const recoverBackup = async (backupId: number) => {
  try {
    await backupApi.recover(backupId);
    notifySuccess("Recovery completed");
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Recovery failed");
  }
};

const loadAlerts = async () => {
  loadingAlerts.value = true;
  try {
    const response = await alertsApi.list();
    alerts.value = response.data.data.items || [];
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to load alerts");
  } finally {
    loadingAlerts.value = false;
  }
};

const resolveAlert = async (id: number) => {
  try {
    await alertsApi.resolve(id);
    notifySuccess("Alert resolved");
    await loadAlerts();
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to resolve alert");
  }
};

const recomputeMetrics = async () => {
  recomputeLoading.value = true;
  try {
    await metricsApi.recompute();
    notifySuccess("Metrics recomputed");
    await loadAlerts();
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Metrics recompute failed");
  } finally {
    recomputeLoading.value = false;
  }
};

const loadSettings = async () => {
  loadingSettings.value = true;
  try {
    const response = await http.get("/api/admin/settings");
    settingsData.value = response.data.data || {};
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to load settings");
  } finally {
    loadingSettings.value = false;
  }
};

const createPolicy = async () => {
  policySaving.value = true;
  try {
    await http.post("/api/admin/whitelist-policies", null, { params: policyForm.value });
    notifySuccess("Whitelist policy created");
    await loadSettings();
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to create policy");
  } finally {
    policySaving.value = false;
  }
};

const exportReport = async (type: string) => {
  exportingType.value = type;
  try {
    if (type === "reconciliation") await reportsApi.reconciliation();
    if (type === "audit") await reportsApi.audit();
    if (type === "compliance") await reportsApi.compliance();
    if (type === "whitelist") await reportsApi.whitelist();
    notifySuccess(`${type} report exported`);
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Export failed");
  } finally {
    exportingType.value = "";
  }
};

onMounted(async () => {
  await Promise.all([loadBackups(), loadAlerts(), loadSettings()]);
});
</script>

<style scoped>
.settings-block {
  margin-top: 10px;
  background: #f7f8fa;
  border: 1px solid #e5e7eb;
  border-radius: 8px;
  padding: 10px;
}
.admin-hero {
  background: linear-gradient(135deg, #ffffff 0%, #f6f8ff 52%, #eef7ff 100%);
}
@media (max-width: 768px) {
  :deep(.el-row .el-col) {
    margin-bottom: 12px;
  }
}
</style>
