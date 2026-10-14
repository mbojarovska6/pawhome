<!-- "Are you sure?" popup used before deleting a record. -->
<script setup>
defineProps({
  title: { type: String, default: 'Are you sure?' },
  message: { type: String, default: '' },
  busy: { type: Boolean, default: false },
});
const emit = defineEmits(['confirm', 'cancel']);
</script>

<template>
  <div class="overlay" @click.self="emit('cancel')">
    <div class="card dialog">
      <h3>{{ title }}</h3>
      <p>{{ message }}</p>
      <div class="buttons">
        <button class="btn secondary" @click="emit('cancel')">Cancel</button>
        <button class="btn danger" :disabled="busy" @click="emit('confirm')">
          {{ busy ? 'Deleting…' : 'Delete' }}
        </button>
      </div>
    </div>
  </div>
</template>
