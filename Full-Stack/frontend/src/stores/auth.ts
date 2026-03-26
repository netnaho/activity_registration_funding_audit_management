import { defineStore } from "pinia";

import { authApi } from "../api/endpoints";

interface UserProfile {
  id: number;
  username: string;
  full_name: string;
  role: string;
}

export const useAuthStore = defineStore("auth", {
  state: () => ({
    token: localStorage.getItem("access_token") || "",
    profile: null as UserProfile | null,
  }),
  actions: {
    async login(username: string, password: string) {
      const response = await authApi.login(username, password);
      const token = response.data?.data?.access_token;
      if (token) {
        this.token = token;
        localStorage.setItem("access_token", token);
      }
    },
    async fetchMe() {
      const response = await authApi.me();
      this.profile = response.data?.data || null;
      if (this.profile?.role) {
        localStorage.setItem("user_role", this.profile.role);
      }
    },
    logout() {
      this.token = "";
      this.profile = null;
      localStorage.removeItem("access_token");
      localStorage.removeItem("user_role");
    },
  },
});
