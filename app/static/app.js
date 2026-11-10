const $ = s => document.querySelector(s);
const el = (tag, props = {}, ...kids) => { const e = Object.assign(document.createElement(tag), props); e.append(...kids); return e; };

let user = localStorage.getItem('user');
let users = [], current = null, timer = null;
const quill = new Quill('#editor', { theme: 'snow', modules: { toolbar: '#toolbar' }, placeholder: 'Start writing…' });

async function api(path, opts = {}) {
  const headers = { 'X-User': user };
  if (opts.json !== undefined) { headers['Content-Type'] = 'application/json'; opts.body = JSON.stringify(opts.json); }
  const r = await fetch('/api' + path, { method: opts.method, body: opts.body, headers });
  if (!r.ok) {
    let msg = 'Something went wrong. Try again.';
    try { const j = await r.json(); if (typeof j.detail === 'string') msg = j.detail; } catch {}
    throw new Error(msg);
  }
  return r.status === 204 ? null : r.json();
}

function banner(msg) {
  const b = $('#banner'); b.textContent = msg; b.hidden = false;
  clearTimeout(banner.t); banner.t = setTimeout(() => (b.hidden = true), 5000);
}
function status(msg, bad = false) { const s = $('#status'); s.textContent = msg; s.className = bad ? 'bad' : ''; }
const fmt = iso => new Date(iso).toLocaleString([], { dateStyle: 'medium', timeStyle: 'short' });

function fill(ul, docs, emptyText) {
  ul.replaceChildren(...(docs.length ? docs.map(d => {
    const meta = d.access === 'owner' ? 'Updated ' + fmt(d.updated_at)
      : `From ${d.owner} · ${d.access === 'editor' ? 'can edit' : 'view only'}`;
    return el('li', { className: current && current.id === d.id ? 'active' : '' },
      el('button', { className: 'doc', onclick: () => openDoc(d.id) },
        el('span', { className: 't', textContent: d.title }), el('span', { className: 'm', textContent: meta })));
  }) : [el('li', { className: 'empty', textContent: emptyText })]));
}

async function refresh() {
  const d = await api('/docs');
  fill($('#owned'), d.owned, 'No documents yet. Create one or upload a file.');
  fill($('#shared'), d.shared, 'Nothing has been shared with you yet.');
}

function closeDoc() {
  current = null; location.hash = '';
  $('#editorWrap').hidden = true; $('#empty').hidden = false;
}

async function openDoc(id) {
  await flush();
  try {
    const d = await api('/docs/' + id);
    current = d; location.hash = id;
    $('#empty').hidden = true; $('#editorWrap').hidden = false;
    $('#title').value = d.title; $('#title').disabled = d.access === 'viewer';
    quill.clipboard.dangerouslyPasteHTML(d.content, 'silent');
    quill.enable(d.access !== 'viewer');
    $('#badge').textContent = d.access === 'owner' ? 'Owner' : d.access === 'editor' ? 'Shared · can edit' : 'Shared · view only';
    $('#shareBtn').hidden = $('#delBtn').hidden = d.access !== 'owner';
    status(''); refresh();
  } catch (e) { banner(e.message); closeDoc(); refresh(); }
}

function schedule() {
  status('Unsaved changes');
  clearTimeout(timer); timer = setTimeout(() => { timer = null; save(); }, 800);
}
async function flush() { if (timer) { clearTimeout(timer); timer = null; await save(); } }
async function save() {
  if (!current) return;
  const title = $('#title').value.trim();
  if (!title) return status('Add a title to save.', true);
  try {
    const d = await api('/docs/' + current.id, { method: 'PUT', json: { title, content: quill.root.innerHTML } });
    current.title = d.title; status('Saved'); refresh();
  } catch (e) { status('Not saved: ' + e.message, true); }
}
quill.on('text-change', (_d, _o, src) => { if (src === 'user' && current) schedule(); });
$('#title').addEventListener('input', () => current && schedule());

$('#newBtn').onclick = async () => {
  try { const d = await api('/docs', { method: 'POST', json: { title: 'Untitled document' } }); await refresh(); openDoc(d.id); }
  catch (e) { banner(e.message); }
};
$('#uploadBtn').onclick = () => $('#file').click();
$('#file').onchange = async e => {
  const f = e.target.files[0]; e.target.value = ''; if (!f) return;
  const fd = new FormData(); fd.append('file', f);
  try { const d = await api('/upload', { method: 'POST', body: fd }); await refresh(); openDoc(d.id); }
  catch (err) { banner(err.message); }
};
$('#delBtn').onclick = async () => {
  if (!confirm(`Delete "${current.title}"? This also removes it for people it's shared with.`)) return;
  try { await api('/docs/' + current.id, { method: 'DELETE' }); timer = null; closeDoc(); refresh(); }
  catch (e) { banner(e.message); }
};

function renderShares() {
  $('#shareUser').replaceChildren(...users.filter(u => u.username !== user).map(u => el('option', { value: u.username, textContent: u.name })));
  const s = current.shares;
  $('#shareList').replaceChildren(...(s.length ? s.map(x => el('li', {},
    el('span', { textContent: `${x.name} · ${x.role === 'editor' ? 'can edit' : 'view only'}` }),
    el('button', { type: 'button', className: 'link', textContent: 'Remove', onclick: () => shareCall('DELETE', '/' + x.username) })))
    : [el('li', { className: 'empty', textContent: 'Not shared with anyone yet.' })]));
}
async function shareCall(method, suffix = '', json) {
  try { current = await api(`/docs/${current.id}/share${suffix}`, { method, json }); renderShares(); }
  catch (e) { banner(e.message); }
}
$('#shareBtn').onclick = async () => { await flush(); renderShares(); $('#shareDlg').showModal(); };
$('#closeDlg').onclick = () => $('#shareDlg').close();
$('#shareForm').onsubmit = e => { e.preventDefault(); shareCall('POST', '', { username: $('#shareUser').value, role: $('#shareRole').value }); };

async function init() {
  users = await (await fetch('/api/users')).json();
  if (!users.some(u => u.username === user)) user = users[0].username;
  const sel = $('#user');
  sel.replaceChildren(...users.map(u => el('option', { value: u.username, textContent: u.name })));
  sel.value = user;
  sel.onchange = async () => {
    const next = sel.value; await flush();   // save pending edits as the previous user
    user = next; localStorage.setItem('user', user); closeDoc(); refresh();
  };
  await refresh();
  const id = parseInt(location.hash.slice(1), 10);
  if (id) openDoc(id);
}
init().catch(e => banner(e.message));
