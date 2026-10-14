<!--
  Search-as-you-type picker for big tables (3,000 animals, 2,000 adopters),
  where a normal <select> with every row would be too slow.
  v-model holds the selected id.
-->
<script setup>
import { ref, onMounted } from 'vue';

const props = defineProps({
  modelValue: { type: [Number, String, null], default: null },
  api: { type: Object, required: true },        // e.g. animals from api.js
  labelFn: { type: Function, required: true },  // row => text shown to the user
  placeholder: { type: String, default: 'Type to search…' },
});
const emit = defineEmits(['update:modelValue']);

const query = ref('');
const options = ref([]);
const open = ref(false);
const selectedLabel = ref('');
let timer;

// When editing, show the label of the already selected record.
onMounted(async () => {
  if (props.modelValue) {
    try {
      selectedLabel.value = props.labelFn(await props.api.get(props.modelValue));
    } catch {
      selectedLabel.value = `#${props.modelValue}`;
    }
  }
});

function onInput() {
  clearTimeout(timer);
  timer = setTimeout(async () => {
    const res = await props.api.list({ search: query.value, limit: 8 });
    options.value = res.data;
    open.value = true;
  }, 250);
}

function choose(row) {
  emit('update:modelValue', row.id);
  selectedLabel.value = props.labelFn(row);
  query.value = '';
  open.value = false;
}

function closeLater() {
  setTimeout(() => (open.value = false), 150); // let a click on an option register first
}
</script>

<template>
  <div class="search-select">
    <input v-model="query" :placeholder="placeholder" @input="onInput" @focus="onInput" @blur="closeLater" />
    <ul v-if="open && options.length">
      <li v-for="row in options" :key="row.id" @mousedown.prevent="choose(row)">{{ labelFn(row) }}</li>
    </ul>
    <div v-if="selectedLabel" class="selected">Selected: {{ selectedLabel }}</div>
  </div>
</template>
