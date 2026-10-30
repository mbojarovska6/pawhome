// Runs every .sql file in the migrations/ folder, in name order.
// Run with:  npm run migrate
// Each migration is written to be safe to run more than once.
const fs = require('fs');
const path = require('path');
const pool = require('./db');

async function main() {
  const dir = path.join(__dirname, 'migrations');
  const files = fs.readdirSync(dir).filter((f) => f.endsWith('.sql')).sort();
  for (const file of files) {
    console.log(`Running ${file}...`);
    await pool.query(fs.readFileSync(path.join(dir, file), 'utf8'));
  }
  console.log('Migrations done.');
}

main()
  .catch((err) => {
    console.error('Migration failed:', err.message);
    process.exitCode = 1;
  })
  .finally(() => pool.end());