<template>
  <AppShell v-if="!isLoginRoute">
    <router-view />
  </AppShell>
  <router-view v-else />
</template>

<script setup lang="ts">
import { computed } from "vue";
import { useRoute } from "vue-router";

import AppShell from "./layouts/AppShell.vue";

const route = useRoute();
const isLoginRoute = computed(() => route.path === "/login");
</script>
