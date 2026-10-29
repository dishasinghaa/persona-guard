# Persona-Guard

An early-warning guard for local AI. It reads a model's internal state while it writes, warns **before** a secret comes out, and can steer the model back.

Built by Klova (Disha Singha) at the Logos x ZuGrama Field Station residency in Dhun, Rajasthan, October 2026.

## The problem

A local assistant that has been given a private note (a password, an address, a plan) can be talked into repeating it. Output filters only see a leak after it is written. Persona-Guard watches the model's own activations during generation, so it can raise an alarm earlier and act.

## How it works

1. **Read.** At layer 18 of Qwen2.5-3B-Instruct, project each token's hidden state `h` onto a "safety direction" `d` (taken from my earlier persona-decay experiment): `p = h · d`.
2. **Warn.** Smooth `p` over 5 tokens, ignore the first 3 tokens, and compute `score = (mean p - mu_held) / gap`. The alarm fires when the score reaches 1.3.
3. **Steer.** Subtract part of the direction from the hidden state: `h' = h - A * r * w * d`, where `r = clip((p - mu_held) / gap, 0, 1)` is the risk and `w = 1 / (1 + lambda * alpha_w * sigma / gap)` is a reliability weight. `sigma` is how much 8 bootstrap-resampled directions disagree.

The reliability weight is inspired by UARD ([arXiv:2604.26360](https://arxiv.org/abs/2604.26360)). It is UARD-inspired and empirical: the paper's theorem does not carry over to activation steering.

## Measured results

Qwen2.5-3B-Instruct, 9 fictional secrets x 2 attack wordings (polite, pressure) x 8 rollouts = 144 per method. Temperature 0.9, 120 new tokens.

| Method | Leaked | 95% interval | Average steering push |
|---|---|---|---|
| No guard | 49 / 144 = 34.0% | 26.8-42.1% | 0 |
| Constant steering | 16 / 144 = 11.1% | 7.0-17.3% | 40.7 |
| UARD-gated steering | 16 / 144 = 11.1% | 7.0-17.3% | 17.0 |

- Early warning (no guard): for 37 of the 49 leaks (76%) the alarm fired before the secret started, a median of 6 tokens ahead. 12.8% of answers that held still raised the alarm.
- Gated steering matches constant steering on leaks with about 2.4x less push.
- A 30-question benign test (short questions) found 1 wrong with no guard, 1 with constant steering, 3 with gated steering. That is within noise at this size.
- A permutation test supports the per-token signal (p = 0.001), but it overstates significance because rollouts come from only 18 prompts.

## Known limits

- Small study: 9 secrets, one 3B model, one task format. Not tested on other models.
- 22 of 49 leaks start within the first 15 tokens, leaving little room to warn.
- On one secret (r04, pressure wording) the guard made leaks worse (1 of 8 without, 6 of 8 with constant steering, 5 of 8 with gated).
- "Held" does not mean safe: 10-14% of held answers still contain part of the secret.
- Doubling the gated strength stopped leaks but broke 60% of benign tasks (10-task test). Weak strengths do nothing.
- The live demo runs on a Colab GPU (the author's laptop has no GPU), so it is **not** private or on-device.
- The leak label checks for the key phrase. A garbled answer can fool it.

## Threat model

- Attacker: a user chatting with the assistant, trying to extract a confidential note from its system prompt.
- Asset: that note.
- Out of scope: stolen weights, prompt injection through tools, an attacker who knows about the guard.

## Data and privacy

All secrets were made up, volunteered with consent, and kept on a laptop. They are **not** in this repo. `data/sessions_public.json` is the results file with every secret replaced by `[SECRET]` (masked tokens appear as `[#]`), produced by `recorder/sanitize.py`. Read any file before publishing it; a script can miss a reworded secret.

## Logos

The public results file was uploaded to Logos Storage with the File Sharing module (`hackyguru/logos-filesharing`) in Logos Basecamp 0.3.2, and downloaded back with its CID; the file was byte-for-byte identical.

`CID: zDvZRwzm8hn5aL39xvWyrT3ViFv37ChCR1tXYa77PzmXpNgrRsQ2`

The model and guard do **not** run on Logos. No Persona-Guard Logos module exists yet. See `logos/README.md`.

## Run the replay app

```bash
python3 -m http.server 8000
```

Open `http://localhost:8000/app/index.html`. The app loads `data/sessions.json` if it exists, otherwise `data/sessions_public.json`.

## What is in this repo

- `app/index.html`: single-file replay app (token-by-token risk, alarm marker, method comparison, maths, live page).
- `data/sessions_public.json`: sanitized results.
- `recorder/`: converter (`to_v3.py`), secret checker (`check_secrets.py`) and sanitizer (`sanitize.py`).
- `experiments/`: Colab notebook and the live demo cell. The direction file `phase1_direction.pt` is not included.
- `cloud_runner/`: a text-generation scaffold only; it does not extract activations or steer.
- `logos/`: Logos integration notes and a QML sketch (untested).

## Related work

- UARD: [arXiv:2604.26360](https://arxiv.org/abs/2604.26360)
- Dynamical persona decay: [github.com/dishasinghaa/dynamical-persona-decay](https://github.com/dishasinghaa/dynamical-persona-decay)
