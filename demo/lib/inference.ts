export type PortableModel = {
  features: string[];
  medians: number[];
  means: number[];
  scales: number[];
  coefficients: number[];
  intercept: number;
};
export const bounds: Record<string, [number, number]> = {
  Age: [60, 96],
  Sex: [0, 1],
  EDUC: [0, 30],
  SES: [1, 5],
  eTIV: [900, 2200],
  nWBV: [0.55, 0.9],
  MMSE: [0, 30],
};
export function infer(
  model: PortableModel,
  values: Record<string, number | null>,
) {
  if (Object.keys(values).some((k) => !(k in bounds)))
    throw new Error('Unexpected measurement');
  const contributions = model.features.map((f, i) => {
    const v = values[f] ?? model.medians[i];
    const [lo, hi] = bounds[f];
    if (
      typeof v !== 'number' ||
      !Number.isFinite(v) ||
      v < lo ||
      v > hi ||
      (['Sex', 'SES'].includes(f) && !Number.isInteger(v))
    )
      throw new Error(`Invalid ${f}`);
    return {
      feature: f,
      value: ((v - model.means[i]) / model.scales[i]) * model.coefficients[i],
    };
  });
  const z = contributions.reduce((s, c) => s + c.value, model.intercept);
  return {
    score: 1 / (1 + Math.exp(-Math.max(-700, Math.min(700, z)))),
    contributions,
  };
}
