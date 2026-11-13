'use strict';

const http = require('node:http');
const fs = require('node:fs');
const os = require('node:os');
const path = require('node:path');

const PORT = Number(process.env.PORT) || 8000;
const ROOT = __dirname;
const PUBLIC_DIR = path.join(ROOT, 'public');
const MAX_BODY = 2 * 1024 * 1024;

function resolveDataFile() {
  const candidates = [path.join(ROOT, 'data'), path.join(os.tmpdir(), 'cloud-db')];
  for (const dir of candidates) {
    try {
      fs.mkdirSync(dir, { recursive: true });
      const probe = path.join(dir, '.write-test');
      fs.writeFileSync(probe, '');
      fs.unlinkSync(probe);
      return path.join(dir, 'db.json');
    } catch {
      // try the next writable location
    }
  }
  console.warn('[db] no writable data directory, running in memory only');
  return null;
}

const DATA_FILE = resolveDataFile();
const DATA_DIR = DATA_FILE ? path.dirname(DATA_FILE) : null;
let memoryOnly = DATA_FILE === null;

const MIME = {
  '.html': 'text/html; charset=utf-8',
  '.css': 'text/css; charset=utf-8',
  '.js': 'text/javascript; charset=utf-8',
  '.json': 'application/json; charset=utf-8',
  '.svg': 'image/svg+xml',
  '.png': 'image/png',
  '.ico': 'image/x-icon',
};

function nowISO() {
  return new Date().toISOString();
}

function seedData() {
  const t = nowISO();
  return {
    version: 1,
    seq: 4,
    tables: [
      {
        name: 'novel_outlines',
        created_at: t,
        columns: [
          { name: 'title', type: 'text' },
          { name: 'genre', type: 'text' },
          { name: 'status', type: 'text' },
          { name: 'summary', type: 'text' },
        ],
        rows: [
          {
            _id: 1,
            title: '长夜行舟',
            genre: '东方幻想',
            status: '连载中',
            summary: '少年在永夜之城寻找失踪的师父，意外卷入守夜人与旧神之间的百年契约。',
            created_at: t,
            updated_at: t,
          },
          {
            _id: 2,
            title: '第七次落日',
            genre: '科幻悬疑',
            status: '大纲',
            summary: '太阳每七天熄灭一次，小镇居民靠记忆换取光明，主角发现自己的记忆被人为篡改。',
            created_at: t,
            updated_at: t,
          },
          {
            _id: 3,
            title: '山海食堂',
            genre: '都市奇谈',
            status: '已完成',
            summary: '深夜食堂的老板娘能听懂妖怪的乡愁，每碗面都对应一段未了的心愿。',
            created_at: t,
            updated_at: t,
          },
        ],
      },
    ],
  };
}

let db = null;

function loadDB() {
  if (memoryOnly) {
    db = seedData();
    return;
  }
  try {
    const raw = fs.readFileSync(DATA_FILE, 'utf8');
    const parsed = JSON.parse(raw);
    if (!parsed || !Array.isArray(parsed.tables)) throw new Error('bad data');
    db = parsed;
  } catch (err) {
    if (err.code !== 'ENOENT') console.error('[db] reset:', err.message);
    db = seedData();
    saveDB();
  }
}

function saveDB() {
  if (memoryOnly || !DATA_FILE) return;
  try {
    fs.mkdirSync(DATA_DIR, { recursive: true });
    const tmp = DATA_FILE + '.tmp';
    fs.writeFileSync(tmp, JSON.stringify(db, null, 2));
    fs.renameSync(tmp, DATA_FILE);
  } catch (err) {
    console.error('[db] persist failed, switching to memory only:', err.message);
    memoryOnly = true;
  }
}

function sendJSON(res, status, data) {
  const body = JSON.stringify(data);
  res.writeHead(status, {
    'Content-Type': 'application/json; charset=utf-8',
    'Cache-Control': 'no-store',
  });
  res.end(body);
}

function readBody(req) {
  return new Promise((resolve, reject) => {
    let size = 0;
    const chunks = [];
    req.on('data', (chunk) => {
      size += chunk.length;
      if (size > MAX_BODY) {
        reject(Object.assign(new Error('请求体过大'), { status: 413 }));
        req.destroy();
        return;
      }
      chunks.push(chunk);
    });
    req.on('end', () => {
      if (!chunks.length) return resolve({});
      try {
        resolve(JSON.parse(Buffer.concat(chunks).toString('utf8')));
      } catch {
        reject(Object.assign(new Error('JSON 格式错误'), { status: 400 }));
      }
    });
    req.on('error', reject);
  });
}

