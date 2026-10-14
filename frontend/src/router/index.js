import { createRouter, createWebHistory } from 'vue-router';

import DashboardView from '../views/DashboardView.vue';
import SheltersView from '../views/SheltersView.vue';
import ShelterForm from '../views/ShelterForm.vue';
import AnimalsView from '../views/AnimalsView.vue';
import AnimalForm from '../views/AnimalForm.vue';
import AdoptersView from '../views/AdoptersView.vue';
import AdopterForm from '../views/AdopterForm.vue';
import ApplicationsView from '../views/ApplicationsView.vue';
import ApplicationForm from '../views/ApplicationForm.vue';

const routes = [
  { path: '/', component: DashboardView },

  { path: '/shelters', component: SheltersView },
  { path: '/shelters/new', component: ShelterForm },
  { path: '/shelters/:id/edit', component: ShelterForm },

  { path: '/animals', component: AnimalsView },
  { path: '/animals/new', component: AnimalForm },
  { path: '/animals/:id/edit', component: AnimalForm },

  { path: '/adopters', component: AdoptersView },
  { path: '/adopters/new', component: AdopterForm },
  { path: '/adopters/:id/edit', component: AdopterForm },

  { path: '/applications', component: ApplicationsView },
  { path: '/applications/new', component: ApplicationForm },
  { path: '/applications/:id/edit', component: ApplicationForm },

  { path: '/:pathMatch(.*)*', redirect: '/' },
];

export default createRouter({
  history: createWebHistory(),
  routes,
});
