'use strict';

const state = {
  tables: [],
  current: null,
  query: '',
  data: null,
};

const $ = (id) => document.getElementById(id);

function escapeHTML(value) {
  return String(value ?? '')
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
    .replace(/'/g, '&#39;');
}

async function api(path, options = {}) {
  const res = await fetch(path, {
    headers: { 'Content-Type': 'application/json' },
    ...options,
  });
  let data = null;
  try {
    data = await res.json();
  } catch {
    data = null;
  }
  if (!res.ok) {
    throw new Error((data && data.error) || `请求失败（${res.status}）`);
  }
  return data;
}

let toastTimer = null;
function toast(message, isError = false) {
  const el = $('toast');
  el.textContent = message;
  el.classList.toggle('error', isError);
  el.hidden = false;
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => {
    el.hidden = true;
  }, 2400);
}

function setStatus(text) {
  $('statusText').textContent = text;
}

/* ---------------- Modal ---------------- */
let modalSubmit = null;

function openModal({ title, bodyHTML, okText = '保存', onSubmit }) {
  $('modalTitle').textContent = title;
  $('modalBody').innerHTML = bodyHTML;
  $('modalOk').textContent = okText;
  modalSubmit = onSubmit;
  $('overlay').hidden = false;
  const firstInput = $('modalBody').querySelector('input, textarea');
  if (firstInput) setTimeout(() => firstInput.focus(), 30);
}

function closeModal() {
  $('overlay').hidden = true;
  modalSubmit = null;
}

$('modalClose').addEventListener('click', closeModal);
$('modalCancel').addEventListener('click', closeModal);
$('overlay').addEventListener('click', (e) => {
  if (e.target === $('overlay')) closeModal();
});
document.addEventListener('keydown', (e) => {
  if (e.key === 'Escape' && !$('overlay').hidden) closeModal();
  if (e.key === 'Enter' && (e.metaKey || e.ctrlKey) && !$('overlay').hidden) {
    $('modalOk').click();
  }
});
$('modalOk').addEventListener('click', async () => {
  if (!modalSubmit) return;
  try {
    await modalSubmit();
  } catch (err) {
    toast(err.message, true);
  }
});

/* ---------------- Data ---------------- */
async function refreshState(preferredTable) {
  try {
    const data = await api('/api/state');
    state.tables = data.tables || [];
    renderSidebar();
    const total = state.tables.reduce((sum, t) => sum + t.count, 0);
    setStatus(`已连接 · ${state.tables.length} 张数据表 · 共 ${total} 条记录`);

    const target =
      preferredTable && state.tables.some((t) => t.name === preferredTable)
        ? preferredTable
        : state.current && state.tables.some((t) => t.name === state.current)
          ? state.current
          : state.tables[0] && state.tables[0].name;

    if (target) await selectTable(target);
    else resetMain();
  } catch (err) {
    setStatus('连接失败：' + err.message);
    toast(err.message, true);
  }
}

function renderSidebar() {
  $('tableCount').textContent = String(state.tables.length);
  const list = $('tableList');
  list.innerHTML = '';
  for (const table of state.tables) {
    const btn = document.createElement('button');
    btn.className = 'table-item' + (table.name === state.current ? ' active' : '');
    btn.innerHTML = `
      <svg class="t-icon" viewBox="0 0 24 24" width="15" height="15" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="3" y="4" width="18" height="16" rx="2"></rect>
        <path d="M3 9h18M3 14h18M9 4v16"></path>
      </svg>
      <span class="t-name"></span>
      <span class="t-count">${table.count}</span>`;
    btn.querySelector('.t-name').textContent = table.name;
    btn.addEventListener('click', () => selectTable(table.name));
    list.appendChild(btn);
  }
}

function resetMain() {
  state.current = null;
  state.data = null;
  $('tableTitle').textContent = '选择一个数据表';
  $('tableMeta').textContent = '从左侧选择一个数据表，或新建一个';
  $('emptyState').hidden = false;
  $('tableWrap').hidden = true;
  $('searchInput').value = '';
  $('addRowBtn').disabled = true;
  $('addColumnBtn').disabled = true;
  $('dropTableBtn').disabled = true;
}

async function selectTable(name) {
  state.current = name;
  renderSidebar();
  $('addRowBtn').disabled = false;
  $('addColumnBtn').disabled = false;
  $('dropTableBtn').disabled = false;
  await loadRows();
}

