const $ = (selector) => document.querySelector(selector);
const $$ = (selector) => [...document.querySelectorAll(selector)];
const emptyConversation = $('#conversation-empty').cloneNode(true);
const model = { state: null, token: '', view: 'conversation', online: false, dirtyPersona: false, submitting: false, savingPersona: false, creatingTask: false, resetting: false, connecting: false, disconnecting: false, request: null, messageSignature: '', taskSignature: '', toastTimer: null, library: { memories: [], reports: [] }, libraryLoaded: false, librarySignature: '', savingMemory: false, savingReport: false, readingFile: false, fileReadVersion: 0, deletingLibrary: false, deleteItem: null, readerReport: null, readingReport: false };
const titles = { conversation: 'Conversation', persona: 'Persona', activity: 'Activity', connection: 'Connection', library: 'Library' };
const realTask = (task) => task.provider === 'openai';
const replyTask = (task) => task.kind !== 'draft';
const connected = () => Boolean(model.state?.connection?.connected);
const livePending = () => Boolean(model.state?.tasks.some(task => realTask(task) && pending(task)));
const canSend = () => model.online && !model.submitting && !model.resetting && !model.connecting && !model.disconnecting && !livePending() && (!connected() || model.state.connection.can_send);
const money = (value, precise = false) => Number.isFinite(value) ? new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD', minimumFractionDigits: 2, maximumFractionDigits: precise ? 4 : 2 }).format(value) : '—';
const pending = (task) => ['queued', 'running'].includes(task.status);
const titleCase = (text = '') => text.charAt(0).toUpperCase() + text.slice(1);

function toast(message, failure = false) {
  const node = $('#toast');
  clearTimeout(model.toastTimer);
  node.textContent = message;
  node.classList.toggle('failure', failure);
  node.hidden = false;
  model.toastTimer = setTimeout(() => { node.hidden = true; }, failure ? 6500 : 3200);
}

async function api(path, payload) {
  const options = { cache: 'no-store', signal: AbortSignal.timeout(12000) };
  if (payload !== undefined) Object.assign(options, { method: 'POST', headers: { 'Content-Type': 'application/json', 'X-Session-Token': model.token }, body: JSON.stringify(payload) });
  const response = await fetch(path, options);
  const result = await response.json();
  if (!response.ok) { const error = new Error(result.error || 'That change could not be saved. Please try again.'); error.status = response.status; throw error; }
  return result;
}

function setOnline(online) {
  model.online = online;
  $('#offline-banner').hidden = online;
  $('#connection-label').textContent = online ? 'Connected locally' : 'Reconnecting';
  $('#send-message').disabled = !canSend();
  $$('.suggestions button').forEach(button => { button.disabled = !canSend(); });
  $('#connect-ai').disabled = !online || model.connecting || model.disconnecting;
  $('#disconnect-ai').disabled = !online || model.connecting || model.disconnecting;
  $('#api-key').disabled = !online || model.connecting || model.disconnecting;
  $('#reset-open').disabled = !online || model.submitting || model.resetting;
  $('#persona-save').disabled = !online || model.savingPersona;
  $('#task-form button').disabled = !online || model.creatingTask;
  $('#memory-save').disabled = !online || !model.libraryLoaded || model.savingMemory;
  $('#report-save').disabled = !online || !model.libraryLoaded || model.savingReport || model.readingFile;
  $('#library-delete-confirm').disabled = !online || model.deletingLibrary;
  $('#report-select').disabled = !online || !model.libraryLoaded || model.submitting;
  $('#project-context').disabled = !online || model.submitting;
  $$('[data-library-delete]').forEach(button => { button.disabled = !online || model.deletingLibrary; });
}

function switchView(view) {
  if (!titles[view]) view = 'conversation';
  model.view = view;
  $$('.view').forEach(node => { node.hidden = node.id !== `view-${view}`; });
  $$('.nav-button').forEach(node => {
    node.classList.toggle('active', node.dataset.view === view);
    if (node.dataset.view === view) node.setAttribute('aria-current', 'page');
    else node.removeAttribute('aria-current');
  });
  $('#view-title').textContent = titles[view];
  document.title = `${titles[view]} — Presence`;
  if (location.hash !== `#${view}`) history.replaceState(null, '', `#${view}`);
}

