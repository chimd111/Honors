# Multi-provider API pipeline

Run from the repository root. Initial support is daily activity, with baseline,
missing, and noisy conditions. Each condition makes three independent API calls
(nine calls per run). The same prompt string is sent to every selected provider.
These are API models; they do not reproduce consumer chat app settings or tools.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
Copy-Item .env.example .env
```

Create keys while signed in to your own accounts:

- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys
- Gemini: https://aistudio.google.com/apikey

Put the keys in `.env` and fill in `OPENAI_MODEL`, `ANTHROPIC_MODEL`, and
`GEMINI_MODEL` with exact model IDs enabled in your accounts. No model is silently
chosen for you. `.env` is ignored by Git; do not paste keys into code or chat.
Existing environment variables take precedence over `.env`. Provider API billing
and access must be enabled separately where required.

## Preview and send

Generate prompts locally first (no keys required):

```powershell
python -m llm_pipeline --participant 1503960366 --start 2016-03-25 --days 7
```

Inspect the generated `prompt.txt` files, then send:

```powershell
python -m llm_pipeline --participant 1503960366 --start 2016-03-25 --days 7 --send
```

Optional: `--providers openai anthropic` selects providers; `--max-tokens 2048`
sets an output cap. `--data-dir` selects a directory with the three required
experimental daily activity CSVs. Do not point this at `llm_inputs`, because noisy
selection needs `noisy_data_internal.csv` and its `OriginalActivityDate` reference field.

Each unique `llm_runs/<run>/` directory contains:

- `manifest.json`: participant/window, requested models, versions, prompt hashes,
  timestamps and statuses. This internal file contains the participant ID.
- `<condition>/prompt.txt`: exact prompt sent, with identifiers and condition labels excluded.
- `<condition>/<provider>.txt`: unedited extracted response text.
- `<condition>/<provider>.json`: full SDK response, including returned model,
  usage and completion/stop information, plus timing and request provenance.

Original timestamps select the records; manipulated timestamps remain in the
model's table. The selection window includes the start and excludes start + days.
Missing measurements are written as `NA`. No missing values or noisy measurements
are repaired. Reference-date multiplicities must agree across conditions.

API failures are recorded by exception class and HTTP status without persisting
exception messages. Other calls continue; any failed or empty response makes the
process exit with status 1. Successful nonempty responses may still be truncated:
inspect provider stop/status fields before evaluation. Rerunning creates a new
run and resends all selected calls. There is no automatic experiment resume.
Token caps and sampling behavior differ between models; identical prompts do not
guarantee identical generation behavior. Pin exact model versions for experiments.

Official SDK references: [OpenAI](https://developers.openai.com/api/reference/python),
[Anthropic](https://platform.claude.com/docs/en/api/python/messages/create),
[Google](https://googleapis.github.io/python-genai/).