async function loadRows() {
  if (!state.current) return;
  try {
    const q = state.query ? `?q=${encodeURIComponent(state.query)}` : '';
    const data = await api(`/api/tables/${encodeURIComponent(state.current)}${q}`);
    state.data = data;
    renderTable();
  } catch (err) {
    toast(err.message, true);
  }
}

function renderTable() {
  const data = state.data;
  if (!data) return resetMain();

  $('tableTitle').textContent = data.name;
  $('tableMeta').textContent = `${data.columns.length} 个字段 · ${data.total} 条记录${
    state.query ? ` · 搜索「${state.query}」命中 ${data.rows.length} 条` : ''
  }`;
  $('emptyState').hidden = true;
  $('tableWrap').hidden = false;

  const thead = $('dataTable').querySelector('thead');
  const tbody = $('dataTable').querySelector('tbody');

  thead.innerHTML =
    '<tr><th style="width:56px">ID</th>' +
    data.columns
      .map(
        (col) =>
          `<th>${escapeHTML(col.name)}<span class="col-type">${col.type === 'number' ? '数字' : '文本'}</span></th>`
      )
      .join('') +
    '<th style="width:110px"></th></tr>';

  tbody.innerHTML = '';
  for (const row of data.rows) {
    const tr = document.createElement('tr');

    const idTd = document.createElement('td');
    idTd.innerHTML = `<span class="row-id">#${row._id}</span>`;
    tr.appendChild(idTd);

    for (const col of data.columns) {
      const td = document.createElement('td');
      const value = row[col.name];
      td.innerHTML = `<div class="cell-text" title="${escapeHTML(value)}">${escapeHTML(value) || '<span style="color:#c0c4cc">—</span>'}</div>`;
      tr.appendChild(td);
    }

    const actionTd = document.createElement('td');
    actionTd.innerHTML = `<div class="cell-actions">
        <button class="link-btn edit">编辑</button>
        <button class="link-btn del">删除</button>
      </div>`;
    actionTd.querySelector('.edit').addEventListener('click', () => openRowModal(row));
    actionTd.querySelector('.del').addEventListener('click', () => deleteRow(row._id));
    tr.appendChild(actionTd);

    tbody.appendChild(tr);
  }

  $('noResult').hidden = data.rows.length !== 0;
}

/* ---------------- Row CRUD ---------------- */
function openRowModal(row) {
  if (!state.data) return;
  const columns = state.data.columns;
  const isEdit = Boolean(row);

  const bodyHTML = columns
    .map((col) => {
      const value = isEdit ? row[col.name] : '';
      const long = ['summary', 'summary_cn', 'content', 'desc', 'description', 'outline'].includes(
        col.name.toLowerCase()
      );
      if (long || String(value).length > 60) {
        return `<div class="field"><label>${escapeHTML(col.name)}</label>
          <textarea data-col="${escapeHTML(col.name)}">${escapeHTML(value)}</textarea></div>`;
      }
      return `<div class="field"><label>${escapeHTML(col.name)}</label>
        <input data-col="${escapeHTML(col.name)}" type="${col.type === 'number' ? 'number' : 'text'}"
          value="${escapeHTML(value)}" /></div>`;
    })
    .join('');

  openModal({
    title: isEdit ? `编辑记录 #${row._id}` : '新增记录',
    bodyHTML,
    okText: isEdit ? '保存修改' : '添加',
    onSubmit: async () => {
      const values = {};
      $('modalBody')
        .querySelectorAll('[data-col]')
        .forEach((el) => {
          values[el.dataset.col] = el.value;
        });
      if (isEdit) {
        await api(`/api/tables/${encodeURIComponent(state.current)}/rows/${row._id}`, {
          method: 'PUT',
          body: JSON.stringify({ values }),
        });
        toast('记录已更新');
      } else {
        await api(`/api/tables/${encodeURIComponent(state.current)}/rows`, {
          method: 'POST',
          body: JSON.stringify({ values }),
        });
        toast('记录已添加');
      }
      closeModal();
      await refreshState(state.current);
    },
  });
}

async function deleteRow(id) {
  if (!window.confirm(`确定删除记录 #${id} 吗？`)) return;
  try {
    await api(`/api/tables/${encodeURIComponent(state.current)}/rows/${id}`, { method: 'DELETE' });
    toast('记录已删除');
    await refreshState(state.current);
  } catch (err) {
    toast(err.message, true);
  }
}