function readPersona() {
  const form = $('#persona-form');
  return { name: form.elements.name.value.trim(), role: form.elements.role.value.trim(), tone: form.elements.tone.value || 'warm', response_length: form.elements.response_length.value || 'balanced', instructions: form.elements.instructions.value.trim() };
}

function fillPersona(persona) {
  const form = $('#persona-form');
  for (const [key, value] of Object.entries(persona)) if (form.elements[key]) form.elements[key].value = value;
  renderPersonaPreview();
}

function renderPersonaPreview() {
  const persona = readPersona();
  const name = persona.name || 'Your agent';
  $('#persona-preview-name').textContent = name;
  $('#persona-preview-role').textContent = persona.role || 'Give your agent a role.';
  const examples = {
    warm: `Hi, I'm ${name}. Let's make room for your ideas and find a good place to start.`,
    direct: `I'm ${name}. Tell me the goal, and we'll work out the next step.`,
    thoughtful: `I'm ${name}. What would you like to explore? We can think it through together.`,
    playful: `I'm ${name}. Bring an idea—even a wonderfully unfinished one. Let's see where it goes.`
  };
  let copy = examples[persona.tone];
  if (persona.response_length === 'short') copy = copy.split('. ').slice(0, 2).join('. ');
  if (persona.response_length === 'detailed') copy += ' We can look at the possibilities, choose a direction, and break it into manageable steps.';
  $('#persona-preview-copy').textContent = copy;
}

function safeSourceUrl(value) {
  try { const url = new URL(value); return url.protocol === 'https:' ? url.href : null; }
  catch { return null; }
}

function element(tag, className, text) {
  const node = document.createElement(tag);
  if (className) node.className = className;
  if (text !== undefined) node.textContent = text;
  return node;
}

function libraryDate(value) {
  if (!value) return 'Date not recorded';
  if (/^\d{4}-\d{2}-\d{2}$/.test(value)) return value;
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? 'Date not recorded' : date.toLocaleDateString([], { month: 'short', day: 'numeric', year: 'numeric' });
}

function renderSources(sources) {
  if (!Array.isArray(sources) || !sources.length) return null;
  const details = element('details', 'message-sources');
  details.append(element('summary', '', `Sources provided · ${sources.length}`));
  const list = element('div', 'source-list');
  for (const source of sources) {
    const card = element('div', 'source-reference');
    card.append(element('strong', '', `${source.citation || ''} ${source.title || 'Saved source'}`.trim()));
    const metadata = [];
    if (source.kind === 'memory') metadata.push('Saved memory', `Updated ${libraryDate(source.updated_at)}`);
    else if (source.kind === 'project') metadata.push('Presence project document', source.path || '');
    else metadata.push(source.source_name || 'Saved document', libraryDate(source.report_date));
    if (source.line_start) metadata.push(`Lines ${source.line_start}–${source.line_end || source.line_start}`);
    if (source.truncated) metadata.push('Excerpt');
    card.append(element('p', '', metadata.filter(Boolean).join(' · ')));
    const actions = element('div', 'source-actions');
    if (source.kind === 'report' && source.id) {
      const view = element('button', 'text-button', 'View saved text'); view.type = 'button'; view.dataset.reportView = source.id; actions.append(view);
    }
    const url = safeSourceUrl(source.source_url);
    if (url) { const link = element('a', 'text-button', 'Source link ↗'); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; actions.append(link); }
    if (actions.children.length) card.append(actions);
    list.append(card);
  }
  details.append(list);
  return details;
}

function switchLibraryTab(tab) {
  const memory = tab !== 'documents';
  $('#memory-panel').hidden = !memory;
  $('#documents-panel').hidden = memory;
  $('#memory-tab').setAttribute('aria-selected', String(memory));
  $('#documents-tab').setAttribute('aria-selected', String(!memory));
  $('#memory-tab').tabIndex = memory ? 0 : -1;
  $('#documents-tab').tabIndex = memory ? -1 : 0;
}

