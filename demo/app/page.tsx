'use client';
import { useState } from 'react';
import Link from 'next/link';
/* oxlint-disable jsx-a11y/prefer-tag-over-role -- Inline SVG charts require an image role and accessible title. */
import { ArrowUpRight, FlaskConical, RotateCcw, Download } from 'lucide-react';
import { Tabs, TabsList, TabsTrigger, TabsContent } from '@/components/ui/tabs';
import {
  Select,
  SelectTrigger,
  SelectValue,
  SelectContent,
  SelectItem,
} from '@/components/ui/select';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import {
  Table,
  TableHeader,
  TableBody,
  TableHead,
  TableRow,
  TableCell,
} from '@/components/ui/table';
import report from '@/lib/generated/results.json';
import models from '@/lib/generated/models.json';
import { infer, bounds } from '@/lib/inference';
type Family = keyof typeof models;
const families: Family[] = ['demographics', 'mri', 'cognition', 'combined'];
const names = {
  demographics: 'Demographics',
  mri: 'Demographics + MRI',
  cognition: 'Demographics + cognition',
  combined: 'Demographics + MRI + cognition',
};
const colors = {
  demographics: '#8293ab',
  mri: '#225de5',
  cognition: '#149083',
  combined: '#293b58',
};
const labels: Record<string, string> = {
  Age: 'Age (years)',
  Sex: 'Recorded sex',
  EDUC: 'Education (years)',
  SES: 'Socioeconomic class (1–5)',
  eTIV: 'Intracranial volume (cm³)',
  nWBV: 'Normalized brain volume (fraction)',
  MMSE: 'MMSE score (0–30)',
};
const initial: Record<string, number | null> = {
  Age: 75,
  Sex: 0,
  EDUC: 16,
  SES: 2,
  eTIV: 1450,
  nWBV: 0.73,
  MMSE: 27,
};
const pct = (n: number) => `${(n * 100).toFixed(1)}%`,
  fixed = (n: number) => n.toFixed(3);
