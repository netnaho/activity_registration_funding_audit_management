<template>
  <div class="page-container">
    <el-card class="page-surface surface-hover finance-hero" style="margin-bottom: 14px">
      <h2 style="margin: 0">Finance Management</h2>
      <p class="muted" style="margin-top: 6px">Manage budgets, transactions, invoice records, and overspending controls.</p>
    </el-card>

    <el-row :gutter="16">
      <el-col :md="12" :xs="24">
        <el-card class="page-surface surface-hover">
          <template #header>Create Funding Account</template>
          <el-form label-width="120px" label-position="top">
            <el-form-item label="Name"><el-input v-model="accountForm.account_name" /></el-form-item>
            <el-form-item label="Category"><el-input v-model="accountForm.category" /></el-form-item>
            <el-form-item label="Period"><el-input v-model="accountForm.period" /></el-form-item>
            <el-form-item label="Budget"><el-input-number v-model="accountForm.budget_amount" :min="1" /></el-form-item>
            <el-button type="primary" :loading="creatingAccount" @click="createAccount">Create</el-button>
          </el-form>
        </el-card>
      </el-col>
      <el-col :md="12" :xs="24">
        <el-card class="page-surface surface-hover">
          <template #header>Create Transaction</template>
          <el-form label-width="140px" label-position="top">
            <el-form-item label="Account">
              <el-select v-model="txForm.funding_account_id" style="width: 100%">
                <el-option v-for="a in accounts" :key="a.id" :label="`${a.account_name} (${a.budget_amount})`" :value="a.id" />
              </el-select>
            </el-form-item>
            <el-form-item label="Type">
              <el-select v-model="txForm.transaction_type" style="width: 100%">
                <el-option label="income" value="income" />
                <el-option label="expense" value="expense" />
              </el-select>
            </el-form-item>
            <el-form-item label="Amount"><el-input-number v-model="txForm.amount" :min="1" /></el-form-item>
            <el-form-item label="Category"><el-input v-model="txForm.category" /></el-form-item>
            <el-form-item label="Time"><el-date-picker v-model="txTimePicker" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" /></el-form-item>
            <el-form-item label="Note"><el-input v-model="txForm.note" /></el-form-item>
            <el-form-item label="Invoice"><input type="file" @change="onInvoicePicked" /></el-form-item>
            <el-button type="primary" :loading="creatingTx" @click="createTransaction">Save Transaction</el-button>
          </el-form>
        </el-card>
      </el-col>
    </el-row>

    <el-card class="page-surface surface-hover" style="margin-top: 16px">
      <template #header>Finance Overview</template>
      <el-button :loading="loadingOverview" @click="loadOverview">Refresh</el-button>
      <el-table :data="accounts" style="width: 100%; margin-top: 12px" border empty-text="No funding accounts yet">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="account_name" label="Account" />
        <el-table-column prop="category" label="Category" />
        <el-table-column prop="period" label="Period" />
        <el-table-column prop="budget_amount" label="Budget" />
      </el-table>
    </el-card>

    <el-card class="page-surface surface-hover" style="margin-top: 16px">
      <template #header>Finance Statistics</template>
      <el-button :loading="loadingStats" @click="loadStats">Compute Stats</el-button>
      <pre class="stats-block">{{ JSON.stringify(stats, null, 2) }}</pre>
    </el-card>

    <el-dialog v-model="overspendDialogVisible" title="Overspending Warning" width="520px">
      <p>Expenses exceed budget by more than 10%. Secondary confirmation is required to proceed.</p>
      <template #footer>
        <el-button @click="overspendDialogVisible = false">Cancel</el-button>
        <el-button type="danger" @click="confirmOverspend">Confirm and Proceed</el-button>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from "vue";

import { financeApi } from "../api/endpoints";
import { notifyError, notifySuccess, notifyWarning } from "../utils/notify";