function renderLibrary(library) {
  model.library = library;
  model.libraryLoaded = true;
  $('#library-load-status').textContent = 'Saved on this computer. Relevant notes and chosen excerpts may be included in real AI replies.';
  const signature = JSON.stringify(library);
  if (signature === model.librarySignature) return;
  model.librarySignature = signature;
  const memories = library.memories || [];
  const reports = library.reports || [];
  $('#memory-count').textContent = memories.length;
  $('#document-count').textContent = reports.length;
  const memoryCards = document.createDocumentFragment();
  for (const memory of memories) {
    const card = element('article', 'library-item memory-item');
    const heading = element('div', 'library-item-heading');
    heading.append(element('h4', '', memory.title));
    const remove = element('button', 'text-button delete-link', 'Delete'); remove.type = 'button'; remove.dataset.libraryDelete = memory.id; remove.dataset.libraryKind = 'memory'; heading.append(remove);
    card.append(heading, element('p', 'library-item-meta', `Saved memory · ${libraryDate(memory.updated_at || memory.created_at)}`), element('p', 'memory-content', memory.content));
    memoryCards.append(card);
  }
  if (!memories.length) memoryCards.append(element('p', 'library-empty', 'No saved memories yet. Start with something useful about you or your work.'));
  $('#memory-list').replaceChildren(memoryCards);
  const reportCards = document.createDocumentFragment();
  for (const report of reports) {
    const card = element('article', 'library-item report-item');
    card.append(element('span', 'document-type', 'SAVED TEXT'), element('h4', '', report.title), element('p', 'library-item-meta', `${report.source_name || 'Source not recorded'} · ${libraryDate(report.report_date)}`));
    const url = safeSourceUrl(report.source_url);
    if (url) { const link = element('a', 'document-source-link', 'Source link ↗'); link.href = url; link.target = '_blank'; link.rel = 'noopener noreferrer'; card.append(link); }
    const actions = element('div', 'library-item-actions');
    const discuss = element('button', 'secondary-button', 'Discuss this'); discuss.type = 'button'; discuss.dataset.reportDiscuss = report.id;
    const view = element('button', 'text-button', 'View text'); view.type = 'button'; view.dataset.reportView = report.id;
    const remove = element('button', 'text-button delete-link', 'Delete'); remove.type = 'button'; remove.dataset.libraryDelete = report.id; remove.dataset.libraryKind = 'report';
    actions.append(discuss, view, remove); card.append(actions); reportCards.append(card);
  }
  if (!reports.length) reportCards.append(element('p', 'library-empty', 'Add a document, then choose “Discuss this” to bring it into a conversation.'));
  $('#report-list').replaceChildren(reportCards);
  const select = $('#report-select');
  const selected = select.value;
  const options = document.createDocumentFragment();
  const none = element('option', '', 'No document selected'); none.value = ''; options.append(none);
  for (const report of reports) { const option = element('option', '', report.title); option.value = report.id; options.append(option); }
  select.replaceChildren(options);
  if (reports.some(report => report.id === selected)) select.value = selected;
  else if (selected) toast('The selected document was removed. Choose another document before sending.');
}

async function refreshLibrary() {
  try { renderLibrary(await api('/api/library')); setOnline(model.online); }
  catch (error) { $('#library-load-status').textContent = error.message; }
}

function discussReport(id) {
  if (!model.library.reports.some(report => report.id === id)) { toast('This document is no longer in your library.', true); return; }
  if (model.submitting) { toast('Wait for your current message to finish sending.'); return; }
  $('#report-select').value = id;
  switchView('conversation');
  $('#report-reader').close();
  $('#message-input').focus();
  toast('Document selected. Ask a question when you’re ready.');
}

