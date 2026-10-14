// Builds a full CRUD router (list, get one, create, update, delete) for one table.
// Each resource file (animals.js, shelters.js, ...) only describes its table,
// so the SQL logic is written once and reused four times.
const express = require('express');
const pool = require('../db');

function crudRouter(config) {
  const {
    table,          // real table name, e.g. 'animals'
    alias,          // alias used in selectSql, e.g. 'a'
    columns,        // columns the user is allowed to write
    selectSql,      // SELECT ... FROM ... JOIN ... (no WHERE)
    searchColumns,  // columns the ?search= text is matched against
    filters = {},   // ?param=value equality filters: { species: 'a.species' }
    orderBy,        // ORDER BY clause for lists
    label,          // human name for error messages, e.g. 'Animal'
    beforeWrite,    // optional: (data, before) => data   (adjust input before saving)
    afterWrite,     // optional: async ({ before, after }) => {}  (side effects)
  } = config;

  const router = express.Router();

  // Turn ":id" into a number, or answer 400 if it is not one.
  function parseId(req, res) {
    const id = Number.parseInt(req.params.id, 10);
    if (Number.isNaN(id)) {
      res.status(400).json({ error: 'id must be a number' });
      return null;
    }
    return id;
  }

  // Keep only allowed columns from the request body; '' becomes NULL.
  function pickColumns(body) {
    const data = {};
    for (const col of columns) {
      if (body[col] !== undefined) data[col] = body[col] === '' ? null : body[col];
    }
    return data;
  }

  async function findOne(id) {
    const { rows } = await pool.query(`${selectSql} WHERE ${alias}.id = $1`, [id]);
    return rows[0] || null;
  }

  async function findRaw(id) {
    const { rows } = await pool.query(`SELECT * FROM ${table} WHERE id = $1`, [id]);
    return rows[0] || null;
  }

  // GET /api/<resource>?page=1&limit=20&search=luna&species=dog
  router.get('/', async (req, res, next) => {
    try {
      const page = Math.max(1, Number.parseInt(req.query.page, 10) || 1);
      const limit = Math.min(100, Math.max(1, Number.parseInt(req.query.limit, 10) || 20));
      const where = [];
      const params = [];

      if (req.query.search && searchColumns.length) {
        params.push(`%${req.query.search}%`);
        where.push('(' + searchColumns.map((c) => `${c} ILIKE $${params.length}`).join(' OR ') + ')');
      }
      for (const [param, column] of Object.entries(filters)) {
        if (req.query[param] !== undefined && req.query[param] !== '') {
          params.push(req.query[param]);
          where.push(`${column} = $${params.length}`);
        }
      }

      const whereSql = where.length ? `WHERE ${where.join(' AND ')}` : '';
      const countResult = await pool.query(
        `SELECT COUNT(*)::int AS total FROM (${selectSql} ${whereSql}) AS sub`,
        params
      );

      params.push(limit, (page - 1) * limit);
      const { rows } = await pool.query(
        `${selectSql} ${whereSql} ORDER BY ${orderBy} LIMIT $${params.length - 1} OFFSET $${params.length}`,
        params
      );

      res.json({ data: rows, page, limit, total: countResult.rows[0].total });
    } catch (err) {
      next(err);
    }
  });

  // GET /api/<resource>/:id
  router.get('/:id', async (req, res, next) => {
    try {
      const id = parseId(req, res);
      if (id === null) return;
      const row = await findOne(id);
      if (!row) return res.status(404).json({ error: `${label} not found` });
      res.json(row);
    } catch (err) {
      next(err);
    }
  });

  // POST /api/<resource>
  router.post('/', async (req, res, next) => {
    try {
      let data = pickColumns(req.body);
      if (beforeWrite) data = beforeWrite(data, null);
      const cols = Object.keys(data);
      if (!cols.length) return res.status(400).json({ error: 'No fields to save' });

      const placeholders = cols.map((_, i) => `$${i + 1}`).join(', ');
      const { rows } = await pool.query(
        `INSERT INTO ${table} (${cols.join(', ')}) VALUES (${placeholders}) RETURNING id`,
        Object.values(data)
      );
      const after = await findRaw(rows[0].id);
      if (afterWrite) await afterWrite({ before: null, after });
      res.status(201).json(await findOne(rows[0].id));
    } catch (err) {
      next(err);
    }
  });

  // PUT /api/<resource>/:id
  router.put('/:id', async (req, res, next) => {
    try {
      const id = parseId(req, res);
      if (id === null) return;
      const before = await findRaw(id);
      if (!before) return res.status(404).json({ error: `${label} not found` });

      let data = pickColumns(req.body);
      if (beforeWrite) data = beforeWrite(data, before);
      const cols = Object.keys(data);
      if (!cols.length) return res.status(400).json({ error: 'No fields to update' });

      const setSql = cols.map((c, i) => `${c} = $${i + 1}`).join(', ');
      await pool.query(`UPDATE ${table} SET ${setSql} WHERE id = $${cols.length + 1}`, [
        ...Object.values(data),
        id,
      ]);
      const after = await findRaw(id);
      if (afterWrite) await afterWrite({ before, after });
      res.json(await findOne(id));
    } catch (err) {
      next(err);
    }
  });

  // DELETE /api/<resource>/:id
  router.delete('/:id', async (req, res, next) => {
    try {
      const id = parseId(req, res);
      if (id === null) return;
      const { rows } = await pool.query(`DELETE FROM ${table} WHERE id = $1 RETURNING *`, [id]);
      if (!rows.length) return res.status(404).json({ error: `${label} not found` });
      if (afterWrite) await afterWrite({ before: rows[0], after: null });
      res.status(204).end();
    } catch (err) {
      next(err);
    }
  });

  return router;
}

module.exports = crudRouter;
