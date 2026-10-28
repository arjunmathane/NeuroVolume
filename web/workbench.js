// UI state is memory-only. Model inference and file validation live in scenarios.mjs.
const $ = id => document.getElementById(id);
const {report, decline, audit, survivalModels, survivalReport} = bundle;
const familyLabels = {demographics:'Demographics', mri:'Demographics + MRI',
  cognition:'Demographics + cognition', combined:'Demographics + MRI + cognition',
  age:'Age only', age_mri:'Age + normalized brain volume'};
const defaultValues = {Age:75, Sex:0, EDUC:16, SES:2, eTIV:1450, nWBV:.74, MMSE:28};
let values = {...defaultValues}, reference = null;
function activeModel() { return bundle.models[$('study').value][$('family').value]; }
function formatValue(feature, value) {
  if (feature === 'Sex') return value === 0 ? 'Female (0)' : value === 1 ? 'Male (1)' : String(value);
  return Number(value.toFixed(feature === 'nWBV' ? 4 : 3)).toString();
}
function usedValue(row) {
  const value = formatValue(row.feature, row.used);
  return row.imputed ? 'Missing → ' + value + ' (training median)' : value;
}
function signed(value) { return (value > 0 ? '+' : '') + value.toFixed(3); }
function tableRow(cells) {
  const tr = document.createElement('tr');
  cells.forEach((text, i) => {
    const cell = document.createElement(i === 0 ? 'th' : 'td');
    if (i === 0) cell.scope = 'row';
    cell.textContent = text;
    tr.append(cell);
  });
  return tr;
}
function appendOptions(select, pairs) {
  select.replaceChildren();
  pairs.forEach(([value, text]) => {
    const option = document.createElement('option'); option.value = value; option.textContent = text;
    select.append(option);
  });
}
function readValues() {
  const result = {...values};
  activeModel().features.forEach(feature => {
    const input = $('f_' + feature);
    // A partially typed numeric value must never silently become a median-imputed blank.
    result[feature] = input.validity?.badInput ? NaN : input.value === '' ? null : Number(input.value);
  });
  return result;
}
function renderInputs() {
  $('inputs').replaceChildren();
  const model = activeModel();
  model.features.forEach((feature, i) => {
    const field = document.createElement('div'); field.className = 'field';
    const label = document.createElement('label'); label.htmlFor = 'f_' + feature;
    label.textContent = measurementNames[feature];
    let input;
    if (feature === 'Sex' || feature === 'SES') {
      input = document.createElement('select');
      appendOptions(input, [['', 'Missing · use training median'], ...(feature === 'Sex'
        ? [['0','Female (0)'], ['1','Male (1)']]
        : [1,2,3,4,5].map(value => [String(value), String(value)]))]);
    } else {
      input = document.createElement('input'); input.type = 'number';
      input.min = measurementBounds[feature][0]; input.max = measurementBounds[feature][1];
      input.step = feature === 'nWBV' ? '.001' : 'any';
    }
    input.id = 'f_' + feature; input.value = values[feature] ?? '';
    input.setAttribute('aria-describedby', 'hint_' + feature);
    const hint = document.createElement('p'); hint.className = 'hint'; hint.id = 'hint_' + feature;
    hint.textContent = measurementBounds[feature].join('–') + ' · blank uses median ' + formatValue(feature, model.medians[i]);
    input.addEventListener('input', () => {values = readValues(); predict();});
    field.append(label, input, hint); $('inputs').append(field);
  });
  predict();
}
function predict() {
  const model = activeModel();
  let result;
  model.features.forEach(feature => $('f_' + feature).setAttribute('aria-invalid', 'false'));
  try { result = inferScenario(model, readValues()); }
  catch (error) {
    $('error').textContent = error.message;
    model.features.forEach(feature => {
      try {validateMeasurement(feature, readValues()[feature]);}
      catch { $('f_' + feature).setAttribute('aria-invalid', 'true'); }
    });
  }
  $('pinScenario').disabled = !result; $('downloadScenario').disabled = !result;
  $('comparisonResults').hidden = !result || !reference;
  $('clearReference').disabled = !reference;
  $('contributions').replaceChildren();
  const study = $('study').value;
  $('modelIdentity').textContent = (study === 'current' ? 'models/logistic.json' : 'models/decline-logistic.json')
    + ' · SHA-256: ' + bundle.model_sha256[study] + ' · Measurement set: ' + $('family').value + '.';
  if (!result) {
    $('score').textContent = '—'; $('classification').textContent = 'Correct the measurement to calculate a score.';
    $('imputationSummary').textContent = 'No prediction or export is available while a measurement is invalid.';
    $('comparisonStatus').textContent = reference ? 'Reference A is retained. Correct B to compare.' : 'Correct B before pinning a reference.';
    return;
  }
  $('error').textContent = '';
  $('score').textContent = result.score.toFixed(3);
  $('classification').textContent = study === 'future'
    ? 'Illustrative three-year recorded-impairment score. The explorer uses a final refit on all 43 pilot participants, not an independently tested prognostic model.'
    : 'At the fixed 0.5 threshold: ' + (result.score >= .5 ? 'CDR > 0' : 'CDR = 0') + '. This describes recorded current impairment, not future decline.';
  const missing = result.contributions.filter(row => row.imputed);
  $('imputationSummary').textContent = missing.length === model.features.length
    ? 'All measurements are missing. This is the training-median reference profile, not a measurement-informed assessment.'
    : missing.length ? missing.length + ' of ' + model.features.length + ' measurements imputed: '
      + missing.map(row => measurementNames[row.feature]).join(', ') + '. Substitutions are shown below.'
      : 'All ' + model.features.length + ' model measurements supplied. No median substitutions.';
  result.contributions.forEach(row => $('contributions').append(tableRow([
    measurementNames[row.feature], usedValue(row), signed(row.contribution)])));
  $('contributions').append(tableRow(['Intercept', '—', signed(result.intercept)]));
  $('comparisonStatus').textContent = reference ? 'A is pinned; B updates as you edit. Both use ' + familyLabels[$('family').value] + '.'
    : 'Pin the current example as reference A, then edit B. You can also save a single example without pinning.';
  if (reference) {
    const a = inferScenario(model, reference);
    $('referenceScore').textContent = a.score.toFixed(3); $('candidateScore').textContent = result.score.toFixed(3);
    $('scoreDifference').textContent = signed(result.score - a.score);
    $('comparisonRows').replaceChildren();
    result.contributions.forEach((row, i) => $('comparisonRows').append(tableRow([
      measurementNames[row.feature], usedValue(a.contributions[i]), usedValue(row),
      signed(row.contribution - a.contributions[i].contribution)])));
  }
}
function study(preserve = false) {
  const isFuture = $('study').value === 'future';
  appendOptions($('family'), Object.keys(bundle.models[$('study').value]).map(key => [key, familyLabels[key]]));
  $('family').value = isFuture ? 'age_mri' : 'mri';
  reference = null;
  if (!preserve) values = {...defaultValues};
  $('scenarioMessage').textContent = '';
  $('studyTag').textContent = isFuture ? 'OASIS · Exploratory pilot' : 'OASIS · Held-out study';
  $('studyDescription').textContent = isFuture
    ? 'Initially unimpaired participants; first recorded CDR > 0 within 1,095 days. Internal validation only.'
    : 'Recorded baseline CDR > 0 versus CDR = 0. Models fitted on 120 development participants; 30 held out.';
  $('resultTitle').textContent = isFuture ? 'Future recorded-impairment score · pilot' : 'Current recorded-impairment score';
  $('evidenceTitle').textContent = isFuture ? 'Future impairment: exploratory internal validation' : 'Current impairment: held-out participants';
  $('metricLabel').textContent = isFuture ? 'Mean OOF AUC' : 'Test ROC-AUC';
  $('evidence').replaceChildren();
  if (isFuture) {
    const c = decline.cohort;
    $('finding').textContent = c.included + ' participants: ' + c.events + ' recorded events and ' + c.non_events
      + ' observed non-events; ' + c.excluded_insufficient_followup + ' excluded for insufficient follow-up. Adding whole-brain volume did not improve the mean out-of-fold AUC.';
    Object.entries(decline.results).forEach(([key, result]) => {
      const repeats = result.per_repeat_metrics;
      const mean = field => repeats.reduce((sum, row) => sum + row[field], 0) / repeats.length;
      $('evidence').append(tableRow([familyLabels[key], result.mean_repeated_oof_auc.toFixed(3),
        (100 * mean('sensitivity')).toFixed(1) + '%', (100 * mean('specificity')).toFixed(1) + '%',
        '3 folds × 10 repeats; no independent test']));
    });
    $('evidenceCaption').textContent = 'Mean repeated out-of-fold metrics at the fixed 0.5 threshold. Both models had zero sensitivity: every participant was classified as a non-event. AUC alone does not describe a useful screening model.';
    $('limitations').textContent = decline.limitations.join(' ');
  } else {
    $('finding').textContent = 'Adding MRI changed the primary logistic test AUC from 0.683 to 0.688. The paired 95% bootstrap interval for the difference is −0.158 to +0.167; incremental MRI value was not established.';
    report.results.filter(row => row.algorithm === 'logistic').forEach(row => $('evidence').append(tableRow([
      row.label, row.test.auc.toFixed(3), (100 * row.test.sensitivity).toFixed(1) + '%',
      (100 * row.test.specificity).toFixed(1) + '%', '30 test participants; 120 development'])));
    $('evidenceCaption').textContent = 'Prespecified logistic models; sensitivity and specificity at threshold 0.5. These metrics describe the same held-out cohort. Other benchmark algorithms are documented in the repository.';
    $('limitations').textContent = 'Current recorded impairment is not future decline or confirmed Alzheimer disease. Cognitive scores measure a related clinical construct. A single small cohort limits generalization. Model scores are not clinically calibrated.';
  }
  renderInputs();
}
function downloadJSON(data, filename) {
  const link = document.createElement('a'); const url = URL.createObjectURL(new Blob([JSON.stringify(data, null, 2)], {type:'application/json'}));
  link.href = url; link.download = filename; link.click(); setTimeout(() => URL.revokeObjectURL(url), 1000);
}
$('study').addEventListener('change', () => study());
$('family').addEventListener('change', () => {reference = null; $('scenarioMessage').textContent = ''; renderInputs();});
$('reset').addEventListener('click', () => {values = {...defaultValues}; $('scenarioMessage').textContent = ''; renderInputs();});
$('pinScenario').addEventListener('click', () => {
  try {
    const data = makeScenarioFile(bundle, $('study').value, $('family').value, readValues());
    reference = {...data.scenarios.b}; $('scenarioMessage').textContent = ''; predict();
  } catch (error) {$('scenarioMessage').textContent = error.message;}
});
$('clearReference').addEventListener('click', () => {reference = null; predict();});
$('downloadScenario').addEventListener('click', () => {
  try { downloadJSON(makeScenarioFile(bundle, $('study').value, $('family').value, readValues(), reference),
    'neurovolume-' + $('study').value + '-' + $('family').value + '-scenario.json'); }
  catch (error) { $('scenarioMessage').textContent = error.message; }
});
$('restoreScenario').addEventListener('change', async event => {
  const file = event.target.files?.[0]; if (!file) return;
  try {
    if (file.size > 65536) throw new Error('Choose a scenario JSON file smaller than 64 KB.');
    const data = readScenarioFile(await file.text(), bundle);
    $('study').value = data.study; study(true); $('family').value = data.family;
    values = {...defaultValues, ...data.scenarios.b}; reference = data.scenarios.a;
    renderInputs(); $('scenarioMessage').textContent = '';
    $('comparisonStatus').textContent = 'Scenario restored. ' + $('comparisonStatus').textContent;
  } catch (error) { $('scenarioMessage').textContent = error.message; }
  finally { event.target.value = ''; }
});