function validName(name) {
  return typeof name === 'string' && /^[\w\u4e00-\u9fa5-]{1,40}$/.test(name);
}

function findTable(name) {
  return db.tables.find((t) => t.name === name);
}

function cleanValue(value) {
  if (value === null || value === undefined) return '';
  if (typeof value === 'number' || typeof value === 'boolean') return value;
  return String(value).slice(0, 20000);
}

function normalizeRow(input, columns) {
  const row = {};
  for (const col of columns) {
    row[col.name] = cleanValue(input[col.name]);
  }
  return row;
}

function rowsFor(table, query) {
  const q = (query || '').trim().toLowerCase();
  const rows = q
    ? table.rows.filter((row) =>
        table.columns.some((col) => String(row[col.name] ?? '').toLowerCase().includes(q))
      )
    : table.rows.slice();
  return rows.sort((a, b) => String(b.updated_at).localeCompare(String(a.updated_at)));
}

async function handleAPI(req, res, url) {
  const parts = url.pathname.split('/').filter(Boolean); // api, ...
  const method = req.method;

  if (parts[0] !== 'api') return false;

  // GET /api/state
  if (parts[1] === 'state' && method === 'GET') {
    sendJSON(res, 200, {
      tables: db.tables.map((t) => ({
        name: t.name,
        count: t.rows.length,
        columns: t.columns,
      })),
    });
    return true;
  }

  // GET /api/export
  if (parts[1] === 'export' && method === 'GET') {
    const body = JSON.stringify(db, null, 2);
    res.writeHead(200, {
      'Content-Type': 'application/json; charset=utf-8',
      'Content-Disposition': `attachment; filename="cloud-db-${Date.now()}.json"`,
      'Cache-Control': 'no-store',
    });
    res.end(body);
    return true;
  }

  // POST /api/import
  if (parts[1] === 'import' && method === 'POST') {
    const body = await readBody(req);
    if (!body || !Array.isArray(body.tables)) {
      sendJSON(res, 400, { error: '备份文件格式不正确' });
      return true;
    }
    db = {
      version: 1,
      seq: Number(body.seq) || 1,
      tables: body.tables
        .filter((t) => t && validName(t.name) && Array.isArray(t.columns) && Array.isArray(t.rows))
        .map((t) => ({
          name: t.name,
          created_at: t.created_at || nowISO(),
          columns: t.columns
            .filter((c) => c && validName(c.name))
            .map((c) => ({ name: c.name, type: c.type === 'number' ? 'number' : 'text' })),
          rows: t.rows,
        })),
    };
    if (!db.tables.length) db = seedData();
    saveDB();
    sendJSON(res, 200, { ok: true, tables: db.tables.length });
    return true;
  }

  // /api/tables
  if (parts[1] === 'tables' && parts.length === 2) {
    if (method === 'POST') {
      const body = await readBody(req);
      const name = String(body.name || '').trim();
      if (!validName(name)) {
        sendJSON(res, 400, { error: '表名只能包含中英文、数字、下划线或短横线（1-40 字）' });
        return true;
      }
      if (findTable(name)) {
        sendJSON(res, 409, { error: '已存在同名数据表' });
        return true;
      }
      const rawCols = Array.isArray(body.columns) ? body.columns : [];
      const seen = new Set();
      const columns = [];
      for (const c of rawCols) {
        const colName = String((c && c.name) || '').trim();
        if (!validName(colName) || seen.has(colName)) continue;
        seen.add(colName);
        columns.push({ name: colName, type: c.type === 'number' ? 'number' : 'text' });
      }
      if (!columns.length) {
        sendJSON(res, 400, { error: '至少需要一个字段' });
        return true;
      }
      db.tables.push({ name, created_at: nowISO(), columns, rows: [] });
      saveDB();
      sendJSON(res, 200, { ok: true, name });
      return true;
    }
    if (method === 'GET') {
      sendJSON(res, 200, { tables: db.tables.map((t) => ({ name: t.name, count: t.rows.length })) });
      return true;
    }
  }

  // /api/tables/:name
  if (parts[1] === 'tables' && parts.length >= 3) {
    const name = decodeURIComponent(parts[2]);

    if (parts.length === 3) {
      const table = findTable(name);
      if (!table) {
        sendJSON(res, 404, { error: '数据表不存在' });
        return true;
      }
      if (method === 'GET') {
        sendJSON(res, 200, {
          name: table.name,
          columns: table.columns,
          total: table.rows.length,
          rows: rowsFor(table, url.searchParams.get('q')),
        });
        return true;
      }
      if (method === 'PATCH') {
        const body = await readBody(req);
        const colName = String((body.addColumn && body.addColumn.name) || '').trim();
        if (!validName(colName)) {
          sendJSON(res, 400, { error: '字段名不合法' });
          return true;
        }
        if (table.columns.some((c) => c.name === colName)) {
          sendJSON(res, 409, { error: '字段已存在' });
          return true;
        }
        const type = body.addColumn.type === 'number' ? 'number' : 'text';
        table.columns.push({ name: colName, type });
        for (const row of table.rows) row[colName] = type === 'number' ? '' : '';
        saveDB();
        sendJSON(res, 200, { ok: true });
        return true;
      }
      if (method === 'DELETE') {
        db.tables = db.tables.filter((t) => t.name !== name);
        saveDB();
        sendJSON(res, 200, { ok: true });
        return true;
      }
    }

    // /api/tables/:name/rows
    if (parts[3] === 'rows' && parts.length === 4) {
      const table = findTable(name);
      if (!table) {
        sendJSON(res, 404, { error: '数据表不存在' });
        return true;
      }
      if (method === 'POST') {
        const body = await readBody(req);
        db.seq += 1;
        const stamp = nowISO();
        const row = Object.assign(
          { _id: db.seq },
          normalizeRow(body.values || body, table.columns),
          { created_at: stamp, updated_at: stamp }
        );
        table.rows.push(row);
        saveDB();
        sendJSON(res, 200, { ok: true, row });
        return true;
      }
    }

    // /api/tables/:name/rows/:id
    if (parts[3] === 'rows' && parts.length === 5) {
      const table = findTable(name);
      if (!table) {
        sendJSON(res, 404, { error: '数据表不存在' });
        return true;
      }
      const id = Number(parts[4]);
      const idx = table.rows.findIndex((r) => r._id === id);
      if (idx === -1) {
        sendJSON(res, 404, { error: '记录不存在' });
        return true;
      }
      if (method === 'PUT') {
        const body = await readBody(req);
        table.rows[idx] = Object.assign(
          {},
          table.rows[idx],
          normalizeRow(body.values || body, table.columns),
          { updated_at: nowISO() }
        );
        saveDB();
        sendJSON(res, 200, { ok: true, row: table.rows[idx] });
        return true;
      }
      if (method === 'DELETE') {
        table.rows.splice(idx, 1);
        saveDB();
        sendJSON(res, 200, { ok: true });
        return true;
      }
    }
  }

  sendJSON(res, 404, { error: '接口不存在' });
  return true;
}

