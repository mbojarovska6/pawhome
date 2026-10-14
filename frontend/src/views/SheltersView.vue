<script setup>
import { ref, watch, onMounted } from 'vue';
import { shelters, errorMessage } from '../api';
import { showFlash } from '../flash';
import DataTable from '../components/DataTable.vue';
import ConfirmDialog from '../components/ConfirmDialog.vue';

const columns = [
  { key: 'id', label: '#' },
  { key: 'name', label: 'Name' },
  { key: 'city', label: 'City' },
  { key: 'phone', label: 'Phone' },
  { key: 'capacity', label: 'Capacity' },
  { key: 'animal_count', label: 'Animals' },
];

const rows = ref([]);
const total = ref(0);
const page = ref(1);
const limit = 20;
const loading = ref(false);
const error = ref('');
const search = ref('');
const toDelete = ref(null);
const deleting = ref(false);

async function load() {
  loading.value = true;
  error.value = '';
  try {
    const res = await shelters.list({ page: page.value, limit, search: search.value });
    rows.value = res.data;
    total.value = res.total;
  } catch (err) {
    error.value = errorMessage(err);
  } finally {
    loading.value = false;
  }
}

let timer;
watch(search, () => {
  clearTimeout(timer);
  timer = setTimeout(() => (page.value === 1 ? load() : (page.value = 1)), 300);
});
watch(page, load);
onMounted(load);

async function confirmDelete() {
  deleting.value = true;
  try {
    await shelters.remove(toDelete.value.id);
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
    <h1>Shelters <span class="count">{{ total.toLocaleString() }}</span></h1>
    <router-link to="/shelters/new" class="btn">+ Add shelter</router-link>
  </div>

  <div class="toolbar">
    <input v-model="search" placeholder="Search name or city…" />
  </div>

  <div v-if="error" class="error-box">{{ error }}</div>

  <DataTable :columns="columns" :rows="rows" :total="total" :limit="limit" :loading="loading" v-model:page="page">
    <template #actions="{ row }">
      <router-link :to="`/shelters/${row.id}/edit`" class="btn link small">Edit</router-link>
      <button class="btn link danger small" @click="toDelete = row">Delete</button>
    </template>
  </DataTable>

  <ConfirmDialog
    v-if="toDelete"
    :title="`Delete ${toDelete.name}?`"
    :message="`This also deletes its ${toDelete.animal_count} animals and their applications.`"
    :busy="deleting"
    @cancel="toDelete = null"
    @confirm="confirmDelete"
  />
</template>
