// Seed script: recreates the tables and fills them with ~10,000 realistic rows.
// Run with:  npm run seed
const fs = require('fs');
const path = require('path');
const { faker } = require('@faker-js/faker');
const pool = require('./db');

faker.seed(42); // same data on every run

const COUNTS = { shelters: 50, adopters: 2000, animals: 3000, applications: 5000 };
const NOW = new Date();
const DAY = 24 * 60 * 60 * 1000;

const toDate = (d) => d.toISOString().slice(0, 10); // 'YYYY-MM-DD'

// Insert many rows with one INSERT per batch of 500 (much faster than one by one).
async function insertMany(client, table, columns, rows) {
  const ids = [];
  for (let i = 0; i < rows.length; i += 500) {
    const batch = rows.slice(i, i + 500);
    const values = [];
    const tuples = batch.map((row, r) => {
      const ph = row.map((value, c) => {
        values.push(value);
        return `$${r * columns.length + c + 1}`;
      });
      return `(${ph.join(', ')})`;
    });
    const { rows: inserted } = await client.query(
      `INSERT INTO ${table} (${columns.join(', ')}) VALUES ${tuples.join(', ')} RETURNING id`,
      values
    );
    ids.push(...inserted.map((x) => x.id));
  }
  return ids;
}

// ---------- generators ----------

function makeShelter() {
  const city = faker.location.city();
  const slug = city.toLowerCase().replace(/[^a-z]/g, '');
  return [
    `${city} Animal Shelter`,
    city,
    faker.location.streetAddress(),
    faker.phone.number({ style: 'international' }),
    `info@${slug}-shelter.org`,
    faker.number.int({ min: 20, max: 150 }),
    faker.date.past({ years: 8 }),
  ];
}

function makeAdopter(i) {
  const first = faker.person.firstName();
  const last = faker.person.lastName();
  const clean = (s) => s.toLowerCase().replace(/[^a-z]/g, '');
  return [
    first,
    last,
    `${clean(first)}.${clean(last)}${i}@example.com`, // index keeps emails unique
    faker.phone.number({ style: 'international' }),
    faker.location.city(),
    toDate(faker.date.birthdate({ mode: 'age', min: 18, max: 75 })),
    faker.datatype.boolean({ probability: 0.4 }),
    faker.date.past({ years: 3 }),
  ];
}

const GUINEA_PIG_BREEDS = ['Abyssinian', 'American', 'Peruvian', 'Teddy', 'Silkie', 'Texel', 'Skinny'];

const SPECIES = [
  { weight: 45, value: 'dog' },
  { weight: 35, value: 'cat' },
  { weight: 10, value: 'rabbit' },
  { weight: 6, value: 'guinea pig' },
  { weight: 4, value: 'bird' },
];

function breedFor(species) {
  switch (species) {
    case 'dog': return faker.animal.dog();
    case 'cat': return faker.animal.cat();
    case 'rabbit': return faker.animal.rabbit();
    case 'bird': return faker.animal.bird();
    default: return faker.helpers.arrayElement(GUINEA_PIG_BREEDS);
  }
}

function sizeFor(species) {
  if (species === 'dog') return faker.helpers.arrayElement(['small', 'medium', 'large']);
  if (species === 'cat') return faker.helpers.arrayElement(['small', 'medium']);
  return 'small';
}

function ageFor(species) {
  const max = { dog: 15, cat: 16, rabbit: 9, bird: 8, 'guinea pig': 6 }[species];
  return faker.number.float({ min: 0.2, max, fractionDigits: 1 });
}

const TRAITS = [
  'Friendly and calm', 'Very playful', 'Shy at first', 'Good with children',
  'Gets along with other pets', 'Loves cuddles', 'Needs an experienced owner',
  'Very energetic', 'House-trained', 'Enjoys long walks', 'Quiet and independent',
];

function makeAnimal(shelterIds) {
  const species = faker.helpers.weightedArrayElement(SPECIES);
  return [
    faker.helpers.arrayElement(shelterIds),
    faker.animal.petName(),
    species,
    breedFor(species).slice(0, 80),
    faker.helpers.arrayElement(['M', 'F']),
    ageFor(species),
    sizeFor(species),
    faker.datatype.boolean({ probability: 0.75 }),
    'available', // corrected after applications are created
    toDate(faker.date.past({ years: 2 })),
    faker.helpers.arrayElements(TRAITS, { min: 1, max: 3 }).join('. ') + '.',
  ];
}

