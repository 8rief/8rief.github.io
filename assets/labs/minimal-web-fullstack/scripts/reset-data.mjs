import { mkdir, writeFile } from 'node:fs/promises';
import path from 'node:path';

const dataFile = process.argv[2] || path.join('data', 'tasks.json');
const seedTasks = [
  { id: 1, title: '理解浏览器发出的 GET / 请求', done: true },
  { id: 2, title: '用 fetch 调用 /api/tasks', done: false }
];

await mkdir(path.dirname(dataFile), { recursive: true });
await writeFile(dataFile, `${JSON.stringify(seedTasks, null, 2)}\n`, 'utf8');
console.log(`seeded_tasks=${seedTasks.length}`);
console.log(`data_file=${dataFile}`);
