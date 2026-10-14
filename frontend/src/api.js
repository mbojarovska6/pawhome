// All communication with the Express backend goes through this file.
import axios from 'axios';

const http = axios.create({
  baseURL: import.meta.env.VITE_API_URL || 'http://localhost:3000/api',
});

// Creates the five CRUD functions for one resource, e.g. resource('animals').
function resource(name) {
  return {
    list: (params) => http.get(`/${name}`, { params }).then((r) => r.data),
    get: (id) => http.get(`/${name}/${id}`).then((r) => r.data),
    create: (data) => http.post(`/${name}`, data).then((r) => r.data),
    update: (id, data) => http.put(`/${name}/${id}`, data).then((r) => r.data),
    remove: (id) => http.delete(`/${name}/${id}`),
  };
}

export const shelters = resource('shelters');
export const animals = resource('animals');
export const adopters = resource('adopters');
export const applications = resource('applications');

export const getStats = () => http.get('/stats').then((r) => r.data);

// Turn an axios error into a message we can show to the user.
export function errorMessage(err) {
  return err?.response?.data?.error || err?.message || 'Something went wrong';
}
