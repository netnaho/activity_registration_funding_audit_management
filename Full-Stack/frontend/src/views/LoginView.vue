<template>
  <div class="login-page">
    <div class="left-panel">
      <div class="hero">
        <p class="eyebrow">Enterprise Platform</p>
        <h1>Activity Registration and Funding Audit Management</h1>
        <p class="lead">Secure, auditable, and fully offline-ready workflow platform.</p>
        <ul>
          <li>Checklist-based material management with versioning</li>
          <li>Review state machine with complete timeline</li>
          <li>Financial control, alerts, backup and recovery</li>
        </ul>
      </div>
    </div>

    <el-card class="login-card page-surface">
      <h2>Welcome Back</h2>
      <p class="muted">Sign in with your organization account.</p>
      <el-form @submit.prevent="onSubmit" label-position="top" class="login-form">
        <el-form-item label="Username">
          <el-input v-model="username" autocomplete="username" size="large" />
        </el-form-item>
        <el-form-item label="Password">
          <el-input v-model="password" type="password" autocomplete="current-password" show-password size="large" />
        </el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" size="large" class="cta">Login</el-button>
      </el-form>
      <p v-if="error" class="error">{{ error }}</p>
      <div class="muted demo-help">
        Demo: <code>admin / Admin@123456</code>
      </div>
    </el-card>
  </div>
</template>

<script setup lang="ts">
import { ref } from "vue";
import { useRouter } from "vue-router";
import { ElMessage } from "element-plus";
import { useAuthStore } from "../stores/auth";

const router = useRouter();
const auth = useAuthStore();

const username = ref("admin");
const password = ref("Admin@123456");
const loading = ref(false);
const error = ref("");

const onSubmit = async () => {
  loading.value = true;
  error.value = "";
  try {
    await auth.login(username.value, password.value);
    await auth.fetchMe();
    ElMessage.success("Login successful");
    await router.push("/dashboard");
  } catch {
    error.value = "Invalid username or password";
    ElMessage.error("Login failed");
  } finally {
    loading.value = false;
  }
};
</script>

<style scoped>
.login-page {
  min-height: 100vh;
  display: grid;
  grid-template-columns: 1.1fr 0.9fr;
  align-items: stretch;
  background: radial-gradient(circle at 10% 30%, #d9e8ff 0%, #eef3ff 40%, #f3f5f9 70%);
}
.left-panel {
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px;
}
.hero {
  max-width: 620px;
}
.eyebrow {
  letter-spacing: 1.4px;
  text-transform: uppercase;
  color: #35518c;
  font-weight: 600;
}
.hero h1 {
  margin: 10px 0;
  font-size: clamp(1.8rem, 3vw, 2.7rem);
  line-height: 1.2;
}
.lead {
  font-size: 1.04rem;
  color: #4d5d7d;
}
.hero ul {
  margin: 18px 0 0;
  padding-left: 18px;
  color: #3f4f70;
  line-height: 1.7;
}
.login-card {
  align-self: center;
  justify-self: center;
  width: min(440px, calc(100% - 26px));
  margin: 20px;
  padding: 8px;
  border: 1px solid #d9e3f8;
  box-shadow: 0 18px 46px rgba(20, 40, 80, 0.14);
}
.login-form {
  margin-top: 10px;
}
:deep(.el-form-item__label) {
  font-weight: 600;
}
.cta {
  width: 100%;
  font-weight: 700;
}
.error {
  color: #c0392b;
  margin-top: 10px;
}
.demo-help {
  margin-top: 14px;
}
@media (max-width: 980px) {
  .login-page {
    grid-template-columns: 1fr;
  }
  .left-panel {
    padding: 18px;
  }
  .hero ul {
    margin-bottom: 0;
  }
}
</style>
