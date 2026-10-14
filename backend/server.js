const express = require('express');
const cors = require('cors');
const pool = require('./db');

const app = express();
app.use(cors());            // allow the Vue app (port 5173) to call this API (port 3000)
app.use(express.json());    // parse JSON request bodies

// Quick check that the API and the database are both up.
app.get('/api/health', async (req, res, next) => {
  try {
    await pool.query('SELECT 1');
    res.json({ status: 'ok' });
  } catch (err) {
    next(err);
  }
});

// Row counts per table, shown on the frontend's dashboard.
app.get('/api/stats', async (req, res, next) => {
  try {
    const { rows } = await pool.query(`
      SELECT
        (SELECT COUNT(*)::int FROM shelters)     AS shelters,
        (SELECT COUNT(*)::int FROM adopters)     AS adopters,
        (SELECT COUNT(*)::int FROM animals)      AS animals,
        (SELECT COUNT(*)::int FROM applications) AS applications,
        (SELECT COUNT(*)::int FROM animals WHERE status = 'available')    AS available_animals,
        (SELECT COUNT(*)::int FROM applications WHERE status = 'pending') AS pending_applications`);
    res.json(rows[0]);
  } catch (err) {
    next(err);
  }
});

app.use('/api/shelters', require('./routes/shelters'));
app.use('/api/animals', require('./routes/animals'));
app.use('/api/adopters', require('./routes/adopters'));
app.use('/api/applications', require('./routes/applications'));

// Unknown /api route
app.use('/api', (req, res) => res.status(404).json({ error: 'Route not found' }));

// One place that turns PostgreSQL errors into friendly HTTP responses.
// eslint-disable-next-line no-unused-vars
app.use((err, req, res, next) => {
  switch (err.code) {
    case '23505': // unique_violation
      return res.status(409).json({ error: 'A record with this value already exists (e.g. email)' });
    case '23503': // foreign_key_violation
      return res.status(400).json({ error: 'Referenced record does not exist (check shelter, animal or adopter)' });
    case '23514': // check_violation
      return res.status(400).json({ error: `Invalid value (${err.constraint})` });
    case '23502': // not_null_violation
      return res.status(400).json({ error: `Field "${err.column}" is required` });
    case '22P02': // invalid_text_representation, e.g. "abc" for a number
    case '22007': // invalid_datetime_format
    case '22008': // datetime_field_overflow
      return res.status(400).json({ error: 'A field has the wrong format' });
    default:
      console.error(err);
      return res.status(500).json({ error: 'Server error' });
  }
});

const PORT = process.env.PORT || 3000;
app.listen(PORT, () => console.log(`PawHome API running on http://localhost:${PORT}`));
