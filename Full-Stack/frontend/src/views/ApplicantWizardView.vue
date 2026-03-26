<template>
  <div class="page-container">
    <el-card class="page-surface surface-hover">
      <template #header>
        <div class="header-row">
          <div>
            <strong>Applicant Registration Wizard</strong>
            <p class="muted">Create registration, upload checklist materials, then submit.</p>
          </div>
          <el-button type="primary" :loading="loadingRegistrations" @click="loadRegistrations">Refresh</el-button>
        </div>
      </template>

      <el-steps :active="activeStep" finish-status="success" align-center class="wizard-steps">
        <el-step title="Registration" />
        <el-step title="Materials" />
        <el-step title="Submit" />
      </el-steps>

      <div v-if="activeStep === 0" class="step-panel form-section">
        <el-form label-width="160px" label-position="top" :model="registrationForm">
          <el-form-item label="Title"><el-input v-model="registrationForm.title" /></el-form-item>
          <el-form-item label="Description"><el-input v-model="registrationForm.description" type="textarea" :rows="4" /></el-form-item>
          <el-form-item label="Contact Phone"><el-input v-model="registrationForm.contact_phone" /></el-form-item>
          <el-form-item label="ID Number"><el-input v-model="registrationForm.id_number" /></el-form-item>
          <el-form-item label="Deadline"><el-date-picker v-model="deadlinePicker" type="datetime" value-format="YYYY-MM-DDTHH:mm:ss" /></el-form-item>
          <el-button type="primary" :loading="creatingRegistration" @click="createRegistration">Save Registration</el-button>
          <el-button @click="activeStep = 1" :disabled="!currentRegistrationId">Next</el-button>
        </el-form>
      </div>

      <div v-if="activeStep === 1" class="step-panel">
        <el-alert type="info" :closable="false" :title="`Total upload: ${Math.round(totalUploadSize / 1024 / 1024)} MB / 200 MB`" class="premium-alert" />
        <el-table :data="checklistItems" style="width: 100%; margin-top: 16px" border>
          <el-table-column prop="item_code" label="Code" width="140" />
          <el-table-column prop="item_name" label="Material Item" />
          <el-table-column prop="required" label="Required" width="100">
            <template #default="scope">{{ scope.row.required ? "Yes" : "No" }}</template>
          </el-table-column>
          <el-table-column label="Upload" width="280">
            <template #default="scope">
              <input type="file" :id="`file-${scope.row.id}`" @change="(e) => onFilePicked(e, scope.row.id)" />
              <el-button size="small" type="primary" :loading="uploadingItemId === scope.row.id" @click="upload(scope.row.id)">Upload</el-button>
            </template>
          </el-table-column>
        </el-table>

        <div class="actions">
          <el-button @click="activeStep = 0">Back</el-button>
          <el-button type="primary" @click="activeStep = 2">Next</el-button>
        </div>

        <el-table :data="materialRows" style="width: 100%; margin-top: 24px" empty-text="No uploaded materials yet" border>
          <el-table-column prop="checklist_item_id" label="Checklist Item ID" width="150" />
          <el-table-column label="Versions">
            <template #default="scope">
              <div v-for="v in scope.row.versions" :key="v.material_version_id" class="version-row">
                <el-tag>{{ v.version_number }}</el-tag>
                <span>{{ v.status }}</span>
                <span>{{ v.original_filename }}</span>
              </div>
            </template>
          </el-table-column>
        </el-table>
      </div>

      <div v-if="activeStep === 2" class="step-panel">
        <div class="toolbar-row">
        <el-select v-model="selectedRegistrationId" placeholder="Select registration" class="registration-select">
          <el-option v-for="r in registrations" :key="r.id" :label="`${r.id} - ${r.title} (${r.status})`" :value="r.id" />
        </el-select>
        <el-button type="success" :loading="submittingRegistration" :disabled="!canSubmitSelectedRegistration" @click="submitRegistration">Submit Registration</el-button>
        <span v-if="selectedRegistration" class="muted submit-hint">Current status: {{ selectedRegistration.status }}</span>
        </div>

        <el-divider />
        <el-input v-model="supplementaryReason" placeholder="Supplementary reason" type="textarea" :rows="3" />
        <el-button type="warning" :loading="openingSupplementary" @click="openSupplementary">Open One-Time Supplementary Window</el-button>

        <div class="actions">
          <el-button @click="activeStep = 1">Back</el-button>
        </div>
      </div>
    </el-card>

    <el-card class="page-surface registration-list surface-hover">
      <template #header>My Registrations</template>
      <el-table :data="registrations" style="width: 100%" empty-text="No registrations created yet" border>
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column prop="title" label="Title" />
        <el-table-column prop="status" label="Status" width="180" />
        <el-table-column prop="is_locked" label="Locked" width="100">
          <template #default="scope">{{ scope.row.is_locked ? "Yes" : "No" }}</template>
        </el-table-column>
      </el-table>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from "vue";

