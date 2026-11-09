"""Run with python -m llm_pipeline; preview is the default."""

import argparse
from datetime import datetime, timezone
import hashlib
import importlib.metadata
import json
import os
from pathlib import Path
import time
from uuid import uuid4

from .prompts import prepare_prompts
from .providers import KEYS, generate


def write_json(path, value):
    path.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--participant", required=True)
    parser.add_argument("--start", required=True, help="First baseline date, YYYY-MM-DD")
    parser.add_argument("--days", type=int, default=7)
    parser.add_argument("--data-dir", type=Path, default=Path("experimental_data/daily_activity"))
    parser.add_argument("--output-dir", type=Path, default=Path("llm_runs"))
    parser.add_argument("--providers", nargs="+", choices=list(KEYS), default=list(KEYS))
    parser.add_argument("--max-tokens", type=int, default=2048)
    parser.add_argument("--send", action="store_true", help="Send prompts to APIs (may incur charges)")
    args = parser.parse_args()
    if args.max_tokens < 1:
        parser.error("--max-tokens must be positive")
    try:
        prompts = prepare_prompts(args.data_dir, args.participant, args.start, args.days)
    except (ValueError, OSError) as exc:
        parser.error(str(exc))
    providers = list(dict.fromkeys(args.providers))
    models = {}
    if args.send:
        from dotenv import load_dotenv
        load_dotenv(Path.cwd() / ".env")
        missing = []
        for provider in providers:
            model_var = f"{provider.upper()}_MODEL"
            for variable in (KEYS[provider], model_var):
                if not os.getenv(variable, "").strip():
                    missing.append(variable)
            models[provider] = os.getenv(model_var, "").strip()
        if missing:
            parser.error("Set these variables in .env or your environment: " + ", ".join(missing))
    run_id = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ") + "_" + uuid4().hex[:8]
    run_dir = args.output_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=False)
    versions = {}
    for package in ("pandas", "openai", "anthropic", "google-genai"):
        try:
            versions[package] = importlib.metadata.version(package)
        except importlib.metadata.PackageNotFoundError:
            versions[package] = None
    manifest = {"run_id": run_id, "participant": args.participant, "start": args.start,
                "days": args.days, "data_dir": str(args.data_dir.resolve()), "models": models,
                "max_output_tokens": args.max_tokens, "sent": args.send,
                "package_versions": versions, "prompts": {}, "results": []}
    for condition, prompt in prompts.items():
        path = run_dir / condition
        path.mkdir()
        (path / "prompt.txt").write_text(prompt, encoding="utf-8")
        manifest["prompts"][condition] = hashlib.sha256(prompt.encode("utf-8")).hexdigest()
    write_json(run_dir / "manifest.json", manifest)
    print(f"Prompts and metadata saved to {run_dir}")
    failed = False
    if args.send:
        for condition, prompt in prompts.items():
            for provider in providers:
                started = time.perf_counter()
                result = {"provider": provider, "requested_model": models[provider],
                          "condition": condition, "created_at": datetime.now(timezone.utc).isoformat(),
                          "prompt_sha256": manifest["prompts"][condition]}
                try:
                    result.update(generate(provider, models[provider], prompt, args.max_tokens))
                    result["status"] = "ok" if result["text"] else "empty"
                    failed |= not bool(result["text"])
                    (run_dir / condition / f"{provider}.txt").write_text(result["text"], encoding="utf-8")
                except Exception as exc:
                    # Avoid persisting provider exception messages that may contain credentials.
                    result.update(status="error", error_type=type(exc).__name__,
                                  http_status=getattr(exc, "status_code", None))
                    failed = True
                result["elapsed_seconds"] = round(time.perf_counter() - started, 3)
                write_json(run_dir / condition / f"{provider}.json", result)
                manifest["results"].append({k: v for k, v in result.items() if k not in {"text", "raw"}})
                write_json(run_dir / "manifest.json", manifest)
                print(f"{condition}/{provider}: {result['status']}", flush=True)
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
