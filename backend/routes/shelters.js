const crudRouter = require('./crud');

module.exports = crudRouter({
  table: 'shelters',
  alias: 's',
  label: 'Shelter',
  columns: ['name', 'city', 'address', 'phone', 'email', 'capacity'],
  // Also return how many animals each shelter currently has.
  selectSql: `
    SELECT s.*,
           (SELECT COUNT(*)::int FROM animals a WHERE a.shelter_id = s.id) AS animal_count
    FROM shelters s`,
  searchColumns: ['s.name', 's.city'],
  filters: { city: 's.city' },
  orderBy: 's.name',
});