import { checklistApi, materialApi, registrationApi } from "../api/endpoints";
import { notifyError, notifySuccess, notifyWarning } from "../utils/notify";

interface RegistrationRow { id: number; title: string; status: string; is_locked: boolean }

const activeStep = ref(0);
const loadingRegistrations = ref(false);
const creatingRegistration = ref(false);
const submittingRegistration = ref(false);
const openingSupplementary = ref(false);
const uploadingItemId = ref<number | null>(null);

const registrations = ref<RegistrationRow[]>([]);
const checklistItems = ref<any[]>([]);
const materialRows = ref<any[]>([]);

const registrationForm = ref({ title: "", description: "", contact_phone: "", id_number: "" });
const deadlinePicker = ref("");
const selectedRegistrationId = ref<number | null>(null);
const currentRegistrationId = ref<number | null>(null);
const supplementaryReason = ref("");
const pickedFiles = ref<Record<number, File | null>>({});

const totalUploadSize = computed(() => materialRows.value.reduce((acc: number, item: any) => acc + item.versions.reduce((sum: number, v: any) => sum + Number(v.file_size_bytes || 0), 0), 0));
const selectedRegistration = computed(() => registrations.value.find((r) => r.id === selectedRegistrationId.value) || null);
const canSubmitSelectedRegistration = computed(() => {
  if (!selectedRegistration.value) return false;
  return ["draft", "supplemented"].includes(selectedRegistration.value.status);
});

const loadRegistrations = async () => {
  loadingRegistrations.value = true;
  try {
    const response = await registrationApi.list();
    registrations.value = response.data.data.items || [];
    if (!selectedRegistrationId.value && registrations.value.length > 0) {
      selectedRegistrationId.value = registrations.value[0].id;
      currentRegistrationId.value = registrations.value[0].id;
      await loadMaterials();
    }
  } catch (error: any) { notifyError(error?.response?.data?.msg || "Failed to load registrations"); }
  finally { loadingRegistrations.value = false; }
};

const loadChecklist = async () => {
  try {
    const response = await checklistApi.list();
    checklistItems.value = (response.data.data.items || []).flatMap((x: any) => x.items || []);
  } catch (error: any) { notifyError(error?.response?.data?.msg || "Failed to load checklist"); }
};

const createRegistration = async () => {
  if (!deadlinePicker.value) { notifyWarning("Please select a deadline"); return; }
  creatingRegistration.value = true;
  try {
    const response = await registrationApi.create({ ...registrationForm.value, deadline_at: new Date(deadlinePicker.value).toISOString() });
    const registration = response.data.data;
    currentRegistrationId.value = registration.id;
    selectedRegistrationId.value = registration.id;
    notifySuccess("Registration created");
    await loadRegistrations();
  } catch (error: any) { notifyError(error?.response?.data?.msg || "Failed to create registration"); }
  finally { creatingRegistration.value = false; }
};

