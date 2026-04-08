// ── Storage keys ──────────────────────────────────────────────────────────────
const STORAGE_KEY = 'my_tasks';
const THEME_KEY   = 'my_tasks_theme';

// ── Category config ───────────────────────────────────────────────────────────
const CATEGORIES = {
  work:     { label: '업무', color: 'cat-work' },
  personal: { label: '개인', color: 'cat-personal' },
  study:    { label: '공부', color: 'cat-study' },
};

// ── State ─────────────────────────────────────────────────────────────────────
let activeFilter = 'all';

// ── Storage helpers ───────────────────────────────────────────────────────────
function loadTasks() {
  return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
}

function saveTasks(tasks) {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(tasks));
}

function generateId() {
  return Date.now().toString(36) + Math.random().toString(36).slice(2, 6);
}

// ── Theme ─────────────────────────────────────────────────────────────────────
function applyTheme(dark) {
  document.body.classList.toggle('dark', dark);
  document.getElementById('theme-switch').checked = dark;
  localStorage.setItem(THEME_KEY, dark ? 'dark' : 'light');
}

// ── Sort ──────────────────────────────────────────────────────────────────────
function sortTasks(tasks) {
  const sort     = document.getElementById('sort-select').value;
  const copy     = [...tasks];
  const catOrder = { work: 0, personal: 1, study: 2 };

  switch (sort) {
    case 'newest':
      return copy.sort((a, b) => new Date(b.createdAt) - new Date(a.createdAt));
    case 'oldest':
      return copy.sort((a, b) => new Date(a.createdAt) - new Date(b.createdAt));
    case 'category':
      return copy.sort((a, b) => (catOrder[a.category] ?? 99) - (catOrder[b.category] ?? 99));
    case 'alpha':
      return copy.sort((a, b) => a.text.localeCompare(b.text, 'ko'));
    default: // 미완료 우선
      return [...copy.filter(t => !t.done), ...copy.filter(t => t.done)];
  }
}

// ── Stats panel ───────────────────────────────────────────────────────────────
function renderStats(tasks) {
  const panel = document.getElementById('stats-panel');

  const total = tasks.length;
  const done  = tasks.filter(t => t.done).length;
  const pct   = total === 0 ? 0 : Math.round((done / total) * 100);

  const todayStr   = new Date().toDateString();
  const todayCount = tasks.filter(t => new Date(t.createdAt).toDateString() === todayStr).length;

  const catStats = Object.entries(CATEGORIES).map(([key, cfg]) => {
    const ct    = tasks.filter(t => t.category === key);
    const cdone = ct.filter(t => t.done).length;
    return { key, cfg, total: ct.length, done: cdone };
  }).filter(s => s.total > 0);

  if (total === 0) { panel.innerHTML = ''; return; }

  panel.innerHTML = `
    <div class="progress-section">
      <div class="progress-header">
        <span class="progress-label">${done}/${total} 완료</span>
        <span class="progress-pct">${pct}%</span>
      </div>
      <div class="progress-bar">
        <div class="progress-fill" style="width:${pct}%"></div>
      </div>
    </div>
    ${catStats.length > 0 ? `
    <div class="cat-stats">
      ${catStats.map(s => {
        const cp = s.total === 0 ? 0 : Math.round((s.done / s.total) * 100);
        return `
        <div class="cat-stat-item">
          <span class="category-tag ${s.cfg.color}">${s.cfg.label}</span>
          <span class="cat-stat-nums">${s.done}/${s.total}</span>
          <div class="cat-mini-bar">
            <div class="cat-mini-fill ${s.cfg.color}" style="width:${cp}%"></div>
          </div>
        </div>`;
      }).join('')}
    </div>` : ''}
    <div class="today-badge">오늘 추가 <strong>${todayCount}개</strong></div>
  `;
}

// ── Inline edit ───────────────────────────────────────────────────────────────
function startEdit(id, li) {
  const span  = li.querySelector('.task-text');
  const tasks = loadTasks();
  const task  = tasks.find(t => t.id === id);
  if (!task) return;

  const input = document.createElement('input');
  input.type      = 'text';
  input.className = 'edit-input';
  input.value     = task.text;
  span.replaceWith(input);
  input.focus();
  input.select();

  let committed = false;

  function commit() {
    if (committed) return;
    committed = true;
    const newText = input.value.trim();
    if (newText && newText !== task.text) {
      task.text = newText;
      saveTasks(tasks);
    }
    render();
  }

  input.addEventListener('keydown', e => {
    if (e.key === 'Enter')  { e.preventDefault(); commit(); }
    if (e.key === 'Escape') { committed = true; render(); }
  });
  input.addEventListener('blur', commit);
}

