import { createServer as createHttpServer } from 'node:http';
import { readFile, writeFile, mkdir } from 'node:fs/promises';
import { existsSync } from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));
const DEFAULT_DATA_FILE = path.join(__dirname, 'data', 'tasks.json');
const DEFAULT_PUBLIC_DIR = path.join(__dirname, 'public');
const JSON_LIMIT_BYTES = 64 * 1024;

const MIME_TYPES = new Map([
  ['.html', 'text/html; charset=utf-8'],
  ['.css', 'text/css; charset=utf-8'],
  ['.js', 'text/javascript; charset=utf-8'],
  ['.json', 'application/json; charset=utf-8'],
  ['.svg', 'image/svg+xml; charset=utf-8']
]);

function send(res, status, body, headers = {}) {
  res.writeHead(status, headers);
  res.end(body);
}

function sendJson(res, status, payload) {
  send(res, status, JSON.stringify(payload, null, 2), {
    'content-type': 'application/json; charset=utf-8',
    'cache-control': 'no-store'
  });
}

function safeJsonParse(text) {
  try {
    return [JSON.parse(text), null];
  } catch (error) {
    return [null, error];
  }
}

async function readBody(req) {
  let size = 0;
  const chunks = [];
  for await (const chunk of req) {
    size += chunk.length;
    if (size > JSON_LIMIT_BYTES) {
      const error = new Error('request body too large');
      error.status = 413;
      throw error;
    }
    chunks.push(chunk);
  }
  return Buffer.concat(chunks).toString('utf8');
}

async function ensureDataFile(dataFile) {
  await mkdir(path.dirname(dataFile), { recursive: true });
  if (!existsSync(dataFile)) {
    await writeFile(dataFile, '[]\n', 'utf8');
  }
}

async function loadTasks(dataFile) {
  await ensureDataFile(dataFile);
  const text = await readFile(dataFile, 'utf8');
  const [tasks, error] = safeJsonParse(text);
  if (error || !Array.isArray(tasks)) {
    const parseError = new Error('data file must contain a JSON array');
    parseError.status = 500;
    throw parseError;
  }
  return tasks;
}

async function saveTasks(dataFile, tasks) {
  await mkdir(path.dirname(dataFile), { recursive: true });
  await writeFile(dataFile, `${JSON.stringify(tasks, null, 2)}\n`, 'utf8');
}

function normalizeTitle(title) {
  if (typeof title !== 'string') {
    return '';
  }
  return title.trim().replace(/\s+/g, ' ');
}

function nextId(tasks) {
  return tasks.reduce((max, task) => Math.max(max, Number(task.id) || 0), 0) + 1;
}

function taskSummary(tasks) {
  const done = tasks.filter((task) => task.done).length;
  return { total: tasks.length, done, active: tasks.length - done };
}

