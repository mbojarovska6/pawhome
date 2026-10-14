<script setup>
import { ref, onMounted } from 'vue';
import { getStats, errorMessage } from '../api';

const stats = ref(null);
const error = ref('');

onMounted(async () => {
  try {
    stats.value = await getStats();
  } catch (err) {
    error.value = errorMessage(err);
  }
});
</script>

<template>
  <section class="hero">
    <h1>Welcome to PawHome</h1>
    <p>Manage shelters, animals, adopters and adoption applications in one place.</p>
  </section>

  <div v-if="error" class="error-box">Could not reach the API: {{ error }}</div>

  <div v-if="stats" class="stats">
    <router-link to="/animals" class="card stat">
      <div class="num">{{ stats.animals.toLocaleString() }}</div>
      <div class="label">Animals</div>
      <div class="sub">{{ stats.available_animals.toLocaleString() }} available</div>
    </router-link>
    <router-link to="/shelters" class="card stat">
      <div class="num">{{ stats.shelters.toLocaleString() }}</div>
      <div class="label">Shelters</div>
    </router-link>
    <router-link to="/adopters" class="card stat">
      <div class="num">{{ stats.adopters.toLocaleString() }}</div>
      <div class="label">Adopters</div>
    </router-link>
    <router-link to="/applications" class="card stat">
      <div class="num">{{ stats.applications.toLocaleString() }}</div>
      <div class="label">Applications</div>
      <div class="sub">{{ stats.pending_applications.toLocaleString() }} pending</div>
    </router-link>
  </div>
</template>