const logistic = report.results.filter((r) => r.algorithm === 'logistic');
function AucPlot() {
  const x = (n: number) => 205 + n * 400;
  return (
    <figure>
      <svg
        viewBox="0 0 640 238"
        role="img"
        aria-label="Test ROC-AUC with 95 percent bootstrap intervals"
      >
        <title>Test ROC-AUC by logistic regression feature set</title>
        {[0, 0.25, 0.5, 0.75, 1].map((n) => (
          <g key={n}>
            <line
              x1={x(n)}
              x2={x(n)}
              y1="20"
              y2="185"
              stroke="#e1e7f0"
              strokeDasharray={n === 0.5 ? '4 4' : undefined}
            />
            <text x={x(n)} y="208" textAnchor="middle">
              {n.toFixed(2)}
            </text>
          </g>
        ))}
        {logistic.map((r, i) => (
          <g key={r.key}>
            <text x="0" y={40 + i * 44} className="plot-label">
              {['Demographics', '+ MRI', '+ Cognition', '+ MRI + cognition'][i]}
            </text>
            <line
              x1={x(r.auc_ci[0])}
              x2={x(r.auc_ci[1])}
              y1={35 + i * 44}
              y2={35 + i * 44}
              stroke={colors[r.family as Family]}
              strokeWidth="3"
            />
            <circle
              cx={x(r.test.auc)}
              cy={35 + i * 44}
              r="6"
              fill={colors[r.family as Family]}
            />
            <title>
              {`${r.label}: ${fixed(r.test.auc)} (${r.auc_ci.map(fixed).join('–')})`}
            </title>
          </g>
        ))}
        <text x="405" y="234" textAnchor="middle">
          ROC-AUC (0–1; 0.5 = chance ranking)
        </text>
      </svg>
      <figcaption>
        OASIS-2 · 30 held-out baseline participants · points: ROC-AUC; lines:
        95% stratified bootstrap intervals.
      </figcaption>
    </figure>
  );
}
function RocPlot() {
  return (
    <figure>
      <svg
        viewBox="0 0 380 295"
        role="img"
        aria-label="ROC curves on 30 test participants"
      >
        <title>Test receiver operating characteristic curves</title>
        {[0, 0.5, 1].map((n) => (
          <g key={n}>
            <line
              x1="55"
              x2="350"
              y1={245 - n * 210}
              y2={245 - n * 210}
              stroke="#e1e7f0"
            />
            <text x="43" y={249 - n * 210} textAnchor="end">
              {n.toFixed(1)}
            </text>
            <text x={55 + n * 295} y="265" textAnchor="middle">
              {n.toFixed(1)}
            </text>
          </g>
        ))}
        <line
          x1="55"
          y1="245"
          x2="350"
          y2="35"
          stroke="#c0cad8"
          strokeDasharray="5 5"
        />
        {logistic.map((r) => (
          <polyline
            key={r.key}
            fill="none"
            stroke={colors[r.family as Family]}
            strokeWidth="2.5"
            points={r.roc.fpr
              .map((f, i) => `${55 + f * 295},${245 - r.roc.tpr[i] * 210}`)
              .join(' ')}
          />
        ))}
        <text x="205" y="290" textAnchor="middle">
          False-positive rate (0–1)
        </text>
        <text transform="translate(16,140) rotate(-90)" textAnchor="middle">
          True-positive rate (0–1)
        </text>
      </svg>
      <div className="legend">
        {families.map((f) => (
          <span key={f}>
            <i style={{ background: colors[f] }} />
            {names[f]}
          </span>
        ))}
      </div>
      <figcaption>
        OASIS-2 test cohort · fixed logistic models. Curves show discrimination
        across thresholds.
      </figcaption>
    </figure>
  );
}
export default function Home() {
  const [family, setFamily] = useState<Family>('mri'),
    [values, setValues] = useState(initial),
    [algorithm, setAlgorithm] = useState('logistic');
  const active = models[family];
  const invalid = active.features.some((f) => {
    const v = values[f];
    return (
      v !== null &&
      (!Number.isFinite(v) || v < bounds[f][0] || v > bounds[f][1])
    );
  });
  const prediction = invalid ? null : infer(active, values),
    missing = active.features.filter((f) => values[f] === null);
  const result = logistic.find((r) => r.family === family)!;
  function download() {
    if (!prediction) return;
    const blob = new Blob(
      [
        JSON.stringify(
          {
            feature_set: family,
            inputs: values,
            score: prediction.score,
            threshold: 0.5,
            note: 'Synthetic scenario; research only, not a diagnosis or future risk.',
          },
          null,
          2,
        ),
      ],
      { type: 'application/json' },
    );
    const url = URL.createObjectURL(blob),
      a = document.createElement('a');
    a.href = url;
    a.download = 'neurovolume-scenario.json';
    a.click();
    URL.revokeObjectURL(url);
  }
  return (
    <div className="app-shell">
      <header className="masthead">
        <Link className="brand" href="/" aria-label="NeuroVolume home">
          <span className="brand-mark">
            <FlaskConical size={21} />
          </span>
          NeuroVolume
          <span className="brand-divider" />
          <span className="brand-sub">Research workspace</span>
        </Link>
        <span className="status">
          <span />
          OASIS-2 · Study 01
        </span>
      </header>
      <main>
        <div className="intro">
          <div>
            <p className="eyebrow">MRI MEASUREMENTS / COGNITIVE IMPAIRMENT</p>
            <h1>What does brain volume add?</h1>
            <p className="lede">
              Compare classification models, inspect the evidence, and explore
              synthetic measurements.
            </p>
          </div>
          <a
            className="source-link"
            href="https://sites.wustl.edu/oasisbrains/home/oasis-2/"
            target="_blank"
            rel="noreferrer"
          >
            Original dataset <ArrowUpRight size={16} />
          </a>
        </div>
        <Tabs defaultValue="evidence">
          <TabsList variant="line" className="tabbar">
            <TabsTrigger value="evidence">01 &nbsp; Evidence</TabsTrigger>
            <TabsTrigger value="explorer">02 &nbsp; Model explorer</TabsTrigger>
            <TabsTrigger value="methods">03 &nbsp; Study design</TabsTrigger>
          </TabsList>
          <TabsContent value="evidence">
            <div className="stat-strip">
              <div>
                <span>Independent participants</span>
                <strong>150</strong>
                <small>First visit only; 373 source sessions</small>
              </div>
              <div>
                <span>Development / test</span>
                <strong>
                  120 <em>/</em> 30
                </strong>
                <small>Participant separation; fixed seed</small>
              </div>
              <div>
                <span>MRI model · test ROC-AUC</span>
                <strong>{fixed(logistic[1].test.auc)}</strong>
                <small>Demographics + MRI · logistic regression</small>
              </div>
              <div>
                <span>Added MRI · Δ ROC-AUC</span>
                <strong className="blue">
                  +{fixed(report.differences[0].auc_delta)}
                </strong>
                <small>
                  95% interval{' '}
                  {report.differences[0].ci.map(fixed).join(' to ')}
                </small>
              </div>
            </div>
            <section className="finding">
              <span className="eyebrow">PRIMARY FINDING</span>
              <h2>No clear held-out improvement from MRI.</h2>
              <p>
                Adding brain-volume measurements raised test ROC-AUC from{' '}
                {fixed(logistic[0].test.auc)} to {fixed(logistic[1].test.auc)}.
                The paired uncertainty interval includes both benefit and harm.
                This small study does not establish an incremental MRI benefit.
              </p>
            </section>
            <div className="plot-grid">
              <section className="panel">
                <div className="section-top">
                  <div>
                    <p className="eyebrow">PRESPECIFIED LOGISTIC COMPARISON</p>
                    <h2>Performance, with uncertainty</h2>
                  </div>
                  <span className="chip">Held-out test set</span>
                </div>
                <AucPlot />
                <p className="subtle">
                  Cognition = MMSE. It measures a related clinical construct, so
                  stronger classification is not evidence of detection before
                  symptoms.
                </p>
              </section>
              <section className="panel">
                <p className="eyebrow">DISCRIMINATION</p>
                <h2>How the models separate classes</h2>
                <RocPlot />
              </section>
            </div>
            <section className="panel benchmark">
              <div className="section-top">
                <div>
                  <p className="eyebrow">ALL PREDEFINED BENCHMARKS</p>
                  <h2>Compare the complete results</h2>
                </div>
                <Select
                  value={algorithm}
                  onValueChange={(v) => v && setAlgorithm(v)}
                >
                  <SelectTrigger aria-label="Benchmark algorithm">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="logistic">
                      Logistic regression
                    </SelectItem>
                    <SelectItem value="forest">Random forest</SelectItem>
                    <SelectItem value="boosting">Gradient boosting</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead>Measurements</TableHead>
                    <TableHead>Dev. CV AUC</TableHead>
                    <TableHead>Test AUC</TableHead>
                    <TableHead>Accuracy</TableHead>
                    <TableHead>Sensitivity</TableHead>
                    <TableHead>Specificity</TableHead>
                    <TableHead>Brier score ↓</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {report.results
                    .filter((r) => r.algorithm === algorithm)
                    .map((r) => (
                      <TableRow key={r.key}>
                        <TableCell>{r.label}</TableCell>
                        <TableCell>
                          {fixed(r.cv_auc_mean)} ± {fixed(r.cv_auc_sd)}
                        </TableCell>
                        <TableCell>{fixed(r.test.auc)}</TableCell>
                        <TableCell>{pct(r.test.accuracy)}</TableCell>
                        <TableCell>{pct(r.test.sensitivity)}</TableCell>
                        <TableCell>{pct(r.test.specificity)}</TableCell>
                        <TableCell>{fixed(r.test.brier)}</TableCell>
                      </TableRow>
                    ))}
                </TableBody>
              </Table>
              <p className="subtle">
                Development: 5 folds × 3 repeats; mean ± fold standard deviation
                (not a confidence interval). Test: 30 participants; 13 CDR &gt;
                0 and 17 CDR = 0. Threshold = 0.5. Majority baseline:{' '}
                {pct(report.dummy.accuracy)} accuracy, AUC 0.500. No model was
                selected using test performance.
              </p>
            </section>
          </TabsContent>
          <TabsContent value="explorer">
            <div className="explorer-grid">
              <section className="panel controls">
                <p className="eyebrow">SYNTHETIC SCENARIO</p>
                <h2>Explore the trained model</h2>
                <p>
                  Change the measurements to see the model respond. These
                  starting values are invented, not a participant record.
                </p>
                <label
                  className="field-label"
                  id="feature-set-label"
                  htmlFor="feature-set"
                >
                  Measurements included
                </label>
                <Select
                  value={family}
                  onValueChange={(v) => v && setFamily(v as Family)}
                >
                  <SelectTrigger
                    id="feature-set"
                    aria-labelledby="feature-set-label"
                    className="wide"
                  >
                    <SelectValue>{names[family]}</SelectValue>
                  </SelectTrigger>
                  <SelectContent>
                    {families.map((f) => (
                      <SelectItem key={f} value={f}>
                        {names[f]}
                      </SelectItem>
                    ))}
                  </SelectContent>
                </Select>
                <div className="input-grid">
                  {active.features.map((f) => (
                    <div className="field" key={f}>
                      <label htmlFor={`field-${f}`}>{labels[f]}</label>
                      {f === 'Sex' || f === 'SES' ? (
                        <Select
                          value={
                            values[f] === null ? 'missing' : String(values[f])
                          }
                          onValueChange={(v) =>
                            v &&
                            setValues({
                              ...values,
                              [f]: v === 'missing' ? null : Number(v),
                            })
                          }
                        >
                          <SelectTrigger id={`field-${f}`} className="wide">
                            <SelectValue>
                              {values[f] === null
                                ? 'Missing'
                                : f === 'Sex'
                                  ? values[f] === 0
                                    ? 'Female (F)'
                                    : 'Male (M)'
                                  : String(values[f])}
                            </SelectValue>
                          </SelectTrigger>
                          <SelectContent>
                            {(f === 'Sex' ? [0, 1] : [1, 2, 3, 4, 5]).map(
                              (n) => (
                                <SelectItem key={n} value={String(n)}>
                                  {f === 'Sex'
                                    ? n === 0
                                      ? 'Female (F)'
                                      : 'Male (M)'
                                    : String(n)}
                                </SelectItem>
                              ),
                            )}
                            <SelectItem value="missing">Missing</SelectItem>
                          </SelectContent>
                        </Select>
                      ) : (
                        <Input
                          id={`field-${f}`}
                          type="number"
                          min={bounds[f][0]}
                          max={bounds[f][1]}
                          step={f === 'nWBV' ? 0.001 : 1}
                          value={values[f] ?? ''}
                          placeholder="Missing"
                          onChange={(e) =>
                            setValues({
                              ...values,
                              [f]:
                                e.target.value === ''
                                  ? null
                                  : Number(e.target.value),
                            })
                          }
                        />
                      )}
                    </div>
                  ))}
                </div>
                <p className="subtle">
                  Blank fields use development-set medians. Age is limited to
                  the source cohort (60–96). In-range measurements can still
                  form an unrepresentative combination.
                </p>
                <Button
                  variant="outline"
                  onClick={() => setValues({ ...initial })}
                >
                  <RotateCcw size={15} />
                  Reset example
                </Button>
              </section>
              <div>
                <section className="score-panel" aria-live="polite">
                  <p className="eyebrow">
                    LOGISTIC REGRESSION · {names[family]}
                  </p>
                  {prediction ? (
                    <>
                      <div className="score-number">
                        {prediction.score.toFixed(3)}
                        <span> / 1.000</span>
                      </div>
                      <p className="score-description">
                        Model score for recorded CDR &gt; 0
                      </p>
                      <div className="score-track">
                        <div style={{ width: `${prediction.score * 100}%` }} />
                        <i />
                      </div>
                      <div className="score-scale">
                        <span>0 · CDR = 0</span>
                        <span>0.5 threshold</span>
                        <span>1 · CDR &gt; 0</span>
                      </div>
                      <h2>
                        {prediction.score >= 0.5
                          ? 'Classified as CDR > 0'
                          : 'Classified as CDR = 0'}
                      </h2>
                      <p>
                        This score is not a calibrated clinical probability or a
                        forecast of future decline. No personal health decision
                        should be based on this demo.
                      </p>
                      {missing.length > 0 && (
                        <p className="imputed">
                          Median-imputed:{' '}
                          {missing.map((f) => labels[f]).join(', ')}.
                        </p>
                      )}
                      <Button variant="secondary" onClick={download}>
                        <Download size={16} />
                        Export scenario
                      </Button>
                    </>
                  ) : (
                    <p role="alert">
                      A measurement is outside its allowed range. Correct it to
                      calculate a score.
                    </p>
                  )}
                </section>
                {prediction && (
                  <section className="panel contributions">
                    <p className="eyebrow">WHY THIS SCORE?</p>
                    <h2>Contributions relative to the training mean</h2>
                    {[...prediction.contributions]
                      .sort((a, b) => Math.abs(b.value) - Math.abs(a.value))
                      .map((c) => (
                        <div className="contribution" key={c.feature}>
                          <span>{labels[c.feature]}</span>
                          <div>
                            <i
                              style={{
                                width: `${Math.min((Math.abs(c.value) / Math.max(...prediction.contributions.map((t) => Math.abs(t.value)), 0.01)) * 100, 100)}%`,
                                background:
                                  c.value >= 0 ? '#225de5' : '#8293ab',
                              }}
                            />
                          </div>
                          <b>
                            {c.value >= 0 ? '+' : ''}
                            {c.value.toFixed(2)}
                          </b>
                        </div>
                      ))}
                    <p className="subtle">
                      Values are additive log-odds contributions, not causal
                      effects. Positive values push toward CDR &gt; 0.
                      Intercept: {active.intercept.toFixed(2)}. This model’s
                      test accuracy: {pct(result.test.accuracy)} on 30
                      participants.
                    </p>
                  </section>
                )}
              </div>
            </div>
          </TabsContent>
          <TabsContent value="methods">
            <div className="methods-grid">
              <section className="panel">
                <p className="eyebrow">REPRODUCIBLE BY DESIGN</p>
                <h2>One participant, one baseline</h2>
                <div className="flow">
                  373 sessions → 150 first visits → 120 development / 30 test
                </div>
                <ol className="method-list">
                  <li>
                    <strong>Define the outcome.</strong> CDR &gt; 0 versus CDR =
                    0 at the first visit. This includes very mild/questionable
                    impairment; it is not a biomarker-confirmed Alzheimer
                    diagnosis.
                  </li>
                  <li>
                    <strong>Prevent future information from entering.</strong>{' '}
                    Keep the actual first row, including missing values. Exclude
                    Group (which can encode later conversion), CDR, identifiers
                    and later visits from inputs.
                  </li>
                  <li>
                    <strong>Compare fixed feature sets.</strong> Demographics;
                    demographics + MRI; demographics + MMSE; all three. eTIV and
                    nWBV are precomputed MRI measurements; the model does not
                    read MRI images.
                  </li>
                  <li>
                    <strong>Fit preprocessing within folds.</strong> Median
                    imputation, scaling and models are trained using development
                    data only. Five-fold cross-validation is repeated three
                    times.
                  </li>
                  <li>
                    <strong>Evaluate once on held-out participants.</strong>{' '}
                    Same test set for all 12 predefined models. Logistic
                    regression is the primary comparison. No tuning or feature
                    selection on the test set.
                  </li>
                </ol>
              </section>
              <section className="panel">
                <p className="eyebrow">INTERPRETATION</p>
                <h2>What this study can support</h2>
                <p>
                  The MRI comparison shows a development CV improvement that did
                  not clearly carry over to the held-out set. It does not show
                  that brain imaging is generally unhelpful.
                </p>
                <p>
                  Only 30 test participants, one source cohort, and coarse
                  whole-brain measurements limit generalization. Confidence
                  intervals condition on fitted models and sampled class
                  balance; they omit training and site uncertainty.
                </p>
                <h3>Next: future decline</h3>
                <p>
                  The workbook has{' '}
                  {report.future_feasibility.later_cdr_positive} participants
                  with baseline CDR = 0 and a later CDR &gt; 0. This is a
                  feasibility count, not a prognostic result. A follow-up study
                  needs a time horizon, censoring rules and preferably more
                  progression events.
                </p>
                <h3>Data & attribution</h3>
                <p>
                  Data were provided by OASIS. OASIS-2: Longitudinal; principal
                  investigators D. Marcus, R. Buckner, J. Csernansky, J. Morris.
                  P50 AG05681, P01 AG03991, P01 AG026276, R01 AG021910, P20
                  MH071616, U24 RR021382.
                </p>
                <a
                  className="text-link"
                  href="https://doi.org/10.1162/jocn.2009.21407"
                  target="_blank"
                  rel="noreferrer"
                >
                  Source publication <ArrowUpRight size={15} />
                </a>
                <p className="subtle">
                  Raw participant records are not included in this demo.
                </p>
              </section>
            </div>
          </TabsContent>
        </Tabs>
        <footer>
          <span>
            NEUROVOLUME / Independent computational neuroscience project
          </span>
          <span>Research demonstration · No diagnostic use</span>
        </footer>
      </main>
    </div>
  );
}
