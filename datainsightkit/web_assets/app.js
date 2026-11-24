
const $ = id => document.getElementById(id);
let report;
let activeDataset;
let source = 'Pasted CSV';
const percent = new Intl.NumberFormat(undefined, {style:'percent', maximumFractionDigits:1});
let request = 0;
const displayNumber = new Intl.NumberFormat(undefined, {maximumFractionDigits: 3});
const format = value => typeof value === 'number' ? displayNumber.format(value) : value;
const edgeFormat = new Intl.NumberFormat(undefined, {maximumSignificantDigits: 12});


function inspectColumn(name, col) {
  const panel = $('column-detail');
  const title = node('h3', name);
  title.tabIndex = -1;
  const entries = col.distribution ? Object.entries(col.distribution) : col.top_values;
  const body = node('div', '', 'detail-list');
  for (const [label, value] of entries) {
    const item = node('div', '');
    item.append(node('strong', format(value)), node('span', label));
    body.append(item);
  }
  panel.replaceChildren(title, entries.length ? body : node('p', 'No observed values.', 'muted'));
  if (activeDataset) {
    const control = node('label', '', 'override');
    const toggle = document.createElement('input');
    toggle.type = 'checkbox';
    toggle.checked = report.categorical_overrides.includes(name);
    control.append(toggle, node('span', 'Treat ' + name + ' as categorical'));
    toggle.addEventListener('change', async () => {
      const categorical = new Set(report.categorical_overrides);
      if (toggle.checked) categorical.add(name);
      else categorical.delete(name);
      toggle.disabled = true;
      if (!await profile({...activeDataset, categorical: [...categorical]}, name)) {
        toggle.checked = !toggle.checked;
        toggle.disabled = false;
      }
    });
    panel.append(control);
  }
  if (col.histogram) {
    const figure = node('div', '', 'histogram');
    figure.append(node('h3', 'Distribution'));
    const maximum = Math.max(...col.histogram.map(bin => bin.count));
    col.histogram.forEach((bin, index) => {
      const closing = index === col.histogram.length - 1 ? ']' : ')';
      const row = barRow(`[${edgeFormat.format(bin.lower)}, ${edgeFormat.format(bin.upper)}${closing}`,
        bin.count, maximum, format(bin.count));
      row.title = `[${bin.lower}, ${bin.upper}${closing}`;
      figure.append(row);
    });
    panel.append(figure);
  }
  panel.hidden = false;
  title.focus();
}

function node(tag, value, className) {
  const element = document.createElement(tag);
  element.textContent = value;
  if (className) element.className = className;
  return element;
}
function renderColumns() {
  if (!report) return;
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
    const nameCell = node('td', '');
    const button = node('button', name);
    button.type = 'button';
    button.setAttribute('aria-label', 'Inspect ' + name);
    button.addEventListener('click', () => inspectColumn(name, col));
    nameCell.append(button);
    tr.append(nameCell, node('td', col.kind), missing, node('td', format(col.distinct)),
      node('td', format(typical)), node('td', col.potential_outliers ?? '—'));
    return tr;
  }));
}
function barRow(name, value, max, reading) {
  const row = node('div', '', 'segment');
  const bar = document.createElement('progress');
  bar.max = max;
  bar.value = value;
  bar.setAttribute('aria-label', name);
  row.append(node('span', name), bar, node('strong', reading));
  return row;
}
function render(value, dataset, selectedColumn) {
  report = value;
  activeDataset = dataset;
  $('source').textContent = value.source?.name ?? dataset.name;
  if (!selectedColumn) $('filter').value = '';
  $('column-detail').hidden = true;
  $('numbers').replaceChildren(...[['Rows', value.rows], ['Columns', value.column_count],
    ['Identical row repeats', value.quality.duplicate_rows], ['Missing values', Object.values(value.columns).reduce((sum, col) => sum + col.missing, 0)]].map(([name, count]) => {
    const card = node('div', '', 'metric');
    card.append(node('strong', format(count)), node('small', name));
    return card;
  }));
  const warnings = value.quality.columns_at_least_half_missing;
  $('warnings').textContent = warnings.length ? 'At least half missing: ' + warnings.join(', ') : 'No columns are at least half missing.';
  $('pairs').replaceChildren(...(value.associations.length ? value.associations.slice(0, 12).map(pair =>
    node('div', `${pair.left} × ${pair.right} · r = ${pair.pearson_r.toFixed(2)} · ${pair.pairs} pairs`, 'pair'))
    : [node('p', 'No eligible numeric pairs.', 'muted')]));
  $('case-study').hidden = !value.case_study;
  if (value.case_study) {
    const detail = value.case_study;
    $('attribution').href = value.source.url;
    $('conversion').textContent = `${percent.format(detail.purchases / value.rows)} overall · ${format(detail.purchases)} purchases`;
    const scale = 1;
    $('segments').replaceChildren(...detail.segments.map(segment => barRow(segment.name, segment.rate, scale,
      `${percent.format(segment.rate)} · n=${format(segment.sessions)}`)));
  }
  for (const id of ['overview', 'details', 'links', 'download', 'jump']) $(id).hidden = false;
  renderColumns();
  if (selectedColumn) inspectColumn(selectedColumn, value.columns[selectedColumn]);
}
async function profile(dataset = null, selectedColumn = null) {
  const current = ++request;
  const status = $('status');
  status.textContent = 'Analysing…';
  status.classList.remove('error');
  try {
    const response = dataset ? await fetch('/api/profile', {
      method:'POST', headers:{'Content-Type':'application/json'},
      body:JSON.stringify({csv:dataset.csv, categorical:dataset.categorical})
    }) : await fetch('/api/sample');
    const value = await response.json();
    if (current !== request) return false;
    if (!response.ok) throw new Error(value.error);
    render(value, dataset, selectedColumn);
    status.textContent = selectedColumn ? 'Column types updated.' : 'Profile ready.';
    return true;
  } catch (error) {
    if (current !== request) return false;
    status.textContent = error.message;
    status.classList.add('error');
    return false;
  }
}
$('profile').addEventListener('submit', event => { event.preventDefault(); profile({csv:$('csv').value, name:source, categorical:[]}); });
$('csv').addEventListener('input', () => { source = 'Pasted CSV'; $('file').value = ''; });
$('filter').addEventListener('input', renderColumns);
$('sample').addEventListener('click', () => profile());
$('file').addEventListener('change', async () => {
  const file = $('file').files[0];
  if (!file) return;
  if (file.size > 2 * 1024 * 1024) { $('status').textContent = 'That file is larger than 2 MiB.'; return; }
  const read = ++request;
  try {
    const csv = new TextDecoder('utf-8', {fatal:true}).decode(await file.arrayBuffer());
    if (read !== request) return;
    $('csv').value = csv;
    source = file.name;
    await profile({csv, name:source, categorical:[]});
  } catch (error) {
    if (read !== request) return;
    $('status').textContent = 'Unable to read the file as UTF-8 CSV.';
    $('status').classList.add('error');
  }
});
$('download').addEventListener('click', () => {
  const url = URL.createObjectURL(new Blob([JSON.stringify(report, null, 2)], {type:'application/json'}));
  const link = Object.assign(document.createElement('a'), {href:url, download:'csv-profile.json'});
  link.click();
  setTimeout(() => URL.revokeObjectURL(url), 1000);
});

profile();
