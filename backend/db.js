// Shared PostgreSQL connection pool used by the API and the seed script.
const { Pool, types } = require('pg');

// PostgreSQL NUMERIC (type id 1700) comes back as a string by default.
// Convert it to a JS number so age_years is e.g. 2.5 instead of "2.5".
types.setTypeParser(1700, (value) => (value === null ? null : parseFloat(value)));

// DATE (type id 1082): keep it as a plain 'YYYY-MM-DD' string
// so it does not shift by a day because of time zones.
types.setTypeParser(1082, (value) => value);

const pool = new Pool({
  connectionString:
    process.env.DATABASE_URL || 'postgres://pawhome:pawhome@localhost:5432/pawhome',
});

module.exports = pool;
