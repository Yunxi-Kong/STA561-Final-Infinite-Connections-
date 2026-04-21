"""One-shot bootstrap: install Python deps, download NLTK data, verify Ollama.

Run this ONCE on your Windows box after pulling the upgrade:

    python scripts/setup_env.py

What it does:

1. pip install -r requirements.txt (or tells you what's missing)
2. Downloads NLTK data: wordnet, cmudict, averaged_perceptron_tagger,
   omw-1.4 (~15MB total).
3. Downloads the sentence-transformers MiniLM model (~80MB) once so
   later runs are offline.
4. Probes your local Ollama at http://localhost:11434 and lists the
   models you already have pulled; prints recommended upgrade commands.
5. Writes a summary to data/reports/setup_summary.json so we can cite
   the environment state in the technical appendix.
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SUMMARY_PATH = ROOT / "data" / "reports" / "setup_summary.json"
ENV_FILE = ROOT / ".env"


def _bootstrap_env_file() -> None:
    """Load .env so later steps see the keys the user pasted there."""
    if not ENV_FILE.exists():
        return
    for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
        line = raw.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, _, value = line.partition("=")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and value and key not in os.environ:
            os.environ[key] = value


_bootstrap_env_file()


def _section(title: str) -> None:
    bar = "=" * 68
    print(f"\n{bar}\n  {title}\n{bar}", flush=True)


def _run(cmd: list[str], *, check: bool = True) -> tuple[int, str, str]:
    print(f"$ {' '.join(cmd)}", flush=True)
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.stdout:
        print(result.stdout.rstrip(), flush=True)
    if result.returncode != 0 and result.stderr:
        print(result.stderr.rstrip(), file=sys.stderr, flush=True)
    if check and result.returncode != 0:
        sys.exit(result.returncode)
    return result.returncode, result.stdout, result.stderr


def step_pip_install() -> dict:
    _section("1. Install Python dependencies")
    req_path = ROOT / "requirements.txt"
    if not req_path.exists():
        print("requirements.txt not found, skipping.")
        return {"ok": False, "reason": "no_requirements"}
    rc, _, _ = _run(
        [sys.executable, "-m", "pip", "install", "--upgrade", "pip", "--quiet"],
        check=False,
    )
    rc2, _, _ = _run(
        [sys.executable, "-m", "pip", "install", "-r", str(req_path), "--quiet"],
        check=False,
    )
    return {"ok": rc2 == 0, "pip_return_code": rc2}


def step_nltk_data() -> dict:
    _section("2. Download NLTK corpora (wordnet, cmudict, POS tagger)")
    try:
        import nltk  # type: ignore[import-untyped]
    except ImportError:
        print("NLTK missing. Install step must have failed.")
        return {"ok": False, "reason": "nltk_missing"}
    for resource in ("wordnet", "cmudict", "averaged_perceptron_tagger", "omw-1.4"):
        print(f"  > nltk.download({resource!r})")
        nltk.download(resource, quiet=True)
    return {"ok": True, "resources": ["wordnet", "cmudict", "averaged_perceptron_tagger", "omw-1.4"]}


def step_embedding_model() -> dict:
    _section("3. Cache the sentence-transformers embedding model")
    try:
        from sentence_transformers import SentenceTransformer  # type: ignore[import-untyped]
    except ImportError:
        return {"ok": False, "reason": "sentence_transformers_missing"}
    model_name = "sentence-transformers/all-MiniLM-L6-v2"
    print(f"Loading {model_name} (first time will download ~80MB)...")
    start = time.time()
    SentenceTransformer(model_name)
    return {"ok": True, "model": model_name, "load_seconds": round(time.time() - start, 2)}


def step_ollama_probe() -> dict:
    _section("4. Probe local Ollama daemon")
    try:
        from infinite_connections.ollama_client import OllamaClient, OllamaError
    except ImportError:
        print("infinite_connections.ollama_client not importable - are you in the project root?")
        return {"ok": False, "reason": "import_error"}

    client = OllamaClient()
    try:
        models = client.list_models()
    except OllamaError as exc:
        print(f"  Ollama unreachable: {exc}")
        print("  -> Start Ollama (the desktop app or `ollama serve`) and rerun this script.")
        return {"ok": False, "reason": "ollama_unreachable"}
    print(f"  Installed models: {models or '(none)'}")

    recommended = {
        "qwen2.5:7b": "Current local baseline (keep).",
        "llama3:8b": "Secondary solver (keep, provides architecture diversity).",
        "qwen3.5:9b": "RECOMMENDED upgrade for generator role (if listed in your Ollama library).",
    }
    pull_needed = [m for m in recommended if m not in models]
    if pull_needed:
        print("\n  Recommended pulls (run manually):")
        for model in pull_needed:
            print(f"    ollama pull {model}     # {recommended[model]}")
    return {"ok": True, "installed_models": models, "recommended_missing": pull_needed}


def step_external_keys() -> dict:
    _section("5. External solver API keys (free tiers)")
    providers = {
        "CEREBRAS_API_KEY": "https://cloud.cerebras.ai  (signup, no card, 1M tokens/day free)",
        "GROQ_API_KEY":     "https://console.groq.com   (signup, no card, ~14K req/day free)",
        "GEMINI_API_KEY":   "https://aistudio.google.com/app/apikey  (Google login, 1K req/day free)",
    }
    status = {}
    for env_name, url in providers.items():
        present = bool(os.getenv(env_name))
        mark = "SET " if present else "MISS"
        print(f"  {mark}  {env_name}  -> {url}")
        status[env_name] = present
    if not all(status.values()):
        print(
            "\n  Missing keys are OK; the multi-solver pipeline skips any"
            " provider whose key is missing and continues with the rest.\n"
            "  The pipeline needs at least ONE external key to produce the"
            " 70B calibration signal. Cerebras alone is sufficient."
        )
    return {"ok": True, "providers": status}


def main() -> int:
    summary = {}
    summary["pip"] = step_pip_install()
    summary["nltk"] = step_nltk_data() if summary["pip"]["ok"] else {"ok": False, "reason": "pip_failed"}
    summary["embedding"] = (
        step_embedding_model() if summary["pip"]["ok"] else {"ok": False, "reason": "pip_failed"}
    )
    summary["ollama"] = step_ollama_probe()
    summary["keys"] = step_external_keys()

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2), encoding="utf-8")
    print(f"\nWrote {SUMMARY_PATH}")
    return 0 if all(s.get("ok") for s in summary.values()) else 1


if __name__ == "__main__":
    sys.exit(main())
