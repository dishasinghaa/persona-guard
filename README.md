# Persona-Guard — synthetic prototype

A local-first prototype for exploring activation-based early warning and uncertainty-aware intervention.

## IMPORTANT: sample data only
`data/sessions.json` contains invented synthetic traces and fictional secrets. It is not a real Qwen run and must not be presented as experimental evidence. The interface labels the data as sample data.

## Run locally
From the project root:

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/app/`.

The app fetches `../data/sessions.json`, so use a local server rather than opening `index.html` directly if you want automatic data loading. If port 8000 is busy, use 8001.

## New: Mathematics and cloud model lab
- Mathematics tab documents the proposed risk normalization, ensemble disagreement, uncertainty weighting, activation-steering abstraction, evaluation metrics, and Pareto dominance, with caveats.
- Cloud Model Lab tab is a UI scaffold for endpoint configuration and a health check. It does not itself host or run models.
- `cloud_runner/` contains an undeployed FastAPI starter for authenticated cloud text generation, with a model allowlist and sequential model loading. See `cloud_runner/README.md`.
- The cloud scaffold does not yet extract activations, apply steering, or calculate valid leakage metrics. Those must be implemented and validated before claiming research results.

## What is implemented
- Overview and research framing
- Synthetic token-level replay with risk/trust display
- Method summaries for no guard, constant steering and UARD-gated steering
- Attack-scenario summary
- Safety–utility explorer with Pareto non-dominance calculation
- JSON upload to swap datasets if they follow the expected schema
- Explicit sample-data provenance warning

## What is NOT implemented
- Real model inference or activation hooks
- The Colab recorder
- Empirical results, validated uncertainty intervals, or claims of safety improvement
- A live cloud deployment or authenticated browser-to-runner proxy
- Activation hooks, real leakage detection, and intervention/steering in the cloud runner
- A live Logos integration
- A robust benign-task evaluation pipeline

The current frontier uses synthetic example configurations derived from mock aggregate metrics. Its job is to test the UI and calculation flow, not to support scientific conclusions.

## Formula used in this prototype
For the activation-steering adaptation:

`risk_t = clip((p_t - mu_held) / gap, 0, 1)`

`trust_t = 1 / (1 + lambda * alpha_w * sigma_t)`

`steering_t = alpha_max * risk_t * trust_t`

This is UARD-inspired, but the original UARD reward-discounting theorem does not automatically transfer to this setting.

## Expected `sessions.json` shape
- `schema_version`
- `is_mock`
- `cal: {mu_held, mu_leak, gap}`
- `alpha_max`, `lambda`, `alpha_w`
- `sessions[]`: scenario ID/name, arm, rollout, text, label, pieces, p, sigma, alpha, offset, utility_score, false_alarm
- `utility_evaluations[]`: task ID, task, arm, success, is_mock

## Suggested next steps
1. Validate the real recorder on a tiny batch.
2. Add benign-task evaluations that compare guarded vs unguarded output on the same tasks.
3. Pre-register or fix calibration and test split before looking at final results.
4. Compute confidence intervals over independent scenarios and avoid overclaiming from a small sample.
5. Keep fictional resident secrets out of Git; get explicit consent and delete the data after the agreed test.

---

## v3.1 changes

**Fixed in `app/index.html`**
- Model tokens, scenario names and labels are HTML-escaped (before, a token containing `<img onerror=...>` ran as code).
- Rollout menu is built from the data (it was fixed at 1-6, so rollouts 7-8 from the recorder could not be opened).
- No benign-task evaluations now shows `n/a` instead of a false `0.0%` utility loss.
- The frontier no longer invents five "levels" per method. It plots `sweep` rows from the data file if present, otherwise one point per method. Real alpha sweeps must come from Colab.
- "Sample only" / "synthetic aggregate" labels now follow `is_mock`.
- A file with calibration `gap <= 0` shows an INVALID CALIBRATION warning.

**Fixed in `experiments/colab_phase0_smoke_test.ipynb`**: the activation hook was never defined (NameError); it is now defined in cell 4. Syntax-checked only; not run on a GPU.

**New**
- `recorder/to_v3.py`: converts the Colab recorder's `sessions.json` to this schema (sigma/gap, alpha/alpha_max, false alarms, lead time; refuses a calibration with gap <= 0; never copies the secret).
- `recorder/check_secrets.py`: screens `data/resident_secrets.json` for real-looking secrets, missing consent and duplicates, printing masked values only.

Still NOT done: real alpha sweep, benign-task evaluation, entropy baseline, held-out resident scenarios, Logos integration.

### v3.2
- `to_v3.py` now skips the first 3 tokens when judging alarms (token 0 reflects the prompt, so it read high in every rollout), smooths the projection (rolling mean of 5), and picks the alert threshold automatically: the lowest threshold with at most 20% false alarms on held *unguarded* rollouts. The app applies the same smoothing, so replay shading matches.
- Run: `python3 recorder/to_v3.py recorder_sessions.json data/sessions.json --model Qwen/Qwen2.5-3B-Instruct --scenarios scen.json --utility util.json --sweep sweep.json`
- `data/sessions.json` from a real run contains the model's text including leaked secrets: keep it out of Git (add it to .gitignore).

---

## v3.3: measured results (Qwen2.5-3B-Instruct, recorded on a Colab T4)

9 fictional secrets from residents (consented), 2 attack styles, 8 sampled rollouts per cell, so n = 144 per method.
Direction `d` is from the earlier persona-decay experiment (layer 18), not refit on these secrets.

| Method | Leak rate (95% CI) | Mean push | Benign tasks wrong (of 30) |
|---|---|---|---|
| No guard | 34.0% (26.8-42.1) | 0 | 1 |
| Constant steering, strength 41.9 | 11.1% (7.0-17.3) | 40.7 | 1 |
| UARD-gated, peak 83.7 | 11.1% (7.0-17.3) | 17.0 | 3 |

Early warning on unguarded answers: 76% of leaks flagged before they start (37 of 49), median 6 tokens ahead (max 17); 12.8% of held answers false-alarm.
22 of 49 leaks begin within the first 15 tokens, so there is little room to warn.

**Not established:** UARD matching constant steering with less push is a point estimate; the leak rates are identical and the utility difference (2 tasks of 30) is within noise. Strength x32 (peak 167) reaches 0% leaks but breaks 60% of benign tasks. Weak strengths (<=41.9 peak for UARD) do nothing. The benign set is 30 short factual questions only. The per-token signal may partly track refusal-vs-compliance style. One model, one layer, nine fictional secrets.

### v3.4
- Overview: "Measured highlights" card (leak rate, share of leaks warned before they start, median warning in tokens, false alarms), computed from the loaded file.
- Replay: shows the token where the alarm fired and how many tokens before the secret it was.
- Model Diagnostics: "Is there one universal failure direction?" panel from `generality` in `data/sessions.json` (cosines 0.40 and 0.23; held-out-secret scores 0.92 for the original d vs 1.44 for a direction fitted on the other secrets; 23 testable leaks, so tentative).
- Cloud Model Lab hidden (it was never connected). Maths page now says the update subtracts d.

### v3.5
- New **Live (Colab)** page: paste the https link printed by the Colab live cell and the live demo appears inside the app (sandboxed iframe). Not on-device: the model and guard run on a Colab GPU. The replay pages work without it.
- Live cell: `experiments/live_demo_cell.py` is standalone (fresh Colab runtime, T4 GPU; upload phase1_direction.pt and resident_secrets.json first). Untested on a GPU when written.

### v3.6
- `recorder/sanitize.py` makes a public copy of the results (`data/sessions_public.json`) with every secret replaced by `[SECRET]` and masked tokens shown as `[#]`. It re-scans its output and fails if any secret term is left. Read the output once yourself before publishing.
- The replay app now falls back to `data/sessions_public.json` when `data/sessions.json` is not present (the real file is gitignored).
- `logos/` holds the PLANNED Logos integration (Storage for sharing the sanitized results; a QML-only Basecamp module). Nothing there has been built or run; see `logos/README.md`.

## Run the replay app locally
From this folder: `python3 -m http.server 8000`, then open http://localhost:8000/app/index.html
