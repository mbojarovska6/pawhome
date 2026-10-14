<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { adopters, errorMessage } from '../api';
import { showFlash } from '../flash';

const route = useRoute();
const router = useRouter();
const id = route.params.id;
const isEdit = computed(() => Boolean(id));

const form = ref({
  first_name: '',
  last_name: '',
  email: '',
  phone: '',
  city: '',
  date_of_birth: '',
  has_garden: false,
});
const error = ref('');
const saving = ref(false);

// Adopters must be at least 18: latest allowed birth date.
const maxBirthDate = (() => {
  const d = new Date();
  d.setFullYear(d.getFullYear() - 18);
  return d.toISOString().slice(0, 10);
})();

onMounted(async () => {
  if (!isEdit.value) return;
  try {
    const adopter = await adopters.get(id);
    for (const key of Object.keys(form.value)) form.value[key] = adopter[key] ?? '';
  } catch (err) {
    error.value = errorMessage(err);
  }
});

async function save() {
  saving.value = true;
  error.value = '';
  try {
    if (isEdit.value) await adopters.update(id, form.value);
    else await adopters.create(form.value);
    showFlash(`${form.value.first_name} ${form.value.last_name} was saved`);
    router.push('/adopters');
  } catch (err) {
    error.value = errorMessage(err);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="page-head">
    <h1>{{ isEdit ? 'Edit adopter' : 'Add adopter' }}</h1>
  </div>

  <div v-if="error" class="error-box">{{ error }}</div>

  <form class="card form" @submit.prevent="save">
    <div class="field">
      <label>First name *</label>
      <input v-model.trim="form.first_name" required maxlength="60" />
    </div>
    <div class="field">
      <label>Last name *</label>
      <input v-model.trim="form.last_name" required maxlength="60" />
    </div>
    <div class="field">
      <label>Email *</label>
      <input v-model.trim="form.email" type="email" required maxlength="120" />
    </div>
    <div class="field">
      <label>Phone</label>
      <input v-model.trim="form.phone" maxlength="30" />
    </div>
    <div class="field">
      <label>City</label>
      <input v-model.trim="form.city" maxlength="80" />
    </div>
    <div class="field">
      <label>Date of birth</label>
      <input v-model="form.date_of_birth" type="date" :max="maxBirthDate" />
      <span class="hint">Adopters must be 18 or older.</span>
    </div>
    <div class="field check">
      <input id="garden" v-model="form.has_garden" type="checkbox" />
      <label for="garden">Has a garden</label>
    </div>
    <div class="form-actions">
      <button class="btn" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      <router-link to="/adopters" class="btn secondary">Cancel</router-link>
    </div>
  </form>
</template>
