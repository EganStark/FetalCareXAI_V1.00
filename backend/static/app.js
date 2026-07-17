const state = {
  schema: null,
  modelCard: null,
  lastInput: null,
  lastResult: null,
  lastExplanation: null,
  comparisonBase: null,
  analytics: { assessments: 0, explanations: 0, confidenceTotal: 0, responseTotal: 0, classes: { Normal: 0, Suspect: 0, Pathological: 0 } }
};

const groups = [
  { title: 'Heart rate & events', match: ['baseline value','accelerations','fetal_movement','uterine_contractions','light_decelerations','severe_decelerations','prolongued_decelerations'] },
  { title: 'Variability', match: ['mean_value_of_short_term_variability','abnormal_short_term_variability','mean_value_of_long_term_variability','percentage_of_time_with_abnormal_long_term_variability'] },
  { title: 'Histogram profile', match: ['histogram_width','histogram_min','histogram_number_of_peaks','histogram_mode','histogram_mean','histogram_median','histogram_variance','histogram_tendency'] }
];

const labels = {
  'baseline value': 'Baseline fetal heart rate', accelerations: 'Accelerations', fetal_movement: 'Fetal movement',
  uterine_contractions: 'Uterine contractions', light_decelerations: 'Light decelerations', severe_decelerations: 'Severe decelerations',
  mean_value_of_short_term_variability: 'Mean short-term variability', mean_value_of_long_term_variability: 'Mean long-term variability',
  prolongued_decelerations: 'Prolonged decelerations', abnormal_short_term_variability: 'Abnormal short-term variability',
  percentage_of_time_with_abnormal_long_term_variability: 'Abnormal long-term variability time',
  histogram_width: 'Histogram width', histogram_min: 'Histogram minimum', histogram_number_of_peaks: 'Histogram peaks', histogram_mode: 'Histogram mode', histogram_mean: 'Histogram mean',
  histogram_median: 'Histogram median', histogram_variance: 'Histogram variance', histogram_tendency: 'Histogram tendency'
};

const presets = {
  normal: {prolongued_decelerations:0,abnormal_short_term_variability:20,percentage_of_time_with_abnormal_long_term_variability:5,histogram_mean:135,histogram_mode:134,histogram_median:135,accelerations:.003,histogram_variance:45,'baseline value':125,mean_value_of_short_term_variability:1.8,uterine_contractions:.003,histogram_min:85,mean_value_of_long_term_variability:12,light_decelerations:.001,histogram_width:95,histogram_tendency:.1,severe_decelerations:0,histogram_number_of_peaks:3,fetal_movement:.08},
  suspect: {prolongued_decelerations:.001,abnormal_short_term_variability:45,percentage_of_time_with_abnormal_long_term_variability:25,histogram_mean:145,histogram_mode:144,histogram_median:144,accelerations:.001,histogram_variance:75,'baseline value':140,mean_value_of_short_term_variability:1.2,uterine_contractions:.008,histogram_min:70,mean_value_of_long_term_variability:25,light_decelerations:.006,histogram_width:120,histogram_tendency:.4,severe_decelerations:0,histogram_number_of_peaks:6,fetal_movement:.02},
  pathological: {prolongued_decelerations:.003,abnormal_short_term_variability:75,percentage_of_time_with_abnormal_long_term_variability:85,histogram_mean:165,histogram_mode:165,histogram_median:164,accelerations:0,histogram_variance:120,'baseline value':155,mean_value_of_short_term_variability:.4,uterine_contractions:.012,histogram_min:55,mean_value_of_long_term_variability:45,light_decelerations:.012,histogram_width:150,histogram_tendency:.8,severe_decelerations:.001,histogram_number_of_peaks:12,fetal_movement:.005}
};

