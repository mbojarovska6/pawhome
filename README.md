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

---

# Task 2 – Data lake (Silo + dlt)

| Service | URL | Login |
|---|---|---|
| Silo console (main lake) | http://localhost:9001 | `silo-admin` / `silo-password-123` |
| RustFS console (bonus lake) | http://localhost:9101 | `rustfs-admin` / `rustfs-password-123` |
| JupyterLab | http://localhost:8888 | token `pawhome` |

```bash
docker compose up -d --build                  # starts the app + silo + rustfs + jupyter
docker compose exec backend npm run migrate   # adds updated_at (needed for incremental loads)
```

Notebooks (in `lake/notebooks/`, shown as `work/` in JupyterLab):

| Notebook | Task part | Mode |
|---|---|---|
| `01_full_load_postgres.ipynb` | 2 – full load of all 4 tables | `replace` |
| `02_incremental_load_postgres.ipynb` | 3 – incremental load on `updated_at` (+ RustFS bonus) | `append` |
| `03_full_load_api.ipynb` | 4 – Dog CEO breeds API | `replace` |

Object keys: `<source_system>/<resource>/ingestion_date=<YYYY-MM-DD>/<load_id>.<file_id>.parquet`
Metadata columns: `_source_system`, `_source_resource`, `_ingestion_type`, `_ingested_at`, `_load_id`.
Shared settings and helpers: `lake/notebooks/lake.py`.

---

# Task 3 – Data pile (Apache Iceberg + SQL catalog)

The pile is a second bucket, `pawhome-pile`, in Silo (and in RustFS for the bonus). It holds **Iceberg tables**. A PyIceberg **SQL catalog** (a SQLite file in `lake/notebooks/pile_catalog/`) keeps the list of tables.

```bash
docker compose up -d --build jupyter   # rebuild JupyterLab once (adds PyIceberg)
```

| Notebook | Task part | What |
|---|---|---|
| `04_pile_setup.ipynb` | 1 | pile bucket, SQL catalog (SQLite), namespace `bronze` (+ RustFS bonus) |
| `05_bronze_incremental_postgres.ipynb` | 2 + 3 | incremental `append` into `bronze.postgres_*`, PyIceberg checks, snapshots / time travel (+ RustFS bonus) |
| `06_bronze_api_schema_evolution.ipynb` | 2 + 3 | Dog CEO API `replace` into `bronze.dogceo_breeds`, schema evolution |

- Medallion zone = Iceberg namespace `bronze`. Tables: `bronze.postgres_<table>`, `bronze.dogceo_breeds`.
- Object keys: `bronze/<table>/data/ingestion_date=<YYYY-MM-DD>/<file>.parquet` and `bronze/<table>/metadata/...`
- Partitioning: `ingestion_date = day(_ingested_at)`.
- Shared settings and helpers: `lake/notebooks/pile.py`.
