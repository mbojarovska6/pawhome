<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { applications, animals, adopters, errorMessage } from '../api';
import { showFlash } from '../flash';
import SearchSelect from '../components/SearchSelect.vue';

const route = useRoute();
const router = useRouter();
const id = route.params.id;
const isEdit = computed(() => Boolean(id));

const form = ref({ animal_id: null, adopter_id: null, status: 'pending', message: '' });
const loaded = ref(!id); // new form is ready immediately; edit form waits for data
const error = ref('');
const saving = ref(false);

const animalLabel = (a) => `${a.name} – ${a.species}, ${a.breed ?? ''} (#${a.id}, ${a.status})`;
const adopterLabel = (d) => `${d.first_name} ${d.last_name} – ${d.email}`;

onMounted(async () => {
  if (!isEdit.value) return;
  try {
    const app = await applications.get(id);
    for (const key of Object.keys(form.value)) form.value[key] = app[key] ?? '';
    loaded.value = true;
  } catch (err) {
    error.value = errorMessage(err);
  }
});

async function save() {
  if (!form.value.animal_id || !form.value.adopter_id) {
    error.value = 'Please choose both an animal and an adopter.';
    return;
  }
  saving.value = true;
  error.value = '';
  try {
    if (isEdit.value) await applications.update(id, form.value);
    else await applications.create(form.value);
    showFlash('Application saved');
    router.push('/applications');
  } catch (err) {
    error.value = errorMessage(err);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="page-head">
    <h1>{{ isEdit ? `Edit application #${id}` : 'New application' }}</h1>
  </div>

  <div v-if="error" class="error-box">{{ error }}</div>

  <form v-if="loaded" class="card form" @submit.prevent="save">
    <div class="field">
      <label>Animal *</label>
      <SearchSelect v-model="form.animal_id" :api="animals" :label-fn="animalLabel" placeholder="Search animal by name or breed…" />
    </div>
    <div class="field">
      <label>Adopter *</label>
      <SearchSelect v-model="form.adopter_id" :api="adopters" :label-fn="adopterLabel" placeholder="Search adopter by name or email…" />
    </div>
    <div class="field">
      <label>Status</label>
      <select v-model="form.status">
        <option>pending</option><option>approved</option><option>rejected</option><option>adopted</option>
      </select>
      <span class="hint">Approved → animal becomes reserved. Adopted → animal becomes adopted.</span>
    </div>
    <div class="field wide">
      <label>Message from the adopter</label>
      <textarea v-model="form.message" />
    </div>
    <div class="form-actions">
      <button class="btn" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      <router-link to="/applications" class="btn secondary">Cancel</router-link>
    </div>
  </form>
</template>