async function handleApi(req, res, url, dataFile) {
  const segments = url.pathname.split('/').filter(Boolean);
  const id = segments.length === 3 && segments[0] === 'api' && segments[1] === 'tasks' ? Number(segments[2]) : null;

  if (url.pathname === '/api/health' && req.method === 'GET') {
    sendJson(res, 200, { ok: true, app: 'minimal-web-fullstack-lab' });
    return;
  }

  if (url.pathname === '/api/tasks' && req.method === 'GET') {
    const tasks = await loadTasks(dataFile);
    sendJson(res, 200, { tasks, summary: taskSummary(tasks) });
    return;
  }

  if (url.pathname === '/api/tasks' && req.method === 'POST') {
    const bodyText = await readBody(req);
    const [payload, parseError] = safeJsonParse(bodyText || '{}');
    if (parseError) {
      sendJson(res, 400, { error: 'invalid_json', message: 'Request body must be JSON.' });
      return;
    }
    const title = normalizeTitle(payload.title);
    if (title.length < 1 || title.length > 80) {
      sendJson(res, 400, { error: 'invalid_title', message: 'Title length must be between 1 and 80 characters.' });
      return;
    }
    const tasks = await loadTasks(dataFile);
    const task = { id: nextId(tasks), title, done: false };
    tasks.push(task);
    await saveTasks(dataFile, tasks);
    sendJson(res, 201, { task, summary: taskSummary(tasks) });
    return;
  }

  if (id && segments.length === 3 && req.method === 'PATCH') {
    const bodyText = await readBody(req);
    const [payload, parseError] = safeJsonParse(bodyText || '{}');
    if (parseError || typeof payload.done !== 'boolean') {
      sendJson(res, 400, { error: 'invalid_done', message: 'PATCH body must be JSON with a boolean done field.' });
      return;
    }
    const tasks = await loadTasks(dataFile);
    const task = tasks.find((item) => item.id === id);
    if (!task) {
      sendJson(res, 404, { error: 'not_found', message: `Task ${id} does not exist.` });
      return;
    }
    task.done = payload.done;
    await saveTasks(dataFile, tasks);
    sendJson(res, 200, { task, summary: taskSummary(tasks) });
    return;
  }

  if (id && segments.length === 3 && req.method === 'DELETE') {
    const tasks = await loadTasks(dataFile);
    const kept = tasks.filter((task) => task.id !== id);
    if (kept.length === tasks.length) {
      sendJson(res, 404, { error: 'not_found', message: `Task ${id} does not exist.` });
      return;
    }
    await saveTasks(dataFile, kept);
    sendJson(res, 200, { deleted: id, summary: taskSummary(kept) });
    return;
  }

  if (url.pathname.startsWith('/api/')) {
    sendJson(res, 404, { error: 'not_found', message: 'API route not found.' });
    return;
  }
}

async function serveStatic(req, res, url, publicDir) {
  if (!['GET', 'HEAD'].includes(req.method)) {
    send(res, 405, 'Method Not Allowed\n', { 'content-type': 'text/plain; charset=utf-8' });
    return;
  }
  const rawPath = decodeURIComponent(url.pathname === '/' ? '/index.html' : url.pathname);
  const candidate = path.normalize(path.join(publicDir, rawPath));
  const publicRoot = path.resolve(publicDir);
  if (!candidate.startsWith(`${publicRoot}${path.sep}`) && candidate !== publicRoot) {
    send(res, 403, 'Forbidden\n', { 'content-type': 'text/plain; charset=utf-8' });
    return;
  }
  try {
    const body = await readFile(candidate);
    const type = MIME_TYPES.get(path.extname(candidate)) || 'application/octet-stream';
    send(res, 200, req.method === 'HEAD' ? '' : body, { 'content-type': type });
  } catch (error) {
    if (error.code === 'ENOENT' || error.code === 'EISDIR') {
      send(res, 404, 'Not Found\n', { 'content-type': 'text/plain; charset=utf-8' });
      return;
    }
    throw error;
  }
}

export function createApp(options = {}) {
  const dataFile = options.dataFile || process.env.TASKS_DATA_FILE || DEFAULT_DATA_FILE;
  const publicDir = options.publicDir || DEFAULT_PUBLIC_DIR;
  return createHttpServer(async (req, res) => {
    try {
      const url = new URL(req.url || '/', 'http://localhost');
      if (url.pathname.startsWith('/api/')) {
        await handleApi(req, res, url, dataFile);
        return;
      }
      await serveStatic(req, res, url, publicDir);
    } catch (error) {
      const status = Number(error.status) || 500;
      sendJson(res, status, { error: 'server_error', message: error.message });
    }
  });
}

export function startServer(options = {}) {
  const host = options.host || process.env.HOST || '127.0.0.1';
  const port = Number(options.port ?? process.env.PORT ?? 3000);
  const server = createApp(options);
  server.listen(port, host, () => {
    const address = server.address();
    const actualPort = typeof address === 'object' && address ? address.port : port;
    console.log(`server_url=http://${host}:${actualPort}`);
    console.log(`data_file=${options.dataFile || process.env.TASKS_DATA_FILE || DEFAULT_DATA_FILE}`);
  });
  return server;
}

if (process.argv[1] && fileURLToPath(import.meta.url) === path.resolve(process.argv[1])) {
  startServer();
}
