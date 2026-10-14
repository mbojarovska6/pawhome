const crudRouter = require('./crud');

module.exports = crudRouter({
  table: 'animals',
  alias: 'a',
  label: 'Animal',
  columns: [
    'shelter_id', 'name', 'species', 'breed', 'sex', 'age_years',
    'size', 'is_vaccinated', 'status', 'arrived_at', 'description',
  ],
  // JOIN shelters so the list can show the shelter name instead of an id.
  selectSql: `
    SELECT a.*, s.name AS shelter_name
    FROM animals a
    JOIN shelters s ON s.id = a.shelter_id`,
  searchColumns: ['a.name', 'a.breed'],
  filters: { species: 'a.species', status: 'a.status', shelter_id: 'a.shelter_id' },
  orderBy: 'a.id DESC',
});
