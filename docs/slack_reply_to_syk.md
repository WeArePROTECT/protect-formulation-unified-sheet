# Draft Slack reply → Sun-Young (acknowledging the 20260714 upload)

*Short, warm, and it reinforces the behavior we want from everyone: data on the server + a notes doc describing conditions. Edit to taste.*

---

Thanks @Sun-Young Kim — grabbed both `ASMA_phenotype_20260714.xlsx` and the notes doc. This is exactly what
Alex and I need, and honestly the **notes doc is the model** for what we're going to ask everyone for: it
already documents the per-assay conditions (plate format, reader, cycle interval, media, normalization) that
let us join datasets without accidentally comparing apples to oranges — which is precisely the concern you
raised about assays run under different conditions.

A couple of things so you know we read it carefully:
- We'll build off the **current** sheets — `Competition` (Standard conditions only, dropping `Non_standard_A`),
  `Antibiotic_resistance_v2`, `Growth_endpoint`, and `Growth_Curve_single_96` — and leave the deprecated
  `v1` / 384-well sheets out. The v1→v2 / 384→96 versioning in your notes made that unambiguous, thank you.
- Totally understood it's **raw/pre-QC**. We'll treat it as preliminary and won't hard-code anything that
  breaks when you finalize outlier handling. If it's useful, as we process I can flag high-variability
  wells we notice (e.g. replicate spread, or abx rows failing the ΔOD600 < 0.1 growth check) and send you a
  list — no pressure, just to save you a pass. Whatever QC timeline works for you is fine.

One tiny ask that makes all of this durable: if you can keep the **sheet + column names stable** as new data
lands (and keep dropping a notes doc like this one), our pipeline just keeps working. No rush on syncing
formats with Gwyn — Alex and I can handle the reconciliation on our end.

Really appreciate it 🙏
