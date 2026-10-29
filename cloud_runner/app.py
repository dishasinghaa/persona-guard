"""Starter cloud inference API for Persona-Guard.

This scaffold supports text generation only. It does NOT implement activation
extraction, a leakage detector, or intervention/steering. Deploy behind HTTPS.
"""
import os
from typing import Literal
from fastapi import FastAPI, Header, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

APP_TOKEN = os.environ.get("PERSONA_GUARD_API_TOKEN", "")
ALLOWED_ORIGINS = [x.strip() for x in os.environ.get("PERSONA_GUARD_CORS_ORIGINS", "").split(",") if x.strip()]
MODEL_ALLOWLIST = {
    "qwen2.5-3b": "Qwen/Qwen2.5-3B-Instruct",
    "gemma-3-1b": "google/gemma-3-1b-it",
    "llama-3.2-1b": "meta-llama/Llama-3.2-1B-Instruct",
}
app = FastAPI(title="Persona-Guard Cloud Runner", version="0.1.0")
app.add_middleware(CORSMiddleware, allow_origins=ALLOWED_ORIGINS, allow_credentials=False,
                   allow_methods=["GET", "POST"], allow_headers=["Authorization", "Content-Type"])

class GenerateRequest(BaseModel):
    model_id: Literal["qwen2.5-3b", "gemma-3-1b", "llama-3.2-1b"]
    prompt: str = Field(min_length=1, max_length=12000)
    max_new_tokens: int = Field(default=128, ge=1, le=256)

_model = None
_tokenizer = None
_loaded_id = None

def check_auth(authorization: str | None):
    # Require a strong environment-configured token in deployed environments.
    if not APP_TOKEN:
        raise HTTPException(status_code=503, detail="Server not configured: set PERSONA_GUARD_API_TOKEN")
    if authorization != f"Bearer {APP_TOKEN}":
        raise HTTPException(status_code=401, detail="Unauthorized")

@app.get("/health")
def health():
    return {"status": "ok", "service": "persona-guard-cloud-runner", "generation_ready": True,
            "capabilities": ["text-generation"], "activation_hooks": False}

@app.get("/models")
def models(authorization: str | None = Header(default=None)):
    check_auth(authorization)
    return {"models": [{"id": k, "repo": v} for k, v in MODEL_ALLOWLIST.items()],
            "note": "Model weights load lazily; only one model is resident at a time."}

@app.post("/generate")
def generate(req: GenerateRequest, authorization: str | None = Header(default=None)):
    global _model, _tokenizer, _loaded_id
    check_auth(authorization)
    try:
        import torch
        from transformers import AutoModelForCausalLM, AutoTokenizer
    except ImportError:
        raise HTTPException(status_code=503, detail="Install requirements.txt on the cloud runner")
    repo = MODEL_ALLOWLIST[req.model_id]
    try:
        if _loaded_id != req.model_id:
            # Release the previous model before loading another, avoiding concurrent residency.
            if _model is not None:
                del _model
                _model = None
                _tokenizer = None
                if torch.cuda.is_available(): torch.cuda.empty_cache()
            _tokenizer = AutoTokenizer.from_pretrained(repo, trust_remote_code=False)
            dtype = torch.float16 if torch.cuda.is_available() else torch.float32
            _model = AutoModelForCausalLM.from_pretrained(repo, torch_dtype=dtype, device_map="auto" if torch.cuda.is_available() else None,
                                                          low_cpu_mem_usage=True, trust_remote_code=False)
            if not torch.cuda.is_available(): _model.to("cpu")
            _loaded_id = req.model_id
        inputs = _tokenizer(req.prompt, return_tensors="pt")
        device = next(_model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        with torch.inference_mode():
            out = _model.generate(**inputs, max_new_tokens=req.max_new_tokens, do_sample=False)
        text = _tokenizer.decode(out[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
        return {"model_id": req.model_id, "model_repo": repo, "generated_text": text,
                "max_new_tokens": req.max_new_tokens, "capabilities": {"activation_hooks": False},
                "provenance": "live cloud text generation; not yet a Persona-Guard leakage/steering evaluation"}
    except HTTPException:
        raise
    except Exception as exc:
        # Avoid returning prompts or other potentially sensitive input in errors.
        raise HTTPException(status_code=500, detail=f"Model execution failed ({type(exc).__name__}). Check server logs.")
