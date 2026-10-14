<script setup>
import { ref, watch, onMounted } from 'vue';
import { animals, errorMessage } from '../api';
import { showFlash } from '../flash';
import DataTable from '../components/DataTable.vue';
import ConfirmDialog from '../components/ConfirmDialog.vue';

const columns = [
  { key: 'id', label: '#' },
  { key: 'name', label: 'Name' },
  { key: 'species', label: 'Species' },
  { key: 'breed', label: 'Breed' },
  { key: 'age_years', label: 'Age' },
  { key: 'shelter_name', label: 'Shelter' },
  { key: 'status', label: 'Status' },
];

const rows = ref([]);
const total = ref(0);
const page = ref(1);
const limit = 20;
const loading = ref(false);
const error = ref('');

const search = ref('');
const species = ref('');
const status = ref('');

const toDelete = ref(null);
const deleting = ref(false);

async function load() {
  loading.value = true;
  error.value = '';
  try {
    const res = await animals.list({
      page: page.value, limit, search: search.value, species: species.value, status: status.value,
    });
    rows.value = res.data;
    total.value = res.total;
  } catch (err) {
    error.value = errorMessage(err);
  } finally {
    loading.value = false;
  }
}

// Reload when filters change (with a short delay while typing).
let timer;
watch([search, species, status], () => {
  clearTimeout(timer);
  timer = setTimeout(() => {
    if (page.value === 1) load();
    else page.value = 1; // the page watcher will reload
  }, 300);
});
watch(page, load);
onMounted(load);

async function confirmDelete() {
  deleting.value = true;
  try {
    await animals.remove(toDelete.value.id);
    showFlash(`${toDelete.value.name} was deleted`);
    toDelete.value = null;
    load();
  } catch (err) {
    showFlash(errorMessage(err), 'error');
  } finally {
    deleting.value = false;
  }
}
</script>

<template>
  <div class="page-head">
    <h1>Animals <span class="count">{{ total.toLocaleString() }}</span></h1>
    <router-link to="/animals/new" class="btn">+ Add animal</router-link>
  </div>

  <div class="toolbar">
    <input v-model="search" placeholder="Search name or breed…" />
    <select v-model="species">
      <option value="">All species</option>
      <option>dog</option><option>cat</option><option>rabbit</option>
      <option>bird</option><option>guinea pig</option>
    </select>
    <select v-model="status">
      <option value="">All statuses</option>
      <option>available</option><option>reserved</option><option>adopted</option>
    </select>
  </div>

  <div v-if="error" class="error-box">{{ error }}</div>

  <DataTable :columns="columns" :rows="rows" :total="total" :limit="limit" :loading="loading" v-model:page="page">
    <template #cell-age_years="{ row }">{{ row.age_years }} yrs</template>
    <template #cell-status="{ row }"><span :class="['badge', row.status]">{{ row.status }}</span></template>
    <template #actions="{ row }">
      <router-link :to="`/animals/${row.id}/edit`" class="btn link small">Edit</router-link>
      <button class="btn link danger small" @click="toDelete = row">Delete</button>
    </template>
  </DataTable>

  <ConfirmDialog
    v-if="toDelete"
    :title="`Delete ${toDelete.name}?`"
    message="This also deletes all adoption applications for this animal."
    :busy="deleting"
    @cancel="toDelete = null"
    @confirm="confirmDelete"
  />
</template>