async function readReport(id) {
  if (model.readingReport) return;
  model.readingReport = true;
  try {
    const { report } = await api(`/api/reports/${encodeURIComponent(id)}`);
    model.readerReport = report;
    $('#reader-title').textContent = report.title;
    $('#reader-meta').textContent = `${report.source_name || 'Source not recorded'} · ${libraryDate(report.report_date)}`;
    $('#reader-content').textContent = report.content;
    const url = safeSourceUrl(report.source_url);
    $('#reader-source').hidden = !url;
    if (url) $('#reader-source').href = url;
    else $('#reader-source').removeAttribute('href');
    $('#report-reader').showModal();
  } catch (error) { toast(error.message, true); }
  finally { model.readingReport = false; }
}

function reviewDelete(kind, id) {
  const item = (kind === 'memory' ? model.library.memories : model.library.reports).find(entry => entry.id === id);
  if (!item) return;
  model.deleteItem = { kind, id, title: item.title };
  $('#library-delete-title').textContent = kind === 'memory' ? 'Delete this memory?' : 'Delete this document?';
  $('#library-delete-copy').textContent = `“${item.title}” will no longer be available for new replies. This cannot be undone in Presence.`;
  $('#library-delete-dialog').showModal();
}

function renderMessages(state) {
  const signature = JSON.stringify(state.messages);
  if (signature === model.messageSignature) return;
  model.messageSignature = signature;
  const region = $('#message-region');
  const nearBottom = region.scrollHeight - region.scrollTop - region.clientHeight < 110;
  if (!state.messages.length) { region.replaceChildren(emptyConversation.cloneNode(true)); return; }
  const fragment = document.createDocumentFragment();
  for (const item of state.messages) {
    const entry = document.createElement('article');
    entry.className = `message ${item.role === 'user' ? 'user' : 'assistant'}`;
    const label = document.createElement('div');
    label.className = 'message-label';
    label.textContent = item.role === 'user' ? 'You' : 'Agent';
    const badge = document.createElement('span');
    badge.textContent = item.provider === 'openai' ? 'Live AI' : 'Preview';
    badge.className = item.provider === 'openai' ? 'live-message-badge' : 'preview-message-badge';
    label.append(badge);
    const content = document.createElement('p');
    content.className = 'message-content';
    content.textContent = item.content;
    entry.append(label, content);
    const sources = renderSources(item.sources);
    if (sources) entry.append(sources);
    fragment.append(entry);
  }
  region.replaceChildren(fragment);
  if (nearBottom || state.messages.at(-1)?.role === 'user') region.scrollTop = region.scrollHeight;
}

function renderTasks(state) {
  const active = state.tasks.filter(pending);
  $('#task-count').hidden = active.length === 0;
  $('#task-count').textContent = active.length;
  const replyActive = active.some(replyTask);
  const realReplyActive = active.some(task => realTask(task) && replyTask(task));
  $('#reply-progress').hidden = !replyActive;
  $('#reply-progress-copy').textContent = realReplyActive ? 'Your AI is thinking…' : 'Preparing a preview reply…';
  $('#presence-state').textContent = replyActive ? (realReplyActive ? 'Thinking with your persona' : 'Preparing a preview reply') : connected() ? (state.connection.can_send ? 'Ready for a conversation' : 'Test allowance unavailable') : 'Ready to preview';
  const latestReply = state.tasks.find(replyTask);
  const failure = state.messages.length > 0 && latestReply && realTask(latestReply) && latestReply.status === 'failed';
  $('#reply-error').hidden = !failure;
  $('#reply-error').textContent = failure ? (latestReply.result || 'The real AI reply could not finish. See Activity for details.') : '';
  const signature = JSON.stringify(state.tasks);
  if (signature === model.taskSignature) return;
  model.taskSignature = signature;
  const list = $('#tasks-list');
  if (!state.tasks.length) {
    const empty = document.createElement('p'); empty.className = 'empty-task'; empty.textContent = 'No activity yet. Your conversations and sample tasks will appear here.'; list.replaceChildren(empty); return;
  }
  const fragment = document.createDocumentFragment();
  for (const task of state.tasks) {
    const card = document.createElement('article'); card.className = 'task-item';
    const top = document.createElement('div'); top.className = 'task-item-top';
    const identity = document.createElement('div');
    const heading = document.createElement('h3'); heading.textContent = task.title;
    const kind = document.createElement('p'); kind.className = 'task-kind';
    const date = new Date(task.created_at);
    kind.textContent = `${task.kind === 'draft' ? 'Sample task' : realTask(task) ? 'Real AI conversation' : 'Preview conversation'} · ${Number.isNaN(date.getTime()) ? '' : date.toLocaleString([], { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })}`;
    identity.append(heading, kind);
    const status = document.createElement('span'); status.className = `task-status ${task.status}`; status.textContent = titleCase(task.status);
    top.append(identity, status); card.append(top);
    if (task.result && (task.kind === 'draft' || task.status === 'failed')) { const result = document.createElement('p'); result.className = 'task-result'; result.textContent = task.result; card.append(result); }
    if (pending(task)) {
      const actions = document.createElement('div'); actions.className = 'task-actions';
      const cancel = document.createElement('button'); cancel.className = 'text-button'; cancel.textContent = 'Cancel task'; cancel.dataset.cancelTask = task.id; actions.append(cancel); card.append(actions);
    }
    fragment.append(card);
  }
  list.replaceChildren(fragment);
}

