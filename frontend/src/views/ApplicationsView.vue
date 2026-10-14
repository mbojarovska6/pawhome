<script setup>
import { ref, watch, onMounted } from 'vue';
import { applications, errorMessage } from '../api';
import { showFlash } from '../flash';
import DataTable from '../components/DataTable.vue';
import ConfirmDialog from '../components/ConfirmDialog.vue';

const columns = [
  { key: 'id', label: '#' },
  { key: 'animal_name', label: 'Animal' },
  { key: 'adopter_name', label: 'Adopter' },
  { key: 'status', label: 'Status' },
  { key: 'submitted_at', label: 'Submitted' },
  { key: 'decided_at', label: 'Decided' },
];

const rows = ref([]);
const total = ref(0);
const page = ref(1);
const limit = 20;
const loading = ref(false);
const error = ref('');
const search = ref('');
const status = ref('');
const toDelete = ref(null);
const deleting = ref(false);

const formatDate = (value) => (value ? new Date(value).toLocaleDateString() : '—');

async function load() {
  loading.value = true;
  error.value = '';
  try {
    const res = await applications.list({ page: page.value, limit, search: search.value, status: status.value });
    rows.value = res.data;
    total.value = res.total;
  } catch (err) {
    error.value = errorMessage(err);
  } finally {
    loading.value = false;
  }
}

let timer;
watch([search, status], () => {
  clearTimeout(timer);
  timer = setTimeout(() => (page.value === 1 ? load() : (page.value = 1)), 300);
});
watch(page, load);
onMounted(load);

// Quick action: change status straight from the table.
async function setStatus(row, newStatus) {
  try {
    await applications.update(row.id, { status: newStatus });
    showFlash(`Application #${row.id} is now ${newStatus}`);
    load();
  } catch (err) {
    showFlash(errorMessage(err), 'error');
  }
}

async function confirmDelete() {
  deleting.value = true;
  try {
    await applications.remove(toDelete.value.id);
    showFlash(`Application #${toDelete.value.id} was deleted`);
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
    <h1>Applications <span class="count">{{ total.toLocaleString() }}</span></h1>
    <router-link to="/applications/new" class="btn">+ New application</router-link>
  </div>

  <div class="toolbar">
    <input v-model="search" placeholder="Search animal or adopter…" />
    <select v-model="status">
      <option value="">All statuses</option>
      <option>pending</option><option>approved</option><option>rejected</option><option>adopted</option>
    </select>
  </div>

  <div v-if="error" class="error-box">{{ error }}</div>

  <DataTable :columns="columns" :rows="rows" :total="total" :limit="limit" :loading="loading" v-model:page="page">
    <template #cell-animal_name="{ row }">{{ row.animal_name }} <small style="color: var(--muted)">({{ row.animal_species }})</small></template>
    <template #cell-status="{ row }"><span :class="['badge', row.status]">{{ row.status }}</span></template>
    <template #cell-submitted_at="{ row }">{{ formatDate(row.submitted_at) }}</template>
    <template #cell-decided_at="{ row }">{{ formatDate(row.decided_at) }}</template>
    <template #actions="{ row }">
      <template v-if="row.status === 'pending'">
        <button class="btn link small" @click="setStatus(row, 'approved')">Approve</button>
        <button class="btn link small" @click="setStatus(row, 'rejected')">Reject</button>
      </template>
      <button v-if="row.status === 'approved'" class="btn link small" @click="setStatus(row, 'adopted')">Mark adopted</button>
      <router-link :to="`/applications/${row.id}/edit`" class="btn link small">Edit</router-link>
      <button class="btn link danger small" @click="toDelete = row">Delete</button>
    </template>
  </DataTable>

  <ConfirmDialog
    v-if="toDelete"
    :title="`Delete application #${toDelete.id}?`"
    :message="`${toDelete.adopter_name}'s application for ${toDelete.animal_name} will be removed.`"
    :busy="deleting"
    @cancel="toDelete = null"
    @confirm="confirmDelete"
  />
</template>
