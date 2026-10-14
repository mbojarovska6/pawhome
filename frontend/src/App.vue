<script setup>
import { flash } from './flash';
</script>

<template>
  <header class="topbar">
    <router-link to="/" class="brand">🐾 PawHome</router-link>
    <nav>
      <router-link to="/animals">Animals</router-link>
      <router-link to="/shelters">Shelters</router-link>
      <router-link to="/adopters">Adopters</router-link>
      <router-link to="/applications">Applications</router-link>
    </nav>
  </header>

  <div v-if="flash.text" :class="['flash', flash.kind]">{{ flash.text }}</div>

  <main class="container">
    <router-view />
  </main>
</template>
