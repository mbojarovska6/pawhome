<!--
  Reusable table with pagination.
  Props:
    columns: [{ key: 'name', label: 'Name' }]
    rows, page, limit, total, loading
  Slots:
    cell-<key>  (custom rendering of one column, gets { row })
    actions     (buttons on the right, gets { row })
-->
<script setup>
import { computed } from 'vue';

const props = defineProps({
  columns: { type: Array, required: true },
  rows: { type: Array, default: () => [] },
  page: { type: Number, default: 1 },
  limit: { type: Number, default: 20 },
  total: { type: Number, default: 0 },
  loading: { type: Boolean, default: false },
});
const emit = defineEmits(['update:page']);

const pages = computed(() => Math.max(1, Math.ceil(props.total / props.limit)));
const from = computed(() => (props.total === 0 ? 0 : (props.page - 1) * props.limit + 1));
const to = computed(() => Math.min(props.page * props.limit, props.total));
</script>

<template>
  <div class="card">
    <div class="table-wrap">
      <table>
        <thead>
          <tr>
            <th v-for="col in columns" :key="col.key">{{ col.label }}</th>
            <th></th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="row in rows" :key="row.id">
            <td v-for="col in columns" :key="col.key">
              <slot :name="`cell-${col.key}`" :row="row">{{ row[col.key] ?? '—' }}</slot>
            </td>
            <td class="actions"><slot name="actions" :row="row" /></td>
          </tr>
        </tbody>
      </table>
      <div v-if="loading" class="empty">Loading…</div>
      <div v-else-if="rows.length === 0" class="empty">No records found.</div>
    </div>

    <div class="pager">
      <span>{{ from }}–{{ to }} of {{ total.toLocaleString() }}</span>
      <div class="buttons">
        <button class="btn secondary small" :disabled="page <= 1" @click="emit('update:page', page - 1)">← Prev</button>
        <span style="padding: 5px 8px">Page {{ page }} / {{ pages }}</span>
        <button class="btn secondary small" :disabled="page >= pages" @click="emit('update:page', page + 1)">Next →</button>
      </div>
    </div>
  </div>
</template>