const $ = (selector) => document.querySelector(selector);
const escapeHTML = (value) => String(value).replace(/[&<>'"]/g, char => ({'&':'&amp;','<':'&lt;','>':'&gt;',"'":'&#39;','"':'&quot;'}[char]));
const humanize = (name) => labels[name] || name.replaceAll('_', ' ').replace(/\b\w/g, c => c.toUpperCase());
const percent = (value) => `${Math.round(Number(value) * 100)}%`;

async function request(path, options = {}) {
  const response = await fetch(path, { headers: { 'Content-Type': 'application/json' }, ...options });
  const body = await response.json().catch(() => ({}));
  if (!response.ok) throw new Error(body.error || 'The service could not complete this request.');
  return body;
}

function showView(name) {
  document.querySelectorAll('.view').forEach(view => view.classList.toggle('active', view.id === `${name}-view`));
  document.querySelectorAll('.nav-link').forEach(button => button.classList.toggle('active', button.dataset.view === name));
  if (name === 'analytics') updateAnalytics();
  window.scrollTo({ top: 0, behavior: 'smooth' });
}

function fieldHTML(name, meta) {
  const step = meta.max <= 1 ? '0.001' : meta.type === 'int' ? '1' : '0.1';
  return `<div class="field"><label for="${name}">${escapeHTML(humanize(name))}<span>${meta.min}–${meta.max}</span></label><input id="${name}" name="${name}" type="number" min="${meta.min}" max="${meta.max}" step="${step}" inputmode="decimal" required aria-describedby="${name}-help"><small id="${name}-help">${escapeHTML(meta.description || 'Model input measurement')}</small></div>`;
}

function renderSchema() {
  const features = state.schema.features;
  $('#formFields').innerHTML = groups.map(group => `<section class="field-group"><h3 class="group-title">${group.title}</h3><div class="fields">${group.match.filter(name => features[name]).map(name => fieldHTML(name, features[name])).join('')}</div></section>`).join('');
  renderFeatureReference();
}

function renderFeatureReference(query = '') {
  const term = query.trim().toLowerCase(); const features = state.schema.features;
  const matches = state.schema.required.filter(name => `${humanize(name)} ${features[name].description}`.toLowerCase().includes(term));
  $('#featureReference').innerHTML = matches.length ? matches.map(name => { const meta = features[name]; return `<div class="reference-item"><strong>${escapeHTML(humanize(name))}</strong><span>${escapeHTML(meta.description)}</span><small>Accepted: ${meta.min}–${meta.max}</small></div>`; }).join('') : '<p class="no-results">No measurements match that search.</p>';
}

function getInput() {
  const data = {}; let valid = true;
  state.schema.required.forEach(name => {
    const input = document.getElementById(name); const value = Number(input.value);
    const invalid = input.value === '' || !Number.isFinite(value) || value < Number(input.min) || value > Number(input.max);
    input.classList.toggle('invalid', invalid); input.setAttribute('aria-invalid', String(invalid));
    if (invalid) valid = false; else data[name] = value;
  });
  if (!valid) throw new Error('Complete every measurement using a value inside its accepted range.');
  return data;
}

function showAlert(message) { const alert = $('#formAlert'); alert.textContent = message; alert.classList.remove('hidden'); alert.scrollIntoView({ behavior: 'smooth', block: 'center' }); }
function setLoading(active, text = 'Analyzing measurements…') { $('#loadingText').textContent = text; $('#loadingOverlay').classList.toggle('hidden', !active); }
function toast(message) { const el = $('#toast'); el.textContent = message; el.classList.remove('hidden'); setTimeout(() => el.classList.add('hidden'), 2600); }
function setJourney(stage) { document.querySelectorAll('.journey>div').forEach((item,index) => { item.classList.toggle('active', index === stage); item.classList.toggle('complete', index < stage); }); }
function updateCompletion() { const completed = state.schema.required.filter(name => document.getElementById(name)?.value !== '').length; $('#completionCount').textContent = `${completed}/${state.schema.required.length}`; }
function loadPreset(type) {
  let selected = type;
  if (type === 'random') selected = ['normal', 'suspect', 'pathological'][Math.floor(Math.random() * 3)];
  const source = presets[selected];
  Object.entries(source).forEach(([name, base]) => {
    const input = document.getElementById(name); if (!input) return;
    let value = base;
    if (type === 'random' && base !== 0) {
      const variation = selected === 'suspect' ? .004 : .015;
      value = base * (1 + (Math.random() * 2 - 1) * variation);
      value = Math.min(Number(input.max), Math.max(Number(input.min), value));
      value = Number(value.toFixed(Number(input.step) < .01 ? 4 : 2));
    }
    input.value = value; input.classList.remove('invalid');
  });
  $('#formAlert').classList.add('hidden'); updateCompletion();
  toast(type === 'random' ? 'Randomized valid demo loaded — run it to discover the class' : `${selected[0].toUpperCase()+selected.slice(1)} demo loaded`);
}

function parseCSVLine(line) {
  const values = []; let value = ''; let quoted = false;
  for (let index = 0; index < line.length; index += 1) {
    const char = line[index];
    if (char === '"' && quoted && line[index + 1] === '"') { value += '"'; index += 1; }
    else if (char === '"') quoted = !quoted;
    else if (char === ',' && !quoted) { values.push(value.trim()); value = ''; }
    else value += char;
  }
  values.push(value.trim()); return values;
}
function importCSV(file) {
  if (!file || file.size > 64 * 1024) { showAlert('Choose a CSV file smaller than 64 KB.'); return; }
  const reader = new FileReader();
  reader.onload = () => {
    try {
      const lines = String(reader.result).replace(/^\uFEFF/, '').split(/\r?\n/).filter(line => line.trim());
      if (lines.length < 2) throw new Error('The CSV must contain a header row and at least one data row.');
      const headers = parseCSVLine(lines[0]); const values = parseCSVLine(lines[1]);
      const record = Object.fromEntries(headers.map((header,index) => [header.trim(), values[index]]));
      const missing = state.schema.required.filter(name => !(name in record));
      if (missing.length) throw new Error(`Missing columns: ${missing.map(humanize).join(', ')}`);
      state.schema.required.forEach(name => { const value = Number(record[name]); if (!Number.isFinite(value)) throw new Error(`${humanize(name)} is not numeric.`); document.getElementById(name).value = value; });
      getInput(); updateCompletion(); $('#formAlert').classList.add('hidden'); toast('First CSV data row imported and validated');
    } catch (error) { showAlert(error.message); }
  };
  reader.onerror = () => showAlert('The CSV file could not be read.'); reader.readAsText(file);
}
function downloadCSVTemplate() {
  const headers = state.schema.required.map(name => name.includes(' ') ? `"${name}"` : name).join(',');
  const examples = state.schema.required.map(name => presets.normal[name]).join(',');
  const url = URL.createObjectURL(new Blob([`${headers}\n${examples}\n`], { type: 'text/csv' }));
  const link = document.createElement('a'); link.href = url; link.download = 'fetalcare-ctg-template.csv'; link.click(); URL.revokeObjectURL(url);
}

function renderResult(result) {
  const status = result.class_label.toLowerCase();
  const guidance = { Normal: 'The model found a pattern most consistent with its Normal class.', Suspect: 'The model found a pattern most consistent with its Suspect class. Clinical review is essential.', Pathological: 'The model found a pattern most consistent with its Pathological class. This is not an emergency alert; seek qualified clinical interpretation.' }[result.class_label];
  const probabilities = Object.entries(result.probabilities).map(([label, value]) => `<div class="probability-row"><span>${label}</span><div class="probability-track"><div class="probability-fill" style="width:${percent(value)}"></div></div><strong>${percent(value)}</strong></div>`).join('');
  const uncertainty = result.confidence < .70 ? `<div class="low-confidence"><strong>Closely divided model output</strong>The leading probability is below 70%, so the model shows greater uncertainty between classes. Interpret with additional caution.</div>` : '';
  const compareLabel = state.comparisonBase ? 'Compare with saved A' : 'Save as comparison A';
  $('#resultContent').innerHTML = `<span class="result-kicker">Model classification</span><div class="classification ${status}"><h3>${escapeHTML(result.class_label)}</h3><p>${escapeHTML(guidance)}</p></div>${uncertainty}<div class="interpretation"><div><strong>What this means</strong><span>The highest of three model probabilities determined this label.</span></div><div><strong>What this does not mean</strong><span>It is not a diagnosis, risk score, or instruction for treatment.</span></div></div><div class="confidence-head"><span>Probability distribution</span><strong>${percent(result.confidence)}</strong></div>${probabilities}<p class="result-disclaimer">The large percentage is confidence in the selected model class. It is not certainty or clinical accuracy for an individual case.</p><div class="result-buttons"><button class="button primary explain-button" id="explainBtn" type="button">Explain measurements</button><button class="button subtle" id="compareBtn" type="button">${compareLabel}</button><button class="button subtle" id="printBtn" type="button">Print / Save PDF</button></div><div id="explanation" class="explanation hidden"></div>`;
  $('#resultEmpty').classList.add('hidden'); $('#resultContent').classList.remove('hidden');
  $('#explainBtn').addEventListener('click', explainResult);
  $('#printBtn').addEventListener('click', printAssessment);
  $('#compareBtn').addEventListener('click', handleComparison);
  setJourney(1);
  $('#resultPanel').scrollIntoView({ behavior: 'smooth', block: 'center' });
}

async function runPrediction(event) {
  event.preventDefault(); $('#formAlert').classList.add('hidden');
  try {
    const data = getInput(); setLoading(true); const started = performance.now();
    const result = await request('/predict', { method: 'POST', body: JSON.stringify(data) });
    const responseMs = performance.now() - started; state.lastInput = data; state.lastResult = result; state.lastExplanation = null;
    const a = state.analytics; a.assessments += 1; a.confidenceTotal += result.confidence; a.responseTotal += responseMs; a.classes[result.class_label] += 1;
    renderResult(result);
  } catch (error) { showAlert(error.message); } finally { setLoading(false); }
}

async function explainResult() {
  const button = $('#explainBtn'); button.disabled = true; setLoading(true, 'Generating local explanation…');
  try {
    const result = await request('/explain', { method: 'POST', body: JSON.stringify(state.lastInput) });
    const max = Math.max(...result.explanations.map(item => Math.abs(item.weight)), 0.001);
    const rows = result.explanations.slice(0, 8).map(item => { const width = Math.max(4, Math.abs(item.weight) / max * 100); return `<div class="impact-row"><div class="impact-head"><strong>${escapeHTML(item.feature)}</strong><span>${item.weight > 0 ? 'supports result' : 'opposes result'} · ${escapeHTML(item.value)}</span></div><div class="impact-track"><div class="impact-fill ${item.weight < 0 ? 'negative' : ''}" style="width:${width}%"></div></div></div>`; }).join('');
    const graph = result.graph_url ? `<figure class="lime-figure"><div class="figure-head"><div><strong>Original LIME weight chart</strong><span>Generated by the backend for this exact assessment</span></div><a href="${escapeHTML(result.graph_url)}" target="_blank" rel="noopener">Open full size ↗</a></div><img src="${escapeHTML(result.graph_url)}" alt="LIME horizontal bar chart showing local feature weights for this prediction"><figcaption>Bars to the right have positive weight for the selected class; bars to the left have negative weight. Bar length represents the magnitude of local influence.</figcaption></figure>` : '';
    const panel = $('#explanation'); panel.innerHTML = `<h3>What influenced this result</h3><p>LIME builds a small, interpretable approximation around this exact set of measurements. Longer bars represent stronger local influence on the selected class.</p><p class="explanation-note"><strong>How to read direction:</strong> “Supports result” pushed the approximation toward the displayed class; “opposes result” pushed away from it. Neither direction means medically healthy or unhealthy.</p>${rows}${graph}<p class="explanation-note">These influences can change when any input changes. They explain this prediction only and are not global feature importance or causal medical evidence.</p>`; panel.classList.remove('hidden');
    button.remove(); state.lastExplanation = result; state.analytics.explanations += 1; setJourney(2);
  } catch (error) { toast(error.message); button.disabled = false; } finally { setLoading(false); }
}

function updateAnalytics() {
  const a = state.analytics; $('#metricAssessments').textContent = a.assessments; $('#metricExplanations').textContent = a.explanations;
  $('#metricConfidence').textContent = a.assessments ? percent(a.confidenceTotal / a.assessments) : '—';
  $('#metricResponse').textContent = a.assessments ? `${Math.round(a.responseTotal / a.assessments)} ms` : '—';
  $('#classMix').innerHTML = Object.entries(a.classes).map(([label,count]) => { const share = a.assessments ? Math.round(count/a.assessments*100) : 0; return `<div class="mix-item ${label.toLowerCase()}"><div><span>${label}</span><strong>${count}</strong></div><div class="mix-track"><i style="width:${share}%"></i></div><small>${share}% of this session</small></div>`; }).join('');
}

function printAssessment() {
  if (!state.lastInput || !state.lastResult) return;
  const model = state.modelCard.model; const result = state.lastResult;
  const probabilities = Object.entries(result.probabilities).map(([label,value]) => `<tr><th>${escapeHTML(label)}</th><td>${percent(value)}</td></tr>`).join('');
  const inputs = Object.entries(state.lastInput).map(([name,value]) => `<tr><th>${escapeHTML(humanize(name))}</th><td>${escapeHTML(value)}</td></tr>`).join('');
  const graph = state.lastExplanation?.graph_url ? `<img src="${escapeHTML(state.lastExplanation.graph_url)}" alt="LIME explanation chart">` : '<p>Generate an explanation before printing to include the LIME chart.</p>';
  $('#printReport').innerHTML = `<header><h1>FetalCare XAI assessment report</h1><p>Generated ${new Date().toLocaleString()}</p></header><section><h2>Model result: ${escapeHTML(result.class_label)}</h2><p>Leading model probability: ${percent(result.confidence)}</p><table>${probabilities}</table></section><section><h2>CTG measurements</h2><table>${inputs}</table></section><section><h2>Local explanation</h2>${graph}</section><footer><strong>Research use only — not a diagnosis or medical device.</strong><p>Model version ${escapeHTML(model.version)} · Artifact ${escapeHTML(model.artifact_hash)}</p></footer>`;
  window.print();
}

function handleComparison() {
  if (!state.comparisonBase) {
    state.comparisonBase = { input: { ...state.lastInput }, result: JSON.parse(JSON.stringify(state.lastResult)) };
    $('#compareBtn').textContent = 'Saved as comparison A'; $('#compareBtn').disabled = true;
    toast('Assessment A saved in memory. Change values and run another assessment.'); return;
  }
  renderComparison(state.comparisonBase, { input: state.lastInput, result: state.lastResult });
}

function resultSummary(label, snapshot) {
  return `<article class="comparison-result"><span>Assessment ${label}</span><h3 class="${snapshot.result.class_label.toLowerCase()}">${escapeHTML(snapshot.result.class_label)}</h3><strong>${percent(snapshot.result.confidence)} confidence</strong>${Object.entries(snapshot.result.probabilities).map(([name,value]) => `<div class="compare-prob"><span>${name}</span><i><b style="width:${percent(value)}"></b></i><small>${percent(value)}</small></div>`).join('')}</article>`;
}

function renderComparison(base, current) {
  const changed = state.schema.required.filter(name => Number(base.input[name]) !== Number(current.input[name]));
  const rows = changed.map(name => { const before = base.input[name]; const after = current.input[name]; const delta = Number(after) - Number(before); return `<tr><th>${escapeHTML(humanize(name))}</th><td>${escapeHTML(before)}</td><td>${escapeHTML(after)}</td><td class="${delta > 0 ? 'up' : 'down'}">${delta > 0 ? '+' : ''}${Number(delta.toFixed(4))}</td></tr>`; }).join('');
  $('#comparisonContent').innerHTML = `<div class="comparison-results">${resultSummary('A',base)}${resultSummary('B',current)}</div><section class="changed-values"><div class="comparison-subhead"><div><h3>Changed measurements</h3><p>${changed.length} of ${state.schema.required.length} values differ.</p></div><button class="button text" id="clearComparison" type="button">Clear saved A</button></div>${changed.length ? `<div class="table-scroll"><table><thead><tr><th>Measurement</th><th>A</th><th>B</th><th>Change</th></tr></thead><tbody>${rows}</tbody></table></div>` : '<p>No measurement values changed.</p>'}</section>`;
  $('#clearComparison').addEventListener('click', () => { state.comparisonBase = null; $('#comparisonDialog').close(); toast('Saved comparison cleared'); });
  $('#comparisonDialog').showModal();
}

const classCopy = {
  Normal: { title: 'Normal pattern class', text: 'The model assigns this when the input pattern most closely resembles its learned Normal class.', note: 'It does not confirm fetal wellbeing or remove the need for clinical interpretation.' },
  Suspect: { title: 'Suspect pattern class', text: 'The model assigns this when the input pattern most closely resembles its learned intermediate or concerning class.', note: 'It is not a diagnosis or a standardized clinical escalation level.' },
  Pathological: { title: 'Pathological pattern class', text: 'The model assigns this when the input pattern most closely resembles its learned Pathological class.', note: 'The application does not issue an emergency alert; qualified clinical evaluation is required.' }
};
function showClassExplanation(name) { const item = classCopy[name]; $('#classExplanation').innerHTML = `<span class="class-dot ${name.toLowerCase()}"></span><div><h3>${item.title}</h3><p>${item.text}</p><small>${item.note}</small></div>`; document.querySelectorAll('.class-tab').forEach(button => button.classList.toggle('active', button.dataset.class === name)); }

function renderModelCard() {
  const card = state.modelCard; const model = card.model; const metrics = card.evaluation.metrics;
  $('#modelIdentity').innerHTML = `<div class="model-identity-main"><span class="live-badge"><i></i>Loaded model</span><h2>${escapeHTML(model.name)}</h2><p>${model.features} CTG features · ${model.classes.length} classes · ${escapeHTML(model.algorithm)}</p></div><div class="model-version"><span>Model version</span><strong>${escapeHTML(model.version)}</strong><small>Artifact ${escapeHTML(model.artifact_hash)}</small></div>`;
  const items = [
    ['Accuracy', metrics.accuracy, 'Overall recorded accuracy'],
    ['Macro F1', metrics.macro_f1, 'Equal class weighting'],
    ['ROC AUC', metrics.roc_auc_ovr, 'Not available'],
  ];
  $('#evaluationMetrics').innerHTML = items.map(([label,value,note]) => `<article class="evidence-metric ${value == null ? 'missing' : ''}"><span>${label}</span><strong>${value == null ? '—' : percent(value)}</strong><small>${note}</small></article>`).join('');
  const dataset = card.provenance.dataset; const total = Object.values(dataset.class_counts).reduce((sum,count) => sum + count, 0);
  $('#datasetProfile').innerHTML = `<section class="dataset-profile"><div class="dataset-summary"><div><span class="eyebrow">Supplied dataset</span><h3>${dataset.rows.toLocaleString()} labeled rows</h3><p>${dataset.model_features} model features from ${dataset.predictor_columns} predictors · ${dataset.missing_values} missing values · ${dataset.duplicate_rows} duplicate rows</p></div><small>SHA-256 ${escapeHTML(dataset.sha256.slice(0,12))}…</small></div><div class="provenance-line"><div><strong>Cardiotocography</strong><span>${escapeHTML(dataset.collection_context)}</span></div><div><a href="${escapeHTML(dataset.source_urls.uci)}" target="_blank" rel="noopener">UCI source ↗</a><a href="${escapeHTML(dataset.source_urls.kaggle)}" target="_blank" rel="noopener">Kaggle mirror ↗</a></div></div><div class="balance-bar">${Object.entries(dataset.class_counts).map(([label,count]) => `<i class="${label.toLowerCase()}" style="width:${count/total*100}%" title="${label}: ${count}"></i>`).join('')}</div><div class="balance-legend">${Object.entries(dataset.class_counts).map(([label,count]) => `<span><i class="${label.toLowerCase()}"></i><strong>${label}</strong> ${count} · ${Math.round(count/total*100)}%</span>`).join('')}</div><p class="dataset-warning">Class imbalance is substantial. Overall accuracy alone can hide weaker minority-class performance.</p><div class="dataset-citation"><strong>${escapeHTML(dataset.license)}</strong><span>${escapeHTML(dataset.citation)}</span></div></section>`;
  const matrix = card.evaluation.confusion_matrix; const classNames = ['Normal','Suspect','Pathological']; const perClass = card.evaluation.per_class_metrics;
  const lineage = card.evaluation.evaluation_split;
  $('#diagnosticDashboard').innerHTML = `<section class="diagnostic-panel"><div class="diagnostic-head"><div><span class="eyebrow">Reconstructed held-out evaluation</span><h3>Confusion matrix & per-class measures</h3></div><span class="scope-badge verified">Verified match</span></div><p class="diagnostic-warning verified">${escapeHTML(card.evaluation.diagnostic_warning)}</p><div class="lineage-strip"><span><strong>${lineage.train_rows}</strong>Train rows</span><span><strong>${lineage.test_rows}</strong>Test rows</span><span><strong>80/20</strong>Stratified split</span><span><strong>${lineage.random_state}</strong>Random seed</span></div><div class="diagnostic-grid"><div class="matrix-wrap"><table class="confusion-matrix"><caption>Rows: actual · Columns: predicted</caption><thead><tr><th></th>${classNames.map(name => `<th>${name}</th>`).join('')}</tr></thead><tbody>${matrix.map((row,index) => `<tr><th>${classNames[index]}</th>${row.map((value,column) => `<td class="${index===column?'correct':'error'}"><strong>${value}</strong></td>`).join('')}</tr>`).join('')}</tbody></table></div><div class="per-class-list">${classNames.map(name => `<article><strong>${name}</strong><div><span>Precision <b>${percent(perClass[name].precision)}</b></span><span>Recall <b>${percent(perClass[name].recall)}</b></span><span>F1 <b>${percent(perClass[name].f1)}</b></span><span>Support <b>${perClass[name].support}</b></span></div></article>`).join('')}</div></div><div class="calibration-summary"><span><strong>${card.evaluation.calibration.multiclass_brier.toFixed(4)}</strong>Multiclass Brier</span><span><strong>${percent(card.evaluation.calibration.ece_10_bin)}</strong>10-bin ECE</span><p>Calibration diagnostics are calculated on the reconstructed 423-row held-out set.</p></div></section>`;
}

function bindEvents() {
  document.querySelectorAll('[data-view]').forEach(button => button.addEventListener('click', () => showView(button.dataset.view)));
  document.querySelectorAll('[data-view-link]').forEach(button => button.addEventListener('click', () => showView(button.dataset.viewLink)));
  $('#startAssessment').addEventListener('click', () => $('#assessmentWorkspace').scrollIntoView({ behavior: 'smooth' }));
  $('#predictionForm').addEventListener('submit', runPrediction);
  document.querySelectorAll('[data-preset]').forEach(button => button.addEventListener('click', () => loadPreset(button.dataset.preset)));
  $('#predictionForm').addEventListener('input', updateCompletion);
  $('#clearBtn').addEventListener('click', () => { $('#predictionForm').reset(); document.querySelectorAll('input.invalid').forEach(input => input.classList.remove('invalid')); $('#formAlert').classList.add('hidden'); updateCompletion(); });
  $('#themeToggle').addEventListener('click', () => {
    const nextTheme = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
    document.documentElement.dataset.theme = nextTheme;
    const label = `Switch to ${nextTheme === 'dark' ? 'light' : 'dark'} theme`;
    $('#themeToggle').setAttribute('aria-label', label); $('#themeToggle').title = label;
    document.querySelector('meta[name="theme-color"]').content = nextTheme === 'dark' ? '#0e1f1b' : '#123c36';
  });
  $('#resetAnalytics').addEventListener('click', () => { state.analytics = { assessments: 0, explanations: 0, confidenceTotal: 0, responseTotal: 0, classes: { Normal: 0, Suspect: 0, Pathological: 0 } }; updateAnalytics(); toast('Session analytics reset'); });
  document.querySelectorAll('.class-tab').forEach(button => button.addEventListener('click', () => showClassExplanation(button.dataset.class)));
  $('#featureSearch').addEventListener('input', event => renderFeatureReference(event.target.value));
  $('#csvInput').addEventListener('change', event => { importCSV(event.target.files[0]); event.target.value = ''; });
  $('#downloadTemplate').addEventListener('click', downloadCSVTemplate);
  $('#closeComparison').addEventListener('click', () => $('#comparisonDialog').close());
  $('#comparisonDialog').addEventListener('click', event => { if (event.target === $('#comparisonDialog')) $('#comparisonDialog').close(); });
  showClassExplanation('Normal');
}

async function init() {
  try { [state.schema, state.modelCard] = await Promise.all([request('/schema'), request('/model-card')]); renderSchema(); renderModelCard(); bindEvents(); updateAnalytics(); }
  catch (error) { $('#formFields').innerHTML = `<div class="form-alert">${escapeHTML(error.message)} Refresh the page after the local API starts.</div>`; }
}

document.addEventListener('DOMContentLoaded', init);
