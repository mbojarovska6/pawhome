# 🐾 PawHome – Pet Adoption Shelter

Task 1 for Data Technologies and Services: a web application with a database that serves as the base system for later tasks.

Shelters list animals, people register as adopters, and adopters apply to adopt animals.

| Layer | Technology |
| --- | --- |
| Frontend | Vue 3 + Vite, Vue Router, axios |
| Backend | Node.js + Express, `pg` |
| Database | PostgreSQL 16 (Docker, named volume) |
| Seed data | `@faker-js/faker` – 10,050 rows |

## Run it

Requirements: Docker Desktop.

```bash
docker compose up -d --build              # start database, backend, frontend
docker compose exec backend npm run seed  # create tables + insert 10,050 rows
```

- App: http://localhost:5173
- API: http://localhost:3000/api/animals

Stop with `docker compose down` (data is kept). `docker compose down -v` also deletes the data.

## Database

| Table | Rows | Relationships |
| --- | --- | --- |
| shelters | 50 | has many animals |
| adopters | 2,000 | has many applications |
| animals | 3,000 | belongs to a shelter, has many applications |
| applications | 5,000 | belongs to an animal and an adopter (junction table → many-to-many) |

Schema: `backend/schema.sql`. Seed: `backend/seed.js`.

Check the row counts:

```bash
docker compose exec db psql -U pawhome -c "SELECT COUNT(*) FROM applications;"
```

## API

Each resource (`shelters`, `animals`, `adopters`, `applications`) has:

| Method | Route | Purpose |
| --- | --- | --- |
| GET | `/api/<resource>?page=1&limit=20&search=` | list (paginated, searchable, filterable) |
| GET | `/api/<resource>/:id` | one record |
| POST | `/api/<resource>` | create |
| PUT | `/api/<resource>/:id` | update |
| DELETE | `/api/<resource>/:id` | delete |

Plus `GET /api/stats` (row counts) and `GET /api/health`.

Changing an application's status also updates the animal: `approved` → animal `reserved`, `adopted` → animal `adopted`.

## Run without Docker (development)

```bash
docker compose up -d db                    # only the database
cd backend  && npm install && npm run seed && npm start
cd frontend && npm install && npm run dev
```
