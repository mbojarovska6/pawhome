const crudRouter = require('./crud');

module.exports = crudRouter({
  table: 'adopters',
  alias: 'd',
  label: 'Adopter',
  columns: ['first_name', 'last_name', 'email', 'phone', 'city', 'date_of_birth', 'has_garden'],
  // Also return how many applications each adopter has made.
  selectSql: `
    SELECT d.*,
           (SELECT COUNT(*)::int FROM applications ap WHERE ap.adopter_id = d.id) AS application_count
    FROM adopters d`,
  searchColumns: ['d.first_name', 'd.last_name', 'd.email', 'd.city'],
  filters: { city: 'd.city' },
  orderBy: 'd.id DESC',
});
