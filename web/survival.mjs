// Portable inference for SYNTHETIC software demonstrations only.
export function survivalCurve(model, values, days) {
  const bounds = {age: [18, 120], mmse: [0, 30], hippocampus_icv_ratio: [0, .1]};
  let logScale = model.intercept;
  model.features.forEach((feature, i) => {
    const value = values[feature];
    if (value !== null && (typeof value !== 'number' || !Number.isFinite(value) || value < bounds[feature][0] || value > bounds[feature][1])) {
      throw new Error('Invalid measurement: ' + feature);
    }
    logScale += ((value ?? model.medians[i]) - model.means[i]) / model.scales[i] * model.coefficients[i];
  });
  return days.map(day => {
    if (!Number.isFinite(day) || day < 0) throw new Error('Invalid time.');
    return day === 0 ? 1 : Math.exp(-Math.exp(model.shape * (Math.log(day) - logScale)));
  });
}