// ── Render ────────────────────────────────────────────────────────────────────
function render() {
  const tasks = loadTasks();
  const list  = document.getElementById('task-list');
  const empty = document.getElementById('empty-state');

  list.innerHTML = '';

  const filtered = activeFilter === 'all'
    ? tasks
    : tasks.filter(t => t.category === activeFilter);

  const sorted = sortTasks(filtered);

  // DocumentFragment: single DOM insertion for smooth performance at 100+ items
  const frag = document.createDocumentFragment();

  sorted.forEach(task => {
    const cat = CATEGORIES[task.category] || CATEGORIES.work;
    const li  = document.createElement('li');
    li.className  = 'task-item' + (task.done ? ' done' : '');
    li.dataset.id = task.id;

    li.innerHTML = `
      <input type="checkbox" ${task.done ? 'checked' : ''}>
      <span class="category-tag ${cat.color}">${cat.label}</span>
      <span class="task-text" title="더블클릭으로 편집">${escapeHtml(task.text)}</span>
      <button class="delete-btn" title="삭제">✕</button>
    `;

    li.querySelector('input[type="checkbox"]').addEventListener('change', () => toggleDone(task.id));
    li.querySelector('.delete-btn').addEventListener('click', () => deleteTask(task.id));
    li.querySelector('.task-text').addEventListener('dblclick', () => {
      if (!task.done) startEdit(task.id, li);
    });

    frag.appendChild(li);
  });

  list.appendChild(frag);
  renderStats(tasks);
  empty.style.display = sorted.length === 0 ? 'block' : 'none';
}

// ── CRUD ──────────────────────────────────────────────────────────────────────
function addTask() {
  const input    = document.getElementById('task-input');
  const select   = document.getElementById('category-select');
  const text     = input.value.trim();
  const category = select.value;

  if (!text) return;

  const tasks = loadTasks();
  tasks.push({
    id:        generateId(),
    text,
    done:      false,
    category,
    createdAt: new Date().toISOString(),
  });

  saveTasks(tasks);
  render();
  input.value = '';
  input.focus();
}

function toggleDone(id) {
  const tasks = loadTasks();
  const task  = tasks.find(t => t.id === id);
  if (task) task.done = !task.done;
  saveTasks(tasks);
  render();
}

function deleteTask(id) {
  saveTasks(loadTasks().filter(t => t.id !== id));
  render();
}

function clearCompleted() {
  const tasks     = loadTasks();
  const doneCount = tasks.filter(t => t.done).length;
  if (doneCount === 0) return;
  if (!confirm(`완료된 항목 ${doneCount}개를 모두 삭제할까요?`)) return;
  saveTasks(tasks.filter(t => !t.done));
  render();
}

// ── Export / Import ───────────────────────────────────────────────────────────
function exportTasks() {
  const tasks = loadTasks();
  const blob  = new Blob([JSON.stringify(tasks, null, 2)], { type: 'application/json' });
  const url   = URL.createObjectURL(blob);
  const a     = document.createElement('a');
  a.href     = url;
  a.download = `my-tasks-${new Date().toISOString().slice(0, 10)}.json`;
  a.click();
  URL.revokeObjectURL(url);
}

function importTasks(file) {
  const reader = new FileReader();
  reader.onload = e => {
    try {
      const data = JSON.parse(e.target.result);
      if (!Array.isArray(data) || !data.every(t => t.id && t.text && t.category)) {
        throw new Error();
      }
      if (!confirm(`${data.length}개 항목을 가져옵니다. 현재 데이터가 교체됩니다.`)) return;
      saveTasks(data);
      render();
    } catch {
      alert('가져오기 실패: 올바른 형식의 JSON 파일이 아닙니다.');
    }
  };
  reader.readAsText(file);
}

// ── Filter helper ─────────────────────────────────────────────────────────────
function setFilter(filter) {
  activeFilter = filter;
  document.querySelectorAll('.filter-btn').forEach(b =>
    b.classList.toggle('active', b.dataset.filter === filter)
  );
  render();
}

// ── Escape HTML ───────────────────────────────────────────────────────────────
function escapeHtml(str) {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

// ── Today date ────────────────────────────────────────────────────────────────
function setTodayDate() {
  const opts = { year: 'numeric', month: 'long', day: 'numeric', weekday: 'short' };
  document.getElementById('today-date').textContent =
    new Date(2026, 2, 24).toLocaleDateString('ko-KR', opts);
}

// ── Event listeners ───────────────────────────────────────────────────────────
document.getElementById('add-btn').addEventListener('click', addTask);

document.getElementById('task-input').addEventListener('keydown', e => {
  if (e.key === 'Enter') addTask();
});

document.querySelectorAll('.filter-btn').forEach(btn => {
  btn.addEventListener('click', () => setFilter(btn.dataset.filter));
});

document.getElementById('sort-select').addEventListener('change', render);

document.getElementById('theme-switch').addEventListener('change', e => {
  applyTheme(e.target.checked);
});

document.getElementById('clear-done-btn').addEventListener('click', clearCompleted);

document.getElementById('export-btn').addEventListener('click', exportTasks);

document.getElementById('import-btn').addEventListener('click', () => {
  document.getElementById('import-file').click();
});

document.getElementById('import-file').addEventListener('change', e => {
  const file = e.target.files[0];
  if (file) { importTasks(file); e.target.value = ''; }
});

// Keyboard shortcuts
document.addEventListener('keydown', e => {
  if (!e.altKey) return;
  switch (e.key) {
    case 'n': case 'N':
      e.preventDefault();
      document.getElementById('task-input').focus();
      break;
    case '1': e.preventDefault(); setFilter('all');      break;
    case '2': e.preventDefault(); setFilter('work');     break;
    case '3': e.preventDefault(); setFilter('personal'); break;
    case '4': e.preventDefault(); setFilter('study');    break;
  }
});

// ── Init ──────────────────────────────────────────────────────────────────────
applyTheme(localStorage.getItem(THEME_KEY) === 'dark');
setTodayDate();
render();
