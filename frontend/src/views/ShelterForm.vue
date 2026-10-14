<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { shelters, errorMessage } from '../api';
import { showFlash } from '../flash';

const route = useRoute();
const router = useRouter();
const id = route.params.id;
const isEdit = computed(() => Boolean(id));

const form = ref({ name: '', city: '', address: '', phone: '', email: '', capacity: 50 });
const error = ref('');
const saving = ref(false);

onMounted(async () => {
  if (!isEdit.value) return;
  try {
    const shelter = await shelters.get(id);
    for (const key of Object.keys(form.value)) form.value[key] = shelter[key] ?? '';
  } catch (err) {
    error.value = errorMessage(err);
  }
});

async function save() {
  saving.value = true;
  error.value = '';
  try {
    if (isEdit.value) await shelters.update(id, form.value);
    else await shelters.create(form.value);
    showFlash(`${form.value.name} was saved`);
    router.push('/shelters');
  } catch (err) {
    error.value = errorMessage(err);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="page-head">
    <h1>{{ isEdit ? 'Edit shelter' : 'Add shelter' }}</h1>
  </div>

  <div v-if="error" class="error-box">{{ error }}</div>

  <form class="card form" @submit.prevent="save">
    <div class="field">
      <label>Name *</label>
      <input v-model.trim="form.name" required maxlength="120" />
    </div>
    <div class="field">
      <label>City *</label>
      <input v-model.trim="form.city" required maxlength="80" />
    </div>
    <div class="field wide">
      <label>Address</label>
      <input v-model.trim="form.address" maxlength="200" />
    </div>
    <div class="field">
      <label>Phone</label>
      <input v-model.trim="form.phone" maxlength="30" />
    </div>
    <div class="field">
      <label>Email</label>
      <input v-model.trim="form.email" type="email" maxlength="120" />
    </div>
    <div class="field">
      <label>Capacity (animals)</label>
      <input v-model.number="form.capacity" type="number" min="1" />
    </div>
    <div class="form-actions">
      <button class="btn" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      <router-link to="/shelters" class="btn secondary">Cancel</router-link>
    </div>
  </form>
</template>