const loadingOverview = ref(false);
const creatingAccount = ref(false);
const creatingTx = ref(false);
const loadingStats = ref(false);

const accounts = ref<any[]>([]);
const stats = ref<any>({});

const accountForm = ref({ account_name: "", category: "", period: "", budget_amount: 1000 });
const txForm = ref({ funding_account_id: undefined as number | undefined, transaction_type: "expense", amount: 1, category: "operations", note: "" });
const txTimePicker = ref("");
const invoiceFile = ref<File | null>(null);
const overspendDialogVisible = ref(false);
const pendingTxFormData = ref<FormData | null>(null);

const loadOverview = async () => {
  loadingOverview.value = true;
  try {
    const response = await financeApi.overview();
    accounts.value = response.data.data.accounts || [];
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to load finance overview");
  } finally {
    loadingOverview.value = false;
  }
};

const createAccount = async () => {
  creatingAccount.value = true;
  try {
    await financeApi.createAccount(accountForm.value);
    notifySuccess("Funding account created");
    await loadOverview();
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to create account");
  } finally {
    creatingAccount.value = false;
  }
};

const onInvoicePicked = (event: Event) => {
  const input = event.target as HTMLInputElement;
  invoiceFile.value = input.files?.[0] || null;
};

const buildTxFormData = (overspendConfirmed: boolean) => {
  const formData = new FormData();
  formData.append("funding_account_id", String(txForm.value.funding_account_id || ""));
  formData.append("transaction_type", txForm.value.transaction_type);
  formData.append("amount", String(txForm.value.amount));
  formData.append("transaction_time", new Date(txTimePicker.value).toISOString());
  formData.append("category", txForm.value.category);
  formData.append("note", txForm.value.note || "");
  formData.append("overspend_confirmed", String(overspendConfirmed));
  if (invoiceFile.value) formData.append("invoice_file", invoiceFile.value);
  return formData;
};

const createTransaction = async () => {
  if (!txForm.value.funding_account_id) { notifyWarning("Please select account"); return; }
  if (!txTimePicker.value) { notifyWarning("Please pick transaction time"); return; }
  creatingTx.value = true;
  try {
    await financeApi.createTransaction(buildTxFormData(false));
    notifySuccess("Transaction saved");
  } catch (error: any) {
    if (error?.response?.status === 409) {
      pendingTxFormData.value = buildTxFormData(true);
      overspendDialogVisible.value = true;
      notifyWarning("Overspending warning triggered");
    } else {
      notifyError(error?.response?.data?.msg || "Failed to save transaction");
    }
  } finally {
    creatingTx.value = false;
  }
};

const confirmOverspend = async () => {
  if (!pendingTxFormData.value) { overspendDialogVisible.value = false; return; }
  creatingTx.value = true;
  try {
    await financeApi.createTransaction(pendingTxFormData.value);
    notifySuccess("Transaction saved with overspend confirmation");
    overspendDialogVisible.value = false;
    pendingTxFormData.value = null;
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to confirm overspending transaction");
  } finally {
    creatingTx.value = false;
  }
};

const loadStats = async () => {
  loadingStats.value = true;
  try {
    const response = await financeApi.stats({});
    stats.value = response.data.data || {};
  } catch (error: any) {
    notifyError(error?.response?.data?.msg || "Failed to load statistics");
  } finally {
    loadingStats.value = false;
  }
};

onMounted(loadOverview);
</script>

<style scoped>
.stats-block { margin-top: 12px; background: #f7f8fa; border: 1px solid #e5e7eb; border-radius: 8px; padding: 12px; }
.finance-hero {
  background: linear-gradient(135deg, #ffffff 0%, #f5f9ff 58%, #edf9f2 100%);
}
 :deep(.el-input-number) {
  width: 100%;
 }
@media (max-width: 768px) {
  :deep(.el-row .el-col) {
    margin-bottom: 12px;
  }
}
</style>
