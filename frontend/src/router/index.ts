import { createRouter, createWebHistory, RouteRecordRaw } from "vue-router";

import LoginView from "../views/LoginView.vue";
import DashboardView from "../views/DashboardView.vue";
import ApplicantWizardView from "../views/ApplicantWizardView.vue";
import ReviewerQueueView from "../views/ReviewerQueueView.vue";
import FinanceManagementView from "../views/FinanceManagementView.vue";
import AdminSettingsView from "../views/AdminSettingsView.vue";
import AuditLogsView from "../views/AuditLogsView.vue";

const routes: RouteRecordRaw[] = [
  { path: "/", redirect: "/login" },
  { path: "/login", component: LoginView, meta: { public: true } },
  { path: "/dashboard", component: DashboardView, meta: { roles: ["applicant", "reviewer", "financial_admin", "system_admin"] } },
  { path: "/applicant/wizard", component: ApplicantWizardView, meta: { roles: ["applicant", "system_admin"] } },
  { path: "/reviewer/queue", component: ReviewerQueueView, meta: { roles: ["reviewer", "system_admin"] } },
  { path: "/finance/management", component: FinanceManagementView, meta: { roles: ["financial_admin", "system_admin"] } },
  { path: "/admin/settings", component: AdminSettingsView, meta: { roles: ["system_admin"] } },
  { path: "/audit/logs", component: AuditLogsView, meta: { roles: ["reviewer", "system_admin"] } },
];

const router = createRouter({
  history: createWebHistory(),
  routes,
});

router.beforeEach((to) => {
  const token = localStorage.getItem("access_token");
  if (!to.meta.public && !token) {
    return "/login";
  }

  if (to.meta.roles) {
    const role = localStorage.getItem("user_role");
    if (!role || !(to.meta.roles as string[]).includes(role)) {
      return "/dashboard";
    }
  }
  return true;
});

export default router;
