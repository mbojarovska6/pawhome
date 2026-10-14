<script setup>
import { ref, watch, onMounted } from 'vue';
import { adopters, errorMessage } from '../api';
import { showFlash } from '../flash';
import DataTable from '../components/DataTable.vue';
import ConfirmDialog from '../components/ConfirmDialog.vue';

const columns = [
  { key: 'id', label: '#' },
  { key: 'name', label: 'Name' },
  { key: 'email', label: 'Email' },
  { key: 'city', label: 'City' },
  { key: 'has_garden', label: 'Garden' },
  { key: 'application_count', label: 'Applications' },
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
    const res = await adopters.list({ page: page.value, limit, search: search.value });
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
    await adopters.remove(toDelete.value.id);
    showFlash(`${toDelete.value.first_name} ${toDelete.value.last_name} was deleted`);
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
    <h1>Adopters <span class="count">{{ total.toLocaleString() }}</span></h1>
    <router-link to="/adopters/new" class="btn">+ Add adopter</router-link>
  </div>

  <div class="toolbar">
    <input v-model="search" placeholder="Search name, email or city…" />
  </div>

  <div v-if="error" class="error-box">{{ error }}</div>

  <DataTable :columns="columns" :rows="rows" :total="total" :limit="limit" :loading="loading" v-model:page="page">
    <template #cell-name="{ row }">{{ row.first_name }} {{ row.last_name }}</template>
    <template #cell-has_garden="{ row }">{{ row.has_garden ? 'Yes' : 'No' }}</template>
    <template #actions="{ row }">
      <router-link :to="`/adopters/${row.id}/edit`" class="btn link small">Edit</router-link>
      <button class="btn link danger small" @click="toDelete = row">Delete</button>
    </template>
  </DataTable>

  <ConfirmDialog
    v-if="toDelete"
    :title="`Delete ${toDelete.first_name} ${toDelete.last_name}?`"
    :message="`This also deletes their ${toDelete.application_count} applications.`"
    :busy="deleting"
    @cancel="toDelete = null"
    @confirm="confirmDelete"
  />
</template>
