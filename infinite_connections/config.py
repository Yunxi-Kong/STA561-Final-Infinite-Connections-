"""Runtime configuration for the A+ upgrade pipeline.

All knobs live here so experiments are reproducible. Environment variables
override defaults; defaults are tuned for RTX 4070 Ti Super 16GB + free
API tiers.

Reading order when the scripts run:
  1. Environment variables (highest priority)
  2. data/config/pipeline.json (optional, user-editable)
  3. Defaults defined in this module (lowest priority)
"""

from __future__ import annotations

import json
import os
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_ROOT = PROJECT_ROOT / "data"
CONFIG_PATH = DATA_ROOT / "config" / "pipeline.json"
ENV_FILE = PROJECT_ROOT / ".env"


def _load_env_file() -> None:
    """Minimal .env loader so the user never has to touch Windows env vars.

    Rules:
      * Lines starting with '#' and blank lines are ignored.
      * KEY=VALUE pairs are added to os.environ only if the key is not
        already set (explicit shell export wins).
      * Surrounding quotes are stripped.
    """
    if not ENV_FILE.exists():
        return
    try:
        for raw in ENV_FILE.read_text(encoding="utf-8").splitlines():
            line = raw.strip()
            if not line or line.startswith("#"):
                continue
            if "=" not in line:
                continue
            key, _, value = line.partition("=")
            key = key.strip()
            value = value.strip().strip('"').strip("'")
            if key and value and key not in os.environ:
                os.environ[key] = value
    except OSError:
        pass


# Load .env before any dataclass defaults read from os.getenv()
_load_env_file()


@dataclass(slots=True)
class OllamaModel:
    """One Ollama model that can act as generator or solver."""

    name: str              # Ollama model tag, e.g. "qwen2.5:7b"
    role: str              # "generator", "solver", "both"
    temperature: float = 0.6
    max_tokens: int = 1024
    timeout_seconds: int = 180


@dataclass(slots=True)
class ExternalSolver:
    """A free-tier LLM endpoint used for multi-solver evaluation only.

    Every supported provider (Cerebras / Groq / Gemini) exposes an
    OpenAI-compatible /v1/chat/completions endpoint, so a single
    client implementation can talk to all three.
    """

    provider: str                   # "cerebras" | "groq" | "gemini"
    model: str
    base_url: str
    env_key_name: str               # env var holding the API key
    rpm_limit: int                  # self-imposed requests per minute
    daily_limit: int                # self-imposed requests per day
    temperature: float = 0.2
    max_tokens: int = 800


@dataclass(slots=True)
class PipelineConfig:
    """End-to-end pipeline configuration."""

    # ── Local Ollama ────────────────────────────────────────────
    ollama_host: str = "http://localhost:11434"
    ollama_generator: OllamaModel = field(
        default_factory=lambda: OllamaModel(
            name=os.getenv("OLLAMA_GENERATOR", "qwen2.5:7b"),
            role="generator",
            temperature=0.8,
            max_tokens=1400,
        )
    )
    ollama_solvers: list[OllamaModel] = field(
        default_factory=lambda: [
            OllamaModel(name=os.getenv("OLLAMA_SOLVER_A", "qwen2.5:7b"), role="solver", temperature=0.2),
            OllamaModel(name=os.getenv("OLLAMA_SOLVER_B", "llama3:8b"), role="solver", temperature=0.2),
        ]
    )

    # ── External free-tier solvers ──────────────────────────────
    external_solvers: list[ExternalSolver] = field(
        default_factory=lambda: [
            ExternalSolver(
                provider="cerebras",
                model=os.getenv("CEREBRAS_MODEL", "qwen-3-235b-a22b-instruct-2507"),
                base_url="https://api.cerebras.ai/v1",
                env_key_name="CEREBRAS_API_KEY",
                rpm_limit=28,      # under the 30 RPM free tier cap
                daily_limit=900,   # conservative vs ~1M tok/day budget
            ),
            ExternalSolver(
                provider="groq",
                model="llama-3.3-70b-versatile",
                base_url="https://api.groq.com/openai/v1",
                env_key_name="GROQ_API_KEY",
                rpm_limit=28,
                daily_limit=1200,
            ),
            ExternalSolver(
                provider="gemini",
                model="gemini-2.5-flash-lite",
                base_url="https://generativelanguage.googleapis.com/v1beta/openai",
                env_key_name="GEMINI_API_KEY",
                rpm_limit=14,
                daily_limit=800,
            ),
        ]
    )

    # ── Embeddings ──────────────────────────────────────────────
    embedding_model: str = os.getenv("EMBED_MODEL", "sentence-transformers/all-MiniLM-L6-v2")
    embedding_device: str = os.getenv("EMBED_DEVICE", "cpu")  # "cuda" if user has GPU free

    # ── Evaluation thresholds ───────────────────────────────────
    # A puzzle is "NYT-plausible" iff >= plausibility_solver_floor solvers
    # recover the intended partition.
    plausibility_solver_floor: int = 3
    plausibility_needs_70b: bool = True  # require >=1 of the 70B-class solvers to agree

    # ── Paths ───────────────────────────────────────────────────
    data_dir: Path = field(default_factory=lambda: DATA_ROOT)
    puzzle_dir: Path = field(default_factory=lambda: DATA_ROOT / "puzzles")
    history_dir: Path = field(default_factory=lambda: DATA_ROOT / "history")
    lexicon_dir: Path = field(default_factory=lambda: DATA_ROOT / "lexicons")
    reports_dir: Path = field(default_factory=lambda: DATA_ROOT / "reports")
    eval_dir: Path = field(default_factory=lambda: DATA_ROOT / "eval")

    def external_solver_by_provider(self, provider: str) -> ExternalSolver | None:
        for solver in self.external_solvers:
            if solver.provider == provider:
                return solver
        return None

    def has_external_key(self, provider: str) -> bool:
        solver = self.external_solver_by_provider(provider)
        return bool(solver and os.getenv(solver.env_key_name))

    def to_dict(self) -> dict[str, Any]:
        payload = asdict(self)
        # Path objects are not JSON-serialisable.
        for key, value in list(payload.items()):
            if isinstance(value, Path):
                payload[key] = str(value)
        return payload


def load_config() -> PipelineConfig:
    """Load config from file if present; otherwise use defaults."""

    config = PipelineConfig()
    if CONFIG_PATH.exists():
        try:
            saved = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            saved = {}
        # Top-level scalar overrides only; nested lists/dataclasses stay as defaults
        # unless a dedicated override API is added later.
        for key in ("ollama_host", "embedding_model", "embedding_device",
                    "plausibility_solver_floor", "plausibility_needs_70b"):
            if key in saved:
                setattr(config, key, saved[key])
    return config


def save_config(config: PipelineConfig) -> None:
    CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
    CONFIG_PATH.write_text(json.dumps(config.to_dict(), indent=2), encoding="utf-8")


# Convenience singleton for scripts that just want defaults.
CONFIG = load_config()
