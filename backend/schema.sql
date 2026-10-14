-- PawHome database schema
-- Running this file drops and recreates all tables (used by seed.js).

DROP TABLE IF EXISTS applications, animals, adopters, shelters CASCADE;

CREATE TABLE shelters (
  id          SERIAL PRIMARY KEY,
  name        VARCHAR(120) NOT NULL,
  city        VARCHAR(80)  NOT NULL,
  address     VARCHAR(200),
  phone       VARCHAR(30),
  email       VARCHAR(120),
  capacity    INTEGER CHECK (capacity > 0),
  created_at  TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE adopters (
  id             SERIAL PRIMARY KEY,
  first_name     VARCHAR(60)  NOT NULL,
  last_name      VARCHAR(60)  NOT NULL,
  email          VARCHAR(120) NOT NULL UNIQUE,
  phone          VARCHAR(30),
  city           VARCHAR(80),
  date_of_birth  DATE,
  has_garden     BOOLEAN NOT NULL DEFAULT false,
  created_at     TIMESTAMP NOT NULL DEFAULT now()
);

CREATE TABLE animals (
  id             SERIAL PRIMARY KEY,
  shelter_id     INTEGER NOT NULL REFERENCES shelters(id) ON DELETE CASCADE,
  name           VARCHAR(60) NOT NULL,
  species        VARCHAR(20) NOT NULL
                 CHECK (species IN ('dog', 'cat', 'rabbit', 'bird', 'guinea pig')),
  breed          VARCHAR(80),
  sex            CHAR(1) CHECK (sex IN ('M', 'F')),
  age_years      NUMERIC(4,1) CHECK (age_years >= 0),
  size           VARCHAR(10) CHECK (size IN ('small', 'medium', 'large')),
  is_vaccinated  BOOLEAN NOT NULL DEFAULT false,
  status         VARCHAR(20) NOT NULL DEFAULT 'available'
                 CHECK (status IN ('available', 'reserved', 'adopted')),
  arrived_at     DATE NOT NULL DEFAULT CURRENT_DATE,
  description    TEXT
);

CREATE TABLE applications (
  id            SERIAL PRIMARY KEY,
  animal_id     INTEGER NOT NULL REFERENCES animals(id)  ON DELETE CASCADE,
  adopter_id    INTEGER NOT NULL REFERENCES adopters(id) ON DELETE CASCADE,
  status        VARCHAR(20) NOT NULL DEFAULT 'pending'
                CHECK (status IN ('pending', 'approved', 'rejected', 'adopted')),
  message       TEXT,
  submitted_at  TIMESTAMP NOT NULL DEFAULT now(),
  decided_at    TIMESTAMP,
  CHECK (decided_at IS NULL OR decided_at >= submitted_at)
);

CREATE INDEX idx_animals_shelter      ON animals(shelter_id);
CREATE INDEX idx_animals_status       ON animals(status);
CREATE INDEX idx_applications_animal  ON applications(animal_id);
CREATE INDEX idx_applications_adopter ON applications(adopter_id);