const MESSAGES = [
  'We have a big garden and lots of time for walks.',
  'I work from home and would love a companion.',
  'Our family has had pets before and we are ready for another.',
  'Looking for a calm friend for my apartment.',
  'My kids have been asking for a pet for years.',
  'I have experience with this breed.',
  'We recently moved to a house and finally have space.',
];

const APP_STATUS = [
  { weight: 60, value: 'pending' },
  { weight: 20, value: 'approved' },
  { weight: 15, value: 'rejected' },
  { weight: 5, value: 'adopted' },
];

function makeApplications(animals, adopterIds) {
  const taken = new Set(); // an animal can only be approved/adopted once
  const rows = [];
  for (let i = 0; i < COUNTS.applications; i++) {
    const animal = faker.helpers.arrayElement(animals);
    let status = faker.helpers.weightedArrayElement(APP_STATUS);
    if ((status === 'approved' || status === 'adopted') && taken.has(animal.id)) status = 'rejected';
    if (status === 'approved' || status === 'adopted') taken.add(animal.id);

    // submitted after the animal arrived, decided 1-14 days later (never in the future)
    const arrived = new Date(animal.arrived_at);
    const submitted = faker.date.between({ from: arrived, to: NOW });
    let decided = null;
    if (status !== 'pending') {
      decided = new Date(Math.min(submitted.getTime() + faker.number.int({ min: 1, max: 14 }) * DAY, NOW.getTime()));
    }

    rows.push([
      animal.id,
      faker.helpers.arrayElement(adopterIds),
      status,
      faker.helpers.arrayElement(MESSAGES),
      submitted,
      decided,
    ]);
  }
  return rows;
}

// ---------- main ----------

async function main() {
  const client = await pool.connect();
  try {
    await client.query('BEGIN');
    console.log('Creating tables...');
    await client.query(fs.readFileSync(path.join(__dirname, 'schema.sql'), 'utf8'));

    console.log('Inserting shelters...');
    const shelterIds = await insertMany(
      client, 'shelters',
      ['name', 'city', 'address', 'phone', 'email', 'capacity', 'created_at'],
      Array.from({ length: COUNTS.shelters }, makeShelter)
    );

    console.log('Inserting adopters...');
    const adopterIds = await insertMany(
      client, 'adopters',
      ['first_name', 'last_name', 'email', 'phone', 'city', 'date_of_birth', 'has_garden', 'created_at'],
      Array.from({ length: COUNTS.adopters }, (_, i) => makeAdopter(i + 1))
    );

    console.log('Inserting animals...');
    const animalRows = Array.from({ length: COUNTS.animals }, () => makeAnimal(shelterIds));
    const animalIds = await insertMany(
      client, 'animals',
      ['shelter_id', 'name', 'species', 'breed', 'sex', 'age_years', 'size',
       'is_vaccinated', 'status', 'arrived_at', 'description'],
      animalRows
    );
    const animals = animalIds.map((id, i) => ({ id, arrived_at: animalRows[i][9] }));

    console.log('Inserting applications...');
    await insertMany(
      client, 'applications',
      ['animal_id', 'adopter_id', 'status', 'message', 'submitted_at', 'decided_at'],
      makeApplications(animals, adopterIds)
    );

    console.log('Syncing animal status with applications...');
    await client.query(`
      UPDATE animals SET status = CASE
        WHEN EXISTS (SELECT 1 FROM applications ap WHERE ap.animal_id = animals.id AND ap.status = 'adopted')  THEN 'adopted'
        WHEN EXISTS (SELECT 1 FROM applications ap WHERE ap.animal_id = animals.id AND ap.status = 'approved') THEN 'reserved'
        ELSE 'available' END`);

    await client.query('COMMIT');

    console.log('\nDone. Rows per table:');
    let total = 0;
    for (const t of ['shelters', 'adopters', 'animals', 'applications']) {
      const { rows } = await client.query(`SELECT COUNT(*)::int AS n FROM ${t}`);
      total += rows[0].n;
      console.log(`  ${t.padEnd(14)} ${rows[0].n}`);
    }
    console.log(`  ${'TOTAL'.padEnd(14)} ${total}`);
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('Seeding failed, nothing was saved:', err.message);
    process.exitCode = 1;
  } finally {
    client.release();
    await pool.end();
  }
}

main();
