<script setup>
import { ref, computed, onMounted } from 'vue';
import { useRoute, useRouter } from 'vue-router';
import { animals, shelters, errorMessage } from '../api';
import { showFlash } from '../flash';

const route = useRoute();
const router = useRouter();
const id = route.params.id;              // undefined when adding a new animal
const isEdit = computed(() => Boolean(id));

const form = ref({
  shelter_id: '',
  name: '',
  species: 'dog',
  breed: '',
  sex: 'F',
  age_years: 1,
  size: 'medium',
  is_vaccinated: false,
  status: 'available',
  arrived_at: new Date().toISOString().slice(0, 10),
  description: '',
});
const shelterOptions = ref([]);
const error = ref('');
const saving = ref(false);

onMounted(async () => {
  try {
    // 50 shelters are few enough for a normal dropdown.
    shelterOptions.value = (await shelters.list({ limit: 100 })).data;
    if (isEdit.value) {
      const animal = await animals.get(id);
      for (const key of Object.keys(form.value)) form.value[key] = animal[key] ?? '';
    }
  } catch (err) {
    error.value = errorMessage(err);
  }
});

async function save() {
  saving.value = true;
  error.value = '';
  try {
    if (isEdit.value) await animals.update(id, form.value);
    else await animals.create(form.value);
    showFlash(`${form.value.name} was saved`);
    router.push('/animals');
  } catch (err) {
    error.value = errorMessage(err);
  } finally {
    saving.value = false;
  }
}
</script>

<template>
  <div class="page-head">
    <h1>{{ isEdit ? 'Edit animal' : 'Add animal' }}</h1>
  </div>

  <div v-if="error" class="error-box">{{ error }}</div>

  <form class="card form" @submit.prevent="save">
    <div class="field">
      <label>Name *</label>
      <input v-model.trim="form.name" required maxlength="60" />
    </div>
    <div class="field">
      <label>Shelter *</label>
      <select v-model.number="form.shelter_id" required>
        <option value="" disabled>Choose a shelter</option>
        <option v-for="s in shelterOptions" :key="s.id" :value="s.id">{{ s.name }}</option>
      </select>
    </div>
    <div class="field">
      <label>Species *</label>
      <select v-model="form.species" required>
        <option>dog</option><option>cat</option><option>rabbit</option>
        <option>bird</option><option>guinea pig</option>
      </select>
    </div>
    <div class="field">
      <label>Breed</label>
      <input v-model.trim="form.breed" maxlength="80" />
    </div>
    <div class="field">
      <label>Sex</label>
      <select v-model="form.sex">
        <option value="F">Female</option>
        <option value="M">Male</option>
      </select>
    </div>
    <div class="field">
      <label>Age (years)</label>
      <input v-model.number="form.age_years" type="number" min="0" max="40" step="0.1" />
    </div>
    <div class="field">
      <label>Size</label>
      <select v-model="form.size">
        <option>small</option><option>medium</option><option>large</option>
      </select>
    </div>
    <div class="field">
      <label>Status</label>
      <select v-model="form.status">
        <option>available</option><option>reserved</option><option>adopted</option>
      </select>
      <span class="hint">Also updated automatically when an application is approved or adopted.</span>
    </div>
    <div class="field">
      <label>Arrived at shelter</label>
      <input v-model="form.arrived_at" type="date" required />
    </div>
    <div class="field check">
      <input id="vacc" v-model="form.is_vaccinated" type="checkbox" />
      <label for="vacc">Vaccinated</label>
    </div>
    <div class="field wide">
      <label>Description</label>
      <textarea v-model="form.description" />
    </div>
    <div class="form-actions">
      <button class="btn" :disabled="saving">{{ saving ? 'Saving…' : 'Save' }}</button>
      <router-link to="/animals" class="btn secondary">Cancel</router-link>
    </div>
  </form>
</template>