function serveStatic(req, res, url) {
  let pathname = decodeURIComponent(url.pathname);
  if (pathname === '/') pathname = '/index.html';
  const filePath = path.join(PUBLIC_DIR, path.normalize(pathname).replace(/^(\.\.[/\\])+/, ''));
  if (!filePath.startsWith(PUBLIC_DIR)) {
    res.writeHead(403);
    res.end('Forbidden');
    return;
  }
  fs.readFile(filePath, (err, data) => {
    if (err) {
      fs.readFile(path.join(PUBLIC_DIR, 'index.html'), (e2, fallback) => {
        if (e2) {
          res.writeHead(404);
          res.end('Not Found');
          return;
        }
        res.writeHead(200, { 'Content-Type': MIME['.html'] });
        res.end(fallback);
      });
      return;
    }
    const ext = path.extname(filePath).toLowerCase();
    res.writeHead(200, {
      'Content-Type': MIME[ext] || 'application/octet-stream',
      'Cache-Control': ext === '.html' ? 'no-cache' : 'public, max-age=3600',
    });
    res.end(data);
  });
}

loadDB();

const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, 'http://localhost');
  if (url.pathname.startsWith('/api/')) {
    try {
      const handled = await handleAPI(req, res, url);
      if (!handled) sendJSON(res, 404, { error: '接口不存在' });
    } catch (err) {
      console.error('[api]', err);
      if (!res.headersSent) {
        sendJSON(res, err.status || 500, { error: err.status ? err.message : '服务器内部错误' });
      }
    }
    return;
  }
  serveStatic(req, res, url);
});

server.listen(PORT, '0.0.0.0', () => {
  console.log(`cloud database server listening on ${PORT}`);
});
