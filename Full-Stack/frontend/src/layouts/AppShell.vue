<template>
  <div class="shell">
    <aside class="sidebar" :class="{ collapsed: sidebarCollapsed }">
      <div class="brand">
        <div class="logo">AR</div>
        <div v-if="!sidebarCollapsed" class="brand-text">
          <strong>Activity Audit</strong>
          <small>Management Platform</small>
        </div>
      </div>

      <nav class="nav">
        <button v-for="item in navItems" :key="item.path" class="nav-item" :class="{ active: route.path === item.path }" @click="go(item.path)">
          <span class="dot" />
          <span>{{ item.label }}</span>
        </button>
      </nav>

      <div class="sidebar-footer">
        <el-button size="small" @click="sidebarCollapsed = !sidebarCollapsed">{{ sidebarCollapsed ? "Expand" : "Collapse" }}</el-button>
      </div>
    </aside>

    <main class="main">
      <header class="topbar">
        <div>
          <h1>Activity Registration and Funding Audit</h1>
          <p>{{ roleLabel }} · Offline-ready mode</p>
        </div>
        <div class="topbar-actions">
          <el-tag>{{ roleLabel }}</el-tag>
          <span class="status-pill success">Online</span>
          <el-button @click="logout">Logout</el-button>
        </div>
      </header>

      <section class="content">
        <slot />
      </section>
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed, ref } from "vue";
import { useRoute, useRouter } from "vue-router";

const route = useRoute();
const router = useRouter();
const sidebarCollapsed = ref(false);

const role = localStorage.getItem("user_role") || "";

const allItems = [
  { path: "/dashboard", label: "Dashboard", roles: ["applicant", "reviewer", "financial_admin", "system_admin"] },
  { path: "/applicant/wizard", label: "Applicant", roles: ["applicant", "system_admin"] },
  { path: "/reviewer/queue", label: "Reviewer", roles: ["reviewer", "system_admin"] },
  { path: "/finance/management", label: "Finance", roles: ["financial_admin", "system_admin"] },
  { path: "/admin/settings", label: "Admin", roles: ["system_admin"] },
  { path: "/audit/logs", label: "Audit", roles: ["reviewer", "system_admin"] },
];

const navItems = computed(() => allItems.filter((item) => item.roles.includes(role)));

const roleLabel = computed(() => {
  if (role === "system_admin") return "System Administrator";
  if (role === "financial_admin") return "Financial Administrator";
  if (role === "reviewer") return "Reviewer";
  if (role === "applicant") return "Applicant";
  return "Unknown Role";
});

const go = (path: string) => {
  if (route.path !== path) router.push(path);
};

const logout = () => {
  localStorage.removeItem("access_token");
  localStorage.removeItem("user_role");
  router.push("/login");
};
</script>

<style scoped>
.shell {
  display: grid;
  grid-template-columns: 250px 1fr;
  min-height: 100vh;
}
.sidebar {
  background: linear-gradient(180deg, #0c1a3f 0%, #13285a 48%, #1b3574 100%);
  color: #dce4ff;
  padding: 16px;
  display: flex;
  flex-direction: column;
  gap: 14px;
  box-shadow: inset -1px 0 0 rgba(255, 255, 255, 0.06);
}
.collapsed {
  width: 84px;
}
.brand {
  display: flex;
  align-items: center;
  gap: 10px;
}
.logo {
  width: 38px;
  height: 38px;
  border-radius: 10px;
  background: linear-gradient(135deg, #8bb4ff, #6ee7b7);
  color: #0f2045;
  display: grid;
  place-items: center;
  font-weight: 700;
}
.brand-text {
  display: flex;
  flex-direction: column;
}
.brand-text small {
  opacity: 0.85;
}
.nav {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.nav-item {
  text-align: left;
  border: 1px solid rgba(220, 228, 255, 0.16);
  background: rgba(255, 255, 255, 0.05);
  color: inherit;
  border-radius: 12px;
  padding: 10px 12px;
  cursor: pointer;
  font-weight: 500;
  display: flex;
  align-items: center;
  gap: 9px;
}
.dot {
  width: 8px;
  height: 8px;
  border-radius: 999px;
  background: rgba(255, 255, 255, 0.25);
}
.nav-item.active,
.nav-item:hover {
  background: rgba(255, 255, 255, 0.16);
}
.nav-item.active .dot,
.nav-item:hover .dot {
  background: #84aef6;
}
.sidebar-footer {
  margin-top: auto;
}
.main {
  min-width: 0;
  position: relative;
}
.topbar {
  margin: 16px 16px 0;
  padding: 14px 16px;
  border-radius: 16px;
  border: 1px solid #dfe5f2;
  background: linear-gradient(180deg, #ffffffec, #fbfdffef);
  backdrop-filter: blur(8px);
  display: flex;
  justify-content: space-between;
  align-items: center;
  gap: 12px;
}
.topbar h1 {
  margin: 0;
  font-size: 1.2rem;
}
.topbar p {
  margin: 4px 0 0;
  color: #5a6680;
}
.topbar-actions {
  display: flex;
  align-items: center;
  gap: 8px;
}
.content {
  padding: 16px;
}

@media (max-width: 1200px) {
  .shell {
    grid-template-columns: 210px 1fr;
  }
}

@media (max-width: 980px) {
  .shell {
    grid-template-columns: 1fr;
  }
  .sidebar {
    position: sticky;
    top: 0;
    z-index: 30;
    flex-direction: row;
    align-items: center;
    padding: 10px;
  }
  .nav {
    flex-direction: row;
    overflow-x: auto;
    white-space: nowrap;
    flex: 1;
  }
  .sidebar-footer {
    display: none;
  }
}
</style>
