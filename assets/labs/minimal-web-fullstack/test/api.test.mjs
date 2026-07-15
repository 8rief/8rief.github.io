import test from 'node:test';
import assert from 'node:assert/strict';
import { mkdtemp, rm, writeFile } from 'node:fs/promises';
import os from 'node:os';
import path from 'node:path';
import { createApp } from '../server.mjs';

async function withServer(seedTasks, fn) {
  const dir = await mkdtemp(path.join(os.tmpdir(), 'minimal-web-fullstack-'));
  const dataFile = path.join(dir, 'tasks.json');
  await writeFile(dataFile, `${JSON.stringify(seedTasks, null, 2)}\n`, 'utf8');
  const server = createApp({ dataFile, publicDir: path.resolve('public') });
  await new Promise((resolve) => server.listen(0, '127.0.0.1', resolve));
  const address = server.address();
  const base = `http://127.0.0.1:${address.port}`;
  try {
    await fn(base);
  } finally {
    await new Promise((resolve) => server.close(resolve));
    await rm(dir, { recursive: true, force: true });
  }
}

async function json(base, route, options = {}) {
  const response = await fetch(`${base}${route}`, {
    headers: { 'content-type': 'application/json', ...(options.headers || {}) },
    ...options
  });
  return { response, body: await response.json() };
}

test('task API lists, creates, updates, deletes, and validates tasks', async () => {
  await withServer([{ id: 1, title: 'seed', done: false }], async (base) => {
    let result = await json(base, '/api/tasks');
    assert.equal(result.response.status, 200);
    assert.deepEqual(result.body.summary, { total: 1, done: 0, active: 1 });

    result = await json(base, '/api/tasks', {
      method: 'POST',
      body: JSON.stringify({ title: '  write a smoke test  ' })
    });
    assert.equal(result.response.status, 201);
    assert.equal(result.body.task.id, 2);
    assert.equal(result.body.task.title, 'write a smoke test');

    result = await json(base, '/api/tasks/2', {
      method: 'PATCH',
      body: JSON.stringify({ done: true })
    });
    assert.equal(result.response.status, 200);
    assert.equal(result.body.task.done, true);
    assert.deepEqual(result.body.summary, { total: 2, done: 1, active: 1 });

    result = await json(base, '/api/tasks', {
      method: 'POST',
      body: JSON.stringify({ title: '' })
    });
    assert.equal(result.response.status, 400);
    assert.equal(result.body.error, 'invalid_title');

    result = await json(base, '/api/tasks/2', { method: 'DELETE' });
    assert.equal(result.response.status, 200);
    assert.deepEqual(result.body.summary, { total: 1, done: 0, active: 1 });
  });
});

test('static page and missing API route have explicit status codes', async () => {
  await withServer([], async (base) => {
    const html = await fetch(`${base}/`);
    assert.equal(html.status, 200);
    assert.match(await html.text(), /任务面板/);

    const missing = await json(base, '/api/missing');
    assert.equal(missing.response.status, 404);
    assert.equal(missing.body.error, 'not_found');
  });
});