/* ---------------- Table CRUD ---------------- */
$('newTableBtn').addEventListener('click', () => {
  const bodyHTML = `
    <div class="field">
      <label>表名</label>
      <input id="newTableName" placeholder="例如 novel_outlines" />
    </div>
    <div class="field">
      <label>字段定义</label>
      <div id="colList" style="display:flex;flex-direction:column;gap:8px"></div>
      <button id="addColBtn" class="btn ghost" style="margin-top:8px;width:100%">＋ 添加字段</button>
    </div>
    <p class="modal-hint">表名与字段名支持中英文、数字、下划线。创建后可在表内继续新增字段。</p>`;

  openModal({
    title: '新建数据表',
    bodyHTML,
    okText: '创建',
    onSubmit: async () => {
      const name = $('newTableName').value.trim();
      const columns = [];
      $('colList')
        .querySelectorAll('.col-row')
        .forEach((rowEl) => {
          const colName = rowEl.querySelector('input').value.trim();
          const type = rowEl.querySelector('select').value;
          if (colName) columns.push({ name: colName, type });
        });
      if (!name) throw new Error('请输入表名');
      if (!columns.length) throw new Error('至少添加一个字段');
      await api('/api/tables', {
        method: 'POST',
        body: JSON.stringify({ name, columns }),
      });
      closeModal();
      toast('数据表已创建');
      state.query = '';
      $('searchInput').value = '';
      await refreshState(name);
    },
  });

  const addColRow = () => {
    const rowEl = document.createElement('div');
    rowEl.className = 'col-row';
    rowEl.innerHTML = `
      <input placeholder="字段名" />
      <select><option value="text">文本</option><option value="number">数字</option></select>`;
    $('colList').appendChild(rowEl);
  };
  $('addColBtn').addEventListener('click', addColRow);
  addColRow();
  addColRow();
});

$('addColumnBtn').addEventListener('click', () => {
  openModal({
    title: `为「${state.current}」新增字段`,
    bodyHTML: `
      <div class="field"><label>字段名</label><input id="newColName" placeholder="例如 rating" /></div>
      <div class="field"><label>类型</label>
        <select id="newColType"><option value="text">文本</option><option value="number">数字</option></select>
      </div>
      <p class="modal-hint">已有记录的新字段默认为空，可逐条编辑补充。</p>`,
    okText: '新增',
    onSubmit: async () => {
      const name = $('newColName').value.trim();
      const type = $('newColType').value;
      if (!name) throw new Error('请输入字段名');
      await api(`/api/tables/${encodeURIComponent(state.current)}`, {
        method: 'PATCH',
        body: JSON.stringify({ addColumn: { name, type } }),
      });
      closeModal();
      toast('字段已添加');
      await refreshState(state.current);
    },
  });
});

$('dropTableBtn').addEventListener('click', async () => {
  const name = state.current;
  if (!name) return;
  if (!window.confirm(`确定删除数据表「${name}」及其全部记录吗？此操作不可恢复。`)) return;
  try {
    await api(`/api/tables/${encodeURIComponent(name)}`, { method: 'DELETE' });
    toast('数据表已删除');
    state.current = null;
    await refreshState();
  } catch (err) {
    toast(err.message, true);
  }
});

$('addRowBtn').addEventListener('click', () => openRowModal(null));

/* ---------------- Search ---------------- */
let searchTimer = null;
$('searchInput').addEventListener('input', (e) => {
  clearTimeout(searchTimer);
  const value = e.target.value;
  searchTimer = setTimeout(() => {
    state.query = value.trim();
    loadRows();
  }, 220);
});

/* ---------------- Backup ---------------- */
$('exportBtn').addEventListener('click', () => {
  window.location.href = '/api/export';
});

$('importBtn').addEventListener('click', () => $('importFile').click());

$('importFile').addEventListener('change', async (e) => {
  const file = e.target.files && e.target.files[0];
  e.target.value = '';
  if (!file) return;
  if (!window.confirm('导入将覆盖当前全部数据，确定继续吗？')) return;
  try {
    const text = await file.text();
    const payload = JSON.parse(text);
    await api('/api/import', { method: 'POST', body: JSON.stringify(payload) });
    toast('备份已导入');
    state.current = null;
    await refreshState();
  } catch (err) {
    toast('导入失败：' + err.message, true);
  }
});

/* ---------------- Init ---------------- */
refreshState();
