const crudRouter = require('./crud');
const pool = require('../db');

// Recalculate an animal's status from its applications:
//   any application 'adopted'  -> animal 'adopted'
//   any application 'approved' -> animal 'reserved'
//   otherwise                  -> animal 'available'
async function syncAnimalStatus(animalId) {
  await pool.query(
    `UPDATE animals SET status = CASE
        WHEN EXISTS (SELECT 1 FROM applications WHERE animal_id = $1 AND status = 'adopted')  THEN 'adopted'
        WHEN EXISTS (SELECT 1 FROM applications WHERE animal_id = $1 AND status = 'approved') THEN 'reserved'
        ELSE 'available'
      END
     WHERE id = $1`,
    [animalId]
  );
}

module.exports = crudRouter({
  table: 'applications',
  alias: 'ap',
  label: 'Application',
  columns: ['animal_id', 'adopter_id', 'status', 'message'],
  // JOIN both parents so the table shows names, not ids.
  selectSql: `
    SELECT ap.*,
           an.name    AS animal_name,
           an.species AS animal_species,
           d.first_name || ' ' || d.last_name AS adopter_name,
           d.email    AS adopter_email
    FROM applications ap
    JOIN animals  an ON an.id = ap.animal_id
    JOIN adopters d  ON d.id  = ap.adopter_id`,
  searchColumns: ['an.name', 'd.first_name', 'd.last_name', 'd.email'],
  filters: { status: 'ap.status', animal_id: 'ap.animal_id', adopter_id: 'ap.adopter_id' },
  orderBy: 'ap.submitted_at DESC',

  // Set decided_at automatically when the status leaves or returns to 'pending'.
  beforeWrite(data, before) {
    if (data.status === undefined) return data;
    if (data.status === 'pending') {
      data.decided_at = null;
    } else if (!before || before.status === 'pending' || before.status !== data.status) {
      data.decided_at = new Date();
    }
    return data;
  },

  // Indirect edit: changing an application also updates the animal's status.
  async afterWrite({ before, after }) {
    const ids = new Set([before?.animal_id, after?.animal_id].filter(Boolean));
    for (const id of ids) await syncAnimalStatus(id);
  },
});
