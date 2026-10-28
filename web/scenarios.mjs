// Portable OASIS logistic inference and versioned, local-only scenario files.
export const measurementBounds = {
  Age: [60, 96], Sex: [0, 1], EDUC: [0, 30], SES: [1, 5],
  eTIV: [900, 2200], nWBV: [.55, .9], MMSE: [0, 30],
};
export const measurementNames = {
  Age: 'Age (years)', Sex: 'Recorded sex', EDUC: 'Education (years)',
  SES: 'Socioeconomic category', eTIV: 'Intracranial volume (cm³)',
  nWBV: 'Normalized whole-brain volume (fraction)', MMSE: 'MMSE score (0–30)',
};

export function validateMeasurement(feature, value) {
  const [lo, hi] = measurementBounds[feature];
  if (value !== null && (typeof value !== 'number' || !Number.isFinite(value)
      || value < lo || value > hi
      || (['Sex', 'SES'].includes(feature) && !Number.isInteger(value))))
    throw new Error(measurementNames[feature] + ' is outside the supported range.');
}

export function inferScenario(model, values) {
  if (!values || typeof values !== 'object' || Array.isArray(values))
    throw new Error('Measurements must be an object.');
  if (Object.keys(values).some(key => !Object.hasOwn(measurementBounds, key)))
    throw new Error('Unexpected measurement field.');
  const contributions = model.features.map((feature, i) => {
    const entered = values[feature] ?? null;
    validateMeasurement(feature, entered);
    const used = entered ?? model.medians[i];
    return {feature, entered, used, imputed: entered === null,
      contribution: (used - model.means[i]) / model.scales[i] * model.coefficients[i]};
  });
  const logOdds = contributions.reduce((sum, row) => sum + row.contribution, model.intercept);
  return {score: 1 / (1 + Math.exp(-Math.max(-700, Math.min(700, logOdds)))),
    logOdds, intercept: model.intercept, contributions};
}

function exactKeys(value, expected) {
  return value && typeof value === 'object' && !Array.isArray(value)
    && Object.keys(value).length === expected.length
    && expected.every(key => Object.hasOwn(value, key));
}

function contextFor(bundle, study, family) {
  if (typeof study !== 'string' || typeof family !== 'string'
      || !['current', 'future'].includes(study) || !Object.hasOwn(bundle.models[study], family))
    throw new Error('Unknown study or measurement set.');
  return bundle.models[study][family];
}

function cleanScenario(model, values) {
  inferScenario(model, values);
  return Object.fromEntries(model.features.map(feature => [feature, values[feature] ?? null]));
}

export function makeScenarioFile(bundle, study, family, values, reference = null) {
  const model = contextFor(bundle, study, family);
  return {
    format: 'neurovolume-scenario', schema_version: 1,
    study, family, model_sha256: bundle.model_sha256[study],
    purpose: 'Invented examples for research software exploration; not clinical use.',
    scenarios: {a: reference === null ? null : cleanScenario(model, reference),
      b: cleanScenario(model, values)},
  };
}

export function readScenarioFile(text, bundle) {
  if (typeof text !== 'string' || text.length > 65536)
    throw new Error('Choose a scenario JSON file smaller than 64 KB.');
  let data;
  try { data = JSON.parse(text); } catch { throw new Error('This file is not valid JSON.'); }
  if (!exactKeys(data, ['format', 'schema_version', 'study', 'family', 'model_sha256', 'purpose', 'scenarios'])
      || data.format !== 'neurovolume-scenario' || data.schema_version !== 1)
    throw new Error('Unsupported scenario file. Use a NeuroVolume scenario export.');
  const model = contextFor(bundle, data.study, data.family);
  if (data.model_sha256 !== bundle.model_sha256[data.study])
    throw new Error('This scenario uses a different model version. No measurements were changed.');
  if (data.purpose !== 'Invented examples for research software exploration; not clinical use.'
      || !exactKeys(data.scenarios, ['a', 'b'])
      || !exactKeys(data.scenarios.b, model.features)
      || (data.scenarios.a !== null && !exactKeys(data.scenarios.a, model.features)))
    throw new Error('Unexpected scenario fields. Participant records are not supported.');
  // Construct a fresh object after full validation. Never spread untrusted keys into app state.
  return makeScenarioFile(bundle, data.study, data.family, data.scenarios.b, data.scenarios.a);
}
