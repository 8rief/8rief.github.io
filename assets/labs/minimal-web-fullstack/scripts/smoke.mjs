import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';
import { createApp } from '../server.mjs';

const dataFile = process.argv[2] || path.join('.lab_tmp', 'data', 'tasks.json');
const reportDir = process.argv[3] || 'reports';
await mkdir(reportDir, { recursive: true });

const events = [];
function record(step, data) {
  events.push({ step, ...data });
  console.log(`${step}=${JSON.stringify(data)}`);
}

async function request(base, route, options = {}) {
  const response = await fetch(`${base}${route}`, {
    headers: { 'content-type': 'application/json', ...(options.headers || {}) },
    ...options
  });
  const contentType = response.headers.get('content-type') || '';
  const body = contentType.includes('application/json') ? await response.json() : await response.text();
  record('http', { method: options.method || 'GET', route, status: response.status });
  return { response, body };
}

const server = createApp({ dataFile });
await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
const address = server.address();
const base = `http://127.0.0.1:${address.port}`;
record('server', { url: base, dataFile });

try {
  let result = await request(base, '/api/health');
  if (!result.body.ok) throw new Error('health check failed');

  result = await request(base, '/');
  if (!String(result.body).includes('任务面板')) throw new Error('HTML page missing expected title');

  result = await request(base, '/api/tasks');
  const initialCount = result.body.summary.total;
  if (initialCount !== 2) throw new Error(`expected 2 seed tasks, got ${initialCount}`);

  result = await request(base, '/api/tasks', {
    method: 'POST',
    body: JSON.stringify({ title: '从页面新增一个任务' })
  });
  const createdId = result.body.task.id;
  if (result.response.status !== 201 || createdId !== 3) throw new Error('create task failed');

  result = await request(base, `/api/tasks/${createdId}`, {
    method: 'PATCH',
    body: JSON.stringify({ done: true })
  });
  if (result.body.task.done !== true) throw new Error('patch task failed');

  result = await request(base, '/api/tasks', {
    method: 'POST',
    body: JSON.stringify({ title: '' })
  });
  if (result.response.status !== 400 || result.body.error !== 'invalid_title') throw new Error('invalid title check failed');

  result = await request(base, `/api/tasks/${createdId}`, { method: 'DELETE' });
  if (result.body.summary.total !== 2) throw new Error('delete task failed');

  result = await request(base, '/api/tasks');
  const finalSummary = result.body.summary;
  if (finalSummary.total !== 2 || finalSummary.done !== 1 || finalSummary.active !== 1) {
    throw new Error('final summary mismatch');
  }

  const smokeReport = {
    server_url: base,
    initial_count: initialCount,
    created_id: createdId,
    invalid_title_status: 400,
    final_summary: finalSummary,
    smoke_status: 'ok'
  };
  await writeFile(path.join(reportDir, 'smoke-report.json'), `${JSON.stringify(smokeReport, null, 2)}\n`, 'utf8');
  await writeFile(path.join(reportDir, 'api-transcript.ndjson'), events.map((event) => JSON.stringify(event)).join('\n') + '\n', 'utf8');
  console.log(`initial_count=${initialCount}`);
  console.log(`created_id=${createdId}`);
  console.log(`final_total=${finalSummary.total}`);
  console.log('smoke_status=ok');
} finally {
  await new Promise((resolve) => server.close(resolve));
}
