<template>
  <div class="page-container">
    <el-card class="page-surface hero surface-hover">
      <div class="hero-grid">
        <div>
          <p class="eyebrow">Operations Center</p>
          <h1 class="dashboard-title">Executive Dashboard</h1>
          <p class="muted">Role-based workspace for the Activity Registration and Funding Audit Management Platform.</p>
          <el-space wrap class="quick-actions">
            <el-button v-if="role === 'applicant' || role === 'system_admin'" type="primary" @click="$router.push('/applicant/wizard')">Applicant Wizard</el-button>
            <el-button v-if="role === 'reviewer' || role === 'system_admin'" @click="$router.push('/reviewer/queue')">Reviewer Queue</el-button>
            <el-button v-if="role === 'financial_admin' || role === 'system_admin'" @click="$router.push('/finance/management')">Finance Management</el-button>
            <el-button v-if="role === 'system_admin'" @click="$router.push('/admin/settings')">Admin Settings</el-button>
            <el-button v-if="role === 'reviewer' || role === 'system_admin'" @click="$router.push('/audit/logs')">Audit Logs</el-button>
          </el-space>
        </div>
        <div class="hero-badge-wrap">
          <div class="hero-badge">
            <span class="badge-title">Current Role</span>
            <strong>{{ roleLabel }}</strong>
          </div>
        </div>
      </div>
    </el-card>

    <el-row :gutter="14" class="kpi-row">
      <el-col :xl="8" :md="12" :xs="24">
        <el-card class="kpi surface-hover">
          <p class="kpi-label">Workflow Integrity</p>
          <h3>Registration Flow</h3>
          <p class="muted">Track queue throughput, state transitions, and reviewer decisions.</p>
        </el-card>
      </el-col>
      <el-col :xl="8" :md="12" :xs="24">
        <el-card class="kpi surface-hover">
          <p class="kpi-label">Financial Control</p>
          <h3>Budget Oversight</h3>
          <p class="muted">Monitor expenses, overspend alerts, and invoice-backed transactions.</p>
        </el-card>
      </el-col>
      <el-col :xl="8" :md="24" :xs="24">
        <el-card class="kpi surface-hover">
          <p class="kpi-label">Audit Readiness</p>
          <h3>Compliance Center</h3>
          <p class="muted">Generate exports, validate backups, and review access audit traces.</p>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>

<script setup lang="ts">
const role = localStorage.getItem("user_role") || "";

const roleLabel =
  role === "system_admin"
    ? "System Administrator"
    : role === "financial_admin"
      ? "Financial Administrator"
      : role === "reviewer"
        ? "Reviewer"
        : role === "applicant"
          ? "Applicant"
          : "Unknown";
</script>

<style scoped>
.dashboard-title {
  margin: 4px 0;
  font-size: clamp(1.5rem, 2.8vw, 2rem);
}
.quick-actions {
  margin-top: 16px;
}
.kpi-row {
  margin-top: 12px;
}
.kpi h3 {
  margin: 0 0 8px;
}
.hero {
  background: linear-gradient(135deg, #ffffff 0%, #f4f8ff 60%, #eefaf4 100%);
}
.hero-grid {
  display: grid;
  grid-template-columns: 1.2fr 0.8fr;
  gap: 16px;
}
.eyebrow {
  margin: 0;
  font-size: 0.78rem;
  letter-spacing: 1.2px;
  text-transform: uppercase;
  color: #35518c;
  font-weight: 700;
}
.hero-badge-wrap {
  display: flex;
  justify-content: flex-end;
  align-items: center;
}
.hero-badge {
  min-width: 190px;
  border: 1px solid #d5e2fb;
  background: #ffffff;
  border-radius: 14px;
  box-shadow: 0 10px 24px rgba(31, 111, 235, 0.08);
  padding: 14px;
}
.badge-title {
  display: block;
  color: #5a6680;
  font-size: 0.85rem;
  margin-bottom: 4px;
}
.kpi {
  min-height: 170px;
}
.kpi-label {
  margin: 0 0 8px;
  font-size: 0.8rem;
  text-transform: uppercase;
  letter-spacing: 1px;
  color: #35518c;
  font-weight: 700;
}
@media (max-width: 980px) {
  .hero-grid {
    grid-template-columns: 1fr;
  }
  .hero-badge-wrap {
    justify-content: flex-start;
  }
}
</style>