function renderConnection(state) {
  const connection = state.connection || {};
  const live = Boolean(connection.connected);
  const status = live ? connection.verified ? 'Connected' : 'Key loaded' : 'Not connected';
  $('#mode-label').textContent = live ? 'Live AI mode' : 'Preview mode';
  $('#mode-badge').classList.toggle('live-mode', live);
  $('#mode-notice').classList.toggle('live-notice', live);
  $('#mode-notice-copy').textContent = live
    ? connection.verified ? 'Real replies use your persona, relevant memories, and selected source excerpts. Voice and the 3D avatar remain off.' : 'Your key is loaded. Send a message to test real AI replies using your approved allowance.'
    : 'Preview mode is active. Replies are simulated. Connect OpenAI for real text conversations.';
  $('#connect-cta').hidden = live;
  $('#ai-connection-summary').textContent = status;
  $('#provider-status').textContent = status;
  $('#provider-status').classList.toggle('is-connected', live);
  $('#connection-ready').hidden = !live;
  $('#connection-form').hidden = live;
  if (live) $('#api-key').value = '';
  $('#connection-ready-title').textContent = connection.verified ? 'Your AI is connected.' : 'Key loaded. Ready to test.';
  $('#connection-ready-copy').textContent = connection.verified
    ? 'Real replies are working. Your key stays in memory until you disconnect or restart Presence.'
    : 'No paid call has been made to check this key. Send a message in Conversation to verify the connection.';
  $('#conversation-heading').textContent = live ? 'Your conversation' : 'Try a preview conversation';
  $('#conversation-subtitle').textContent = live ? 'Real text replies, guided by your saved persona.' : 'Scripted replies to explore the interface.';
  $('#composer-note').textContent = live
    ? livePending() ? 'Waiting for your AI’s reply…' : connection.can_send ? 'Live AI · Uses API credit · Enter to send' : 'Test allowance unavailable · See Connection'
    : 'Simulated replies · No API charge · Enter to send';
  $('#footer-status').textContent = live ? 'Saved locally · Real replies powered by OpenAI' : 'Local workspace · Simulated preview replies';
  $('#budget-limit').textContent = money(connection.budget_limit_usd);
  $('#budget-reserved').textContent = money(connection.reserved_usd, true);
  $('#budget-estimated').textContent = money(connection.estimated_cost_usd, true);
  $('#budget-remaining').textContent = money(connection.remaining_usd, true);
  $('#budget-status').textContent = !Number.isFinite(connection.budget_limit_usd) ? 'Waiting for connection details…' : livePending() ? 'A reply is in progress. Its allowance is reserved.' : live && !connection.can_send ? 'No new real replies can start with the current test allowance.' : 'Only messages you send start a paid reply.';
}

