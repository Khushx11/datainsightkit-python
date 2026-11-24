
const $ = id => document.getElementById(id);
let report;

function node(tag, value, className) {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  return element;
}
function renderColumns() {
  const filter = $('filter').value.toLowerCase();
  const rows = Object.entries(report.columns).filter(([name]) => name.toLowerCase().includes(filter));
  $('columns').replaceChildren(...rows.map(([name, col]) => {
    const tr = node('tr', '');
    const typical = col.distribution?.median ?? col.top_values[0]?.[0] ?? '—';
    const missing = node('td', col.missing + ' ');
    const meter = document.createElement('meter');
    meter.min = 0;
    meter.max = report.rows;
    meter.value = col.missing;
    meter.setAttribute('aria-label', 'Missing rows');
    missing.append(meter);
    tr.append(node('td', name), node('td', col.kind), missing, node('td', col.distinct),
      node('td', typical), node('td', col.potential_outliers ?? '—'));
    return tr;
  }));
}
function render(value) {
  report = value;
  $('numbers').replaceChildren(...[['Rows', value.rows], ['Columns', value.column_count],
    ['Duplicates', value.quality.duplicate_rows]].map(([name, count]) => {
    const card = node('div', '', 'metric');
    card.append(node('strong', count), node('small', name));
    return card;
  }));
  const warnings = value.quality.columns_at_least_half_missing;
  $('warnings').textContent = warnings.length ? 'At least half missing: ' + warnings.join(', ') : 'No columns are at least half missing.';
  $('pairs').replaceChildren(...(value.associations.length ? value.associations.slice(0, 12).map(pair =>
    node('div', `${pair.left} × ${pair.right} · r = ${pair.pearson_r.toFixed(2)} · ${pair.pairs} pairs`, 'pair'))
    : [node('p', 'No eligible numeric pairs.', 'muted')]));
  $('empty').hidden = true;
  for (const id of ['overview', 'details', 'links']) $(id).hidden = false;
  renderColumns();
}
async function profile() {
  const status = $('status');
  status.textContent = 'Analysing…';
  status.classList.remove('error');
  try {
    const response = await fetch('/api/profile', {method:'POST', body:$('csv').value});
    const value = await response.json();
    if (!response.ok) throw new Error(value.error);
    render(value);
    status.textContent = 'Profile ready.';
  } catch (error) {
    status.textContent = error.message;
    status.classList.add('error');
  }
}
$('profile').addEventListener('submit', event => { event.preventDefault(); profile(); });
$('filter').addEventListener('input', renderColumns);
$('sample').addEventListener('click', async () => {
  try {
    const response = await fetch('/sample.csv');
    if (!response.ok) throw new Error('Sample could not be loaded.');
    $('csv').value = await response.text();
    $('file').value = '';
    await profile();
  } catch (error) { $('status').textContent = error.message; }
});
$('file').addEventListener('change', async () => {
  const file = $('file').files[0];
  if (!file) return;
  if (file.size > 1024 * 1024) { $('status').textContent = 'That file is larger than 1 MB.'; return; }
  try { $('csv').value = await file.text(); await profile(); }
  catch (error) { $('status').textContent = error.message; }
});
$('download').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type:'application/json'}));
  const link = Object.assign(document.createElement('a'), {href:url, download:'csv-profile.json'});
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});