const onFilePicked = (event: Event, itemId: number) => {
  const input = event.target as HTMLInputElement;
  const file = input.files?.[0] || null;
  if (!file) { pickedFiles.value[itemId] = null; return; }
  const ext = file.name.split(".").pop()?.toLowerCase() || "";
  if (!["pdf", "jpg", "jpeg", "png"].includes(ext)) { notifyError("Only PDF/JPG/PNG files are allowed"); pickedFiles.value[itemId] = null; return; }
  if (file.size > 20 * 1024 * 1024) { notifyError("Single file must be <= 20MB"); pickedFiles.value[itemId] = null; return; }
  if (totalUploadSize.value + file.size > 200 * 1024 * 1024) { notifyError("Total upload size cannot exceed 200MB"); pickedFiles.value[itemId] = null; return; }
  pickedFiles.value[itemId] = file;
};

const upload = async (itemId: number) => {
  if (!currentRegistrationId.value) { notifyWarning("Create a registration first"); return; }
  const file = pickedFiles.value[itemId];
  if (!file) { notifyWarning("Please select a file first"); return; }
  uploadingItemId.value = itemId;
  try {
    const formData = new FormData();
    formData.append("registration_id", String(currentRegistrationId.value));
    formData.append("checklist_item_id", String(itemId));
    formData.append("file", file);
    const response = await materialApi.upload(formData);
    response.data?.data?.duplicate_detected ? notifyWarning("Duplicate file fingerprint detected in system") : notifySuccess("Material uploaded");
    await loadMaterials();
  } catch (error: any) { notifyError(error?.response?.data?.msg || "Upload failed"); }
  finally { uploadingItemId.value = null; }
};

const loadMaterials = async () => {
  if (!currentRegistrationId.value) return;
  try {
    const response = await materialApi.list(currentRegistrationId.value);
    materialRows.value = response.data.data.items || [];
  } catch (error: any) { notifyError(error?.response?.data?.msg || "Failed to load materials"); }
};

const submitRegistration = async () => {
  if (!selectedRegistrationId.value) { notifyWarning("Select a registration to submit"); return; }
  if (!canSubmitSelectedRegistration.value) {
    notifyWarning("Only registrations in draft or supplemented status can be submitted");
    return;
  }
  submittingRegistration.value = true;
  try {
    await registrationApi.submit(selectedRegistrationId.value);
    notifySuccess("Registration submitted");
    await loadRegistrations();
  } catch (error: any) { notifyError(error?.response?.data?.msg || "Submit failed"); }
  finally { submittingRegistration.value = false; }
};

const openSupplementary = async () => {
  if (!selectedRegistrationId.value) { notifyWarning("Select a registration first"); return; }
  if (!supplementaryReason.value.trim()) { notifyWarning("Please provide reason"); return; }
  openingSupplementary.value = true;
  try {
    await registrationApi.supplementary(selectedRegistrationId.value, supplementaryReason.value);
    notifySuccess("Supplementary window opened");
  } catch (error: any) { notifyError(error?.response?.data?.msg || "Failed to open supplementary window"); }
  finally { openingSupplementary.value = false; }
};

onMounted(async () => { await Promise.all([loadChecklist(), loadRegistrations()]); });
</script>

<style scoped>
.header-row { display: flex; justify-content: space-between; align-items: center; gap: 12px; }
.step-panel { margin-top: 24px; }
.actions { margin-top: 16px; display: flex; gap: 10px; }
.version-row { display: flex; gap: 8px; align-items: center; margin-bottom: 6px; }
.registration-list { margin-top: 18px; }
.form-section :deep(.el-form-item__label) {
  font-weight: 600;
}
.wizard-steps {
  margin-top: 6px;
  padding: 8px 4px;
  background: #f8faff;
  border: 1px solid #dfe5f2;
  border-radius: 12px;
}
.premium-alert {
  border-radius: 12px;
}
.registration-select {
  width: 320px;
}
.submit-hint {
  font-size: 0.85rem;
}
@media (max-width: 760px) {
  .header-row {
    flex-direction: column;
    align-items: flex-start;
  }
  .registration-select {
    width: 100%;
  }
}
</style>