function renderState(state) {
  model.state = state;
  model.token = state.session_token;
  $('#presence-name').textContent = state.persona.name;
  $('#presence-role').textContent = state.persona.role;
  $('#tone-summary').textContent = titleCase(state.persona.tone);
  $('#length-summary').textContent = `${titleCase(state.persona.response_length)} replies`;
  if (!model.dirtyPersona && !$('#persona-form').contains(document.activeElement)) fillPersona(state.persona);
  if (state.library) renderLibrary(state.library);
  renderConnection(state);
  renderMessages(state);
  renderTasks(state);
}

let refreshing = false;
async function refresh() {
  if (refreshing) return;
  refreshing = true;
  try { const state = await api('/api/state'); renderState(state); setOnline(true); }
  catch { setOnline(false); }
  finally { refreshing = false; }
}

async function submitMessage() {
  const input = $('#message-input');
  const content = input.value.trim();
  if (!content || !canSend()) return;
  const reportId = $('#report-select').value || null;
  const projectContext = $('#project-context').checked;
  if (!model.request || model.request.content !== content || model.request.report_id !== reportId || model.request.project_context !== projectContext) model.request = { content, request_id: crypto.randomUUID(), conversation_epoch: model.state.conversation_epoch, provider: model.state.mode === 'live' ? 'openai' : 'preview', report_id: reportId, project_context: projectContext };
  model.submitting = true; setOnline(model.online);
  try {
    await api('/api/messages', model.request);
    if (input.value.trim() === content) input.value = '';
    model.request = null;
    await refresh();
    $('#message-region').scrollTop = $('#message-region').scrollHeight;
  } catch (error) { if (error.status === 409) { model.request = null; await refresh(); } toast(`${error.message} Your text is kept so you can retry.`, true); }
  finally { model.submitting = false; setOnline(model.online); input.focus(); }
}

document.addEventListener('click', async event => {
  const view = event.target.closest('[data-view]'); if (view) switchView(view.dataset.view);
  const libraryTab = event.target.closest('[data-library-tab]'); if (libraryTab) switchLibraryTab(libraryTab.dataset.libraryTab);
  const reportDiscuss = event.target.closest('[data-report-discuss]'); if (reportDiscuss) discussReport(reportDiscuss.dataset.reportDiscuss);
  const reportView = event.target.closest('[data-report-view]'); if (reportView) await readReport(reportView.dataset.reportView);
  const libraryDelete = event.target.closest('[data-library-delete]'); if (libraryDelete) reviewDelete(libraryDelete.dataset.libraryKind, libraryDelete.dataset.libraryDelete);
  const prompt = event.target.closest('[data-prompt]');
  if (prompt) { $('#message-input').value = prompt.dataset.prompt; await submitMessage(); }
  const cancel = event.target.closest('[data-cancel-task]');
  if (cancel) {
    cancel.disabled = true;
    try { const result = await api(`/api/tasks/${encodeURIComponent(cancel.dataset.cancelTask)}/cancel`, {}); toast(result.task.status === 'cancelled' ? 'Task cancelled.' : 'This task has already finished.'); await refresh(); }
    catch (error) { toast(error.message, true); cancel.disabled = false; }
  }
});

