# Persona-Guard cloud runner (starter scaffold)

This is an **undeployed starter API**, not a live cloud service. It can generate text using an allowlisted Hugging Face model after deployment. It does not yet implement activation extraction, a risk detector, intervention/steering, trial orchestration, persistence, or evaluation metrics.

## Deploying safely

1. Use a GPU-capable host with enough RAM/VRAM for the chosen model. Free tiers may not provide enough resources or persistent runtime.
2. Set environment variables:
   - `PERSONA_GUARD_API_TOKEN`: long random secret. Required; the API refuses protected requests if absent.
   - `PERSONA_GUARD_CORS_ORIGINS`: comma-separated exact origins for the deployed dashboard. Do not use `*` in a public deployment.
3. Install `requirements.txt` and start with `uvicorn app:app --host 0.0.0.0 --port 8000`.
4. Put it behind the host's HTTPS endpoint. Never place the API token in the HTML or a public repository.
5. Configure the dashboard's Cloud Model Lab with the deployed URL. The dashboard's current health-check is unauthenticated, so it only tests `/health`; `/models` and `/generate` require a Bearer token. A production UI needs a secure authenticated proxy or server-side session before it can call protected routes. Do not embed the secret in browser JavaScript.

## Endpoints
- `GET /health`: status and honest capability flags.
- `GET /models`: allowlist (Bearer token required).
- `POST /generate`: text generation (Bearer token required), body e.g. `{"model_id":"qwen2.5-3b","prompt":"Reply with a harmless greeting.","max_new_tokens":32}`.

Models load lazily and one at a time. Model repositories may have access or license requirements. Change the allowlist only after reviewing each model's license and deployment constraints.

## Safety and research limitations
- Use fictional test secrets only and obtain explicit consent before sending data to a third-party host.
- Do not send real credentials, personal information, private messages, or confidential information.
- The scaffold does not log request bodies intentionally, but hosting platforms may have their own logs/retention policies; review them before use.
- Text generation alone is not a leakage experiment. A research pipeline still needs a fixed prompt set, explicit leak labels, held-out evaluation, benign utility tasks, uncertainty intervals, and model/version metadata.
- Activation hooks and steering are not implemented. Do not report representation drift or Persona-Guard effectiveness from this scaffold.