function drawSurvival() {
  const fields = ['sAge','sMmse','sRatio'];
  const entries = fields.map(id => $(id).validity?.badInput ? NaN : $(id).value === '' ? null : Number($(id).value));
  const limits = [[55,95],[23,30],[.002,.007]]; let error = '';
  entries.forEach((value, i) => {
    const invalid = (value === null && i !== 1) || (value !== null && (!Number.isFinite(value) || value < limits[i][0] || value > limits[i][1]));
    $(fields[i]).setAttribute('aria-invalid', String(invalid));
    if (invalid) error = 'Use measurements within the displayed synthetic example ranges. Age and volume ratio are required.';
  });
  $('survivalError').textContent = error;
  $('survivalTable').replaceChildren();
  if (error) {
    $('survivalChart').innerHTML = '<title id="curveTitle">Invalid scenario</title><desc id="curveDesc">Correct the measurements. No curves are shown.</desc>';
    $('survivalValues').textContent = 'Correct the measurements to view the curves.'; return;
  }
  const profile = {age:entries[0], mmse:entries[1], hippocampus_icv_ratio:entries[2]};
  const days = Array.from({length:61}, (_,i) => i * 1825 / 60);
  const clinical = survivalCurve(survivalModels.clinical, profile, days);
  const mri = survivalCurve(survivalModels.clinical_mri, profile, days);
  const path = curve => curve.map((value, i) => (i === 0 ? 'M' : 'L') + (55 + 420 * i/60).toFixed(2) + ',' + (240 - 210 * value).toFixed(2)).join(' ');
  const grid = [0,.25,.5,.75,1].map(value => `<line x1="55" x2="475" y1="${240-210*value}" y2="${240-210*value}" stroke="#dce3ec"/><text x="45" y="${245-210*value}" text-anchor="end" font-size="12">${value.toFixed(2)}</text>`).join('');
  const ticks = [0,1,2,3,4,5].map(value => `<text x="${55+84*value}" y="260" text-anchor="middle" font-size="12">${value}</text>`).join('');
  $('survivalChart').innerHTML = '<title id="curveTitle">Synthetic survival curves</title><desc id="curveDesc">Invented scenario, not a clinical prognosis. Solid blue is age and cognition; dashed brown adds MRI. Numeric values are in the following table.</desc>' + grid + ticks
    + '<text x="265" y="285" text-anchor="middle" font-size="12">Years since invented baseline</text><path d="' + path(clinical) + '" fill="none" stroke="#164b87" stroke-width="3"/><path d="' + path(mri) + '" fill="none" stroke="#a34e0a" stroke-width="3" stroke-dasharray="7 4"/>';
  const years = [1,3,5];
  const a = survivalCurve(survivalModels.clinical, profile, years.map(year => year*365));
  const b = survivalCurve(survivalModels.clinical_mri, profile, years.map(year => year*365));
  years.forEach((year, i) => $('survivalTable').append(tableRow([year + (year === 1 ? ' year' : ' years'), a[i].toFixed(3), b[i].toFixed(3)])));
  $('survivalValues').textContent = 'At three years, synthetic event-free fraction: age + cognition ' + a[1].toFixed(3) + '; with MRI ' + b[1].toFixed(3)
    + '. These are predictions from invented data, not medical risks.' + (entries[1] === null ? ' Missing MMSE uses training medians.' : '');
}
const gain = survivalReport.paired_mri_gain;
$('survivalEvidence').textContent = survivalReport.training_participants + ' training participants; ' + survivalReport.test_participants
  + ' held-out participants (' + survivalReport.test_events + ' observed events, ' + survivalReport.test_right_censored
  + ' right-censored). Mean test log likelihood: age + cognition ' + survivalReport.results.clinical.mean_test_log_likelihood.toFixed(3)
  + '; with MRI ' + survivalReport.results.clinical_mri.mean_test_log_likelihood.toFixed(3) + '. MRI difference ' + gain.mean.toFixed(3)
  + '; paired 95% bootstrap interval [' + gain.bootstrap_95_interval.map(value => value.toFixed(3)).join(', ') + ']. The interval includes zero.';