function readMemoryForm() {
  return { title: $('#memory-title').value.trim(), content: $('#memory-content').value.trim() };
}
function readReportForm() {
  return { title: $('#report-title').value.trim(), source_name: $('#report-source').value.trim(), source_url: $('#report-url').value.trim(), report_date: $('#report-date').value, content: $('#report-content').value };
}
$('#memory-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (!model.online || model.savingMemory || !model.libraryLoaded) return;
  const saved = readMemoryForm();
  model.savingMemory = true; setOnline(model.online);
  try {
    await api('/api/memories', saved);
    if (JSON.stringify(readMemoryForm()) === JSON.stringify(saved)) $('#memory-form').reset();
    $('#memory-save-status').textContent = 'Memory saved for future conversations.';
    await refreshLibrary(); await refresh(); toast('Memory saved.');
  } catch (error) { $('#memory-save-status').textContent = error.message; toast(error.message, true); }
  finally { model.savingMemory = false; setOnline(model.online); }
});
$('#report-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (!model.online || model.savingReport || model.readingFile || !model.libraryLoaded) return;
  const saved = readReportForm();
  if (saved.source_url && !safeSourceUrl(saved.source_url)) { toast('Use an https:// source link, or leave it blank.', true); return; }
  model.savingReport = true; setOnline(model.online);
  try {
    await api('/api/reports', saved);
    if (JSON.stringify(readReportForm()) === JSON.stringify(saved)) { $('#report-form').reset(); $('#report-file-status').textContent = 'Plain text or Markdown, up to 60,000 characters. Review the text before saving.'; }
    $('#report-save-status').textContent = 'Document saved. Choose “Discuss this” when you’re ready.';
    await refreshLibrary(); await refresh(); toast('Document saved to your library.');
  } catch (error) { $('#report-save-status').textContent = error.message; toast(error.message, true); }
  finally { model.savingReport = false; setOnline(model.online); }
});
$('#report-file').addEventListener('change', async event => {
  const file = event.target.files[0];
  const version = ++model.fileReadVersion;
  if (!file) return;
  const originalText = $('#report-content').value;
  model.readingFile = true; setOnline(model.online);
  try {
    if (!/\.(txt|md)$/i.test(file.name) || file.size > 240000) throw new Error('Choose a plain .txt or .md file up to 60,000 characters.');
    const text = await file.text();
    if (version !== model.fileReadVersion) return;
    if (text.length > 60000 || text.includes('\0')) throw new Error('This file must contain plain text of no more than 60,000 characters.');
    if ($('#report-content').value !== originalText) throw new Error('The text changed while your file was loading. Choose the file again if you want to replace it.');
    $('#report-content').value = text;
    if (!$('#report-title').value.trim()) $('#report-title').value = file.name.replace(/\.(txt|md)$/i, '').slice(0, 160);
    $('#report-file-status').textContent = `${file.name} · ${text.length.toLocaleString()} characters loaded. Review before saving.`;
  } catch (error) { $('#report-file-status').textContent = error.message; toast(error.message, true); }
  finally { if (version === model.fileReadVersion) { model.readingFile = false; event.target.value = ''; setOnline(model.online); } }
});
$('#library-delete-confirm').addEventListener('click', async () => {
  if (!model.online || model.deletingLibrary || !model.deleteItem) return;
  const item = model.deleteItem;
  model.deletingLibrary = true; setOnline(model.online);
  try {
    await api(`/api/${item.kind === 'memory' ? 'memories' : 'reports'}/${encodeURIComponent(item.id)}/delete`, {});
    $('#library-delete-dialog').close(); model.deleteItem = null;
    await refreshLibrary(); await refresh(); toast(item.kind === 'memory' ? 'Memory removed from your library.' : 'Document removed from your library.');
  } catch (error) { toast(error.message, true); }
  finally { model.deletingLibrary = false; setOnline(model.online); }
});
$('.library-tabs').addEventListener('keydown', event => {
  if (!['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
  event.preventDefault();
  const next = event.key === 'Home' ? 'memory' : event.key === 'End' ? 'documents' : $('#memory-tab').getAttribute('aria-selected') === 'true' ? 'documents' : 'memory';
  switchLibraryTab(next);
  $(`#${next === 'memory' ? 'memory' : 'documents'}-tab`).focus();
});
$('#reader-close').addEventListener('click', () => $('#report-reader').close());
$('#reader-discuss').addEventListener('click', () => { if (model.readerReport) discussReport(model.readerReport.id); });

$('#connection-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (!model.online || model.connecting || model.disconnecting) return;
  const input = $('#api-key');
  const key = input.value.trim();
  // Never retain a credential in the field or browser storage after submission.
  input.value = '';
  if (!key) return;
  model.connecting = true;
  $('#connection-save-status').textContent = 'Loading your key for this session…';
  setOnline(model.online);
  try {
    await api('/api/connection', { api_key: key });
    $('#connection-save-status').textContent = 'Key loaded. No paid call was made.';
    await refresh();
    toast('Key loaded. Send a message to test your AI.');
  } catch (error) {
    $('#connection-save-status').textContent = error.message;
    toast(error.message, true);
  } finally { model.connecting = false; setOnline(model.online); }
});
$('#disconnect-ai').addEventListener('click', async () => {
  if (!model.online || model.connecting || model.disconnecting) return;
  model.disconnecting = true;
  setOnline(model.online);
  try {
    await api('/api/connection/disconnect', {});
    $('#connection-save-status').textContent = 'Disconnected. Enter a key to reconnect.';
    await refresh();
    toast('Disconnected. Preview mode is active. In-progress AI calls may still be billed.');
  } catch (error) { toast(error.message, true); }
  finally { model.disconnecting = false; setOnline(model.online); }
});

$('#message-form').addEventListener('submit', event => { event.preventDefault(); submitMessage(); });
$('#message-input').addEventListener('keydown', event => { if (event.key === 'Enter' && !event.shiftKey && !event.isComposing) { event.preventDefault(); submitMessage(); } });
$('#persona-form').addEventListener('input', () => { model.dirtyPersona = true; $('#persona-save-status').textContent = 'You have unsaved changes.'; renderPersonaPreview(); });
$('#persona-form').addEventListener('submit', async event => {
  event.preventDefault();
  if (model.savingPersona || !model.online) return;
  model.savingPersona = true;
  const saved = readPersona();
  $('#persona-save').disabled = true;
  try {
    await api('/api/persona', saved);
    // Preserve edits typed while the save was in flight.
    model.dirtyPersona = JSON.stringify(readPersona()) !== JSON.stringify(saved);
    $('#persona-save-status').textContent = model.dirtyPersona ? 'New edits are not saved yet.' : 'Persona saved on this computer.';
    toast('Persona saved. New conversations will use this style.');
    await refresh();
  } catch (error) { toast(error.message, true); }
  finally { model.savingPersona = false; setOnline(model.online); }
});
$('#task-form').addEventListener('submit', async event => {
  event.preventDefault(); const input = $('#task-title'); const title = input.value.trim(); if (!title || !model.online || model.creatingTask) return;
  model.creatingTask = true;
  const button = $('#task-form button'); button.disabled = true;
  try { await api('/api/tasks', { title, kind: 'draft' }); input.value = ''; await refresh(); toast('Sample task added.'); }
  catch (error) { toast(error.message, true); }
  finally { model.creatingTask = false; setOnline(model.online); }
});
$('#stop-reply').addEventListener('click', async () => {
  const button = $('#stop-reply'); button.disabled = true;
  try { for (const task of model.state.tasks.filter(task => replyTask(task) && pending(task))) await api(`/api/tasks/${encodeURIComponent(task.id)}/cancel`, {}); await refresh(); toast('Replies stopped. A real reply already in progress may still be billed.'); }
  catch (error) { toast(error.message, true); }
  finally { button.disabled = false; }
});
$('#reset-open').addEventListener('click', () => $('#reset-dialog').showModal());
$('#reset-confirm').addEventListener('click', async () => {
  if (model.submitting || model.resetting || !model.online) return;
  model.resetting = true; setOnline(model.online);
  const button = $('#reset-confirm'); button.disabled = true;
  try { await api('/api/conversation/reset', {}); model.request = null; $('#reset-dialog').close(); await refresh(); toast('Conversation reset. Your persona and library are saved.'); }
  catch (error) { toast(error.message, true); }
  finally { model.resetting = false; button.disabled = false; setOnline(model.online); }
});
window.addEventListener('hashchange', () => switchView(location.hash.slice(1)));
window.addEventListener('beforeunload', event => { if (model.dirtyPersona || Object.values(readMemoryForm()).some(Boolean) || Object.values(readReportForm()).some(Boolean)) { event.preventDefault(); event.returnValue = ''; } });
document.addEventListener('visibilitychange', () => { if (!document.hidden) refresh(); });
switchView(location.hash.slice(1));
switchLibraryTab('memory');
setOnline(false);
await refresh();
if (!model.libraryLoaded && model.online) await refreshLibrary();
async function poll() { await refresh(); setTimeout(poll, document.hidden ? 3000 : 850); }
setTimeout(poll, 850);
