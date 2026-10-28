# NeuroVolume status

October 28, 2026 product update: the offline workbench supports same-model paired scenario comparison, explicit imputation details, version-checked local JSON save/restore, expanded evidence tables and numeric survival predictions. This is a software/interface update; no models were retrained and no clinical evidence was added. See the [workbench guide](WORKBENCH.md).

Completed: original OASIS classification study; exploratory three-year OASIS pilot; offline workbench; trained portable models; canonical longitudinal input validator; synthetic event-interval/cohort audit; draft next-study protocol; interval-censored Weibull survival implementation; held-out synthetic software experiment and interactive survival curves.

ADNI application approval was verified in the owner's September 9 approval email on October 9, 2026. Authenticated access and local acquisition of clinical tables, a dictionary, cross-sectional FreeSurfer 7.x measurements and a historical QC guide are complete. The source-specific importer and feasibility audit are implemented. Controlled records and derived participant outputs remain inside ignored `private/`; none is included in the source release.

The reviewed 7.4.1 subset does not support the planned decline fit under the declared timing and quality rules. An older cross-sectional release is needed. The signed-in archive lists that release, but its selected-file download did not produce a confirmed local file in this session. Do not relax QC or mix processing versions to manufacture a result.

Pending: older-release acquisition and source review; final real-cohort sample-size/model/metric specification; larger-cohort training; independent and external validation; public application hosting. No repeat sign-in is requested. Approval and acquisition alone are not predictive validation.

The standalone workbench was served locally and visually checked in Chrome. Study switching, interactive survival curves, invalid-input handling, reset and a saved synthetic report download were verified. No exhaustive cross-browser/accessibility testing is claimed.

Project direction: Arjun Mathane selected the research question and directed development.
