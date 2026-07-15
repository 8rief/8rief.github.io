const list = document.querySelector('#task-list');
const form = document.querySelector('#task-form');
const input = document.querySelector('#task-title');
const status = document.querySelector('#status');

function setStatus(message, isError = false) {
  status.textContent = message;
  status.classList.toggle('error', isError);
}

async function fetchJson(url, options = {}) {
  const response = await fetch(url, {
    headers: { 'content-type': 'application/json', ...(options.headers || {}) },
    ...options
  });
  const payload = await response.json();
  if (!response.ok) {
    throw new Error(payload.message || `HTTP ${response.status}`);
  }
  return payload;
}

function render(tasks, summary) {
  list.innerHTML = '';
  for (const task of tasks) {
    const item = document.createElement('li');
    item.className = `task${task.done ? ' done' : ''}`;
    item.innerHTML = `
      <div>
        <div class="title"></div>
        <div class="meta">#${task.id} · ${task.done ? 'done' : 'active'}</div>
      </div>
      <button class="secondary" data-action="toggle"></button>
      <button class="danger" data-action="delete">删除</button>
    `;
    item.querySelector('.title').textContent = task.title;
    item.querySelector('[data-action="toggle"]').textContent = task.done ? '恢复' : '完成';
    item.querySelector('[data-action="toggle"]').addEventListener('click', () => updateTask(task.id, !task.done));
    item.querySelector('[data-action="delete"]').addEventListener('click', () => deleteTask(task.id));
    list.append(item);
  }
  setStatus(`总数 ${summary.total}，完成 ${summary.done}，待办 ${summary.active}`);
}

async function loadTasks() {
  try {
    const payload = await fetchJson('/api/tasks');
    render(payload.tasks, payload.summary);
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function createTask(title) {
  await fetchJson('/api/tasks', {
    method: 'POST',
    body: JSON.stringify({ title })
  });
  input.value = '';
  await loadTasks();
}

async function updateTask(id, done) {
  try {
    await fetchJson(`/api/tasks/${id}`, {
      method: 'PATCH',
      body: JSON.stringify({ done })
    });
    await loadTasks();
  } catch (error) {
    setStatus(error.message, true);
  }
}

async function deleteTask(id) {
  try {
    await fetchJson(`/api/tasks/${id}`, { method: 'DELETE' });
    await loadTasks();
  } catch (error) {
    setStatus(error.message, true);
  }
}

form.addEventListener('submit', async (event) => {
  event.preventDefault();
  const title = input.value.trim();
  if (!title) {
    setStatus('请输入任务标题。', true);
    return;
  }
  try {
    await createTask(title);
  } catch (error) {
    setStatus(error.message, true);
  }
});

loadTasks();