['sAge','sMmse','sRatio'].forEach(id => $(id).addEventListener('input', drawSurvival));
$('resetSurvival').addEventListener('click', () => {['sAge','sMmse','sRatio'].forEach((id,i) => $(id).value = [74,28,.0048][i]); drawSurvival();});
$('downloadSurvival').addEventListener('click', () => downloadJSON(survivalReport, 'neurovolume-synthetic-survival-report.json'));
$('auditSummary').textContent = `${audit.input_participants} input participants → ${audit.included} included; ${audit.events} events and ${audit.right_censored} right-censored. Exclusions: ${Object.entries(audit.excluded).filter(([,n]) => n).map(([key,n]) => key.replaceAll('_',' ') + ': ' + n).join('; ')}. Median event-observation interval: ${audit.median_event_interval_days} days.`;
audit.followup_bins_days.forEach((label,i) => {
  const row = tableRow([label, String(audit.followup_counts[i]), '']);
  const bar = document.createElement('span'); bar.style.cssText = 'display:block;background:#15635d;height:10px;width:' + 100*audit.followup_counts[i]/Math.max(1,...audit.followup_counts) + '%';
  bar.setAttribute('aria-hidden', 'true'); row.children[2].append(bar); $('auditBars').append(row);
});
$('downloadAudit').addEventListener('click', () => downloadJSON(audit, 'neurovolume-synthetic-audit.json'));
study(); drawSurvival();
