# Multi-provider API pipeline

Run from the repository root. Initial support is daily activity, with baseline,
missing, and noisy conditions. Each condition makes three independent API calls
(nine calls per run). The same prompt string is sent to every selected provider.
These are API models; they do not reproduce consumer chat app settings or tools.

## Step-by-step: source CSV to saved responses

### 1. Open the project terminal

In VS Code, open the `Honors` folder and use a PowerShell terminal in that folder.
You should see `requirements.txt`, `manipulate_dailyactivity.py`, and the
`llm_pipeline` directory. All commands below run from this repository root.

The API pipeline currently supports daily activity only. The sleep, weight, and
other manipulation scripts are separate workflows described in the root README.

### 2. Set up Python once

If you already have a working environment, skip creating another one.

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

In later terminals, activate the same environment again. If PowerShell blocks
activation, use `.\.venv\Scripts\python.exe` instead of `python` in the commands
below; activation is not required when you use that interpreter directly.

### 3. Configure the providers you want to use

Create `.env` only if it does not already exist:

```powershell
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
```

Edit `.env` in VS Code. For each provider you intend to send to, fill in its
`*_API_KEY` and `*_MODEL` entries. Use the full secret key and an exact model ID
available to that account. Never paste keys into prompts, source files, or chat.
You do not need keys to preview and validate locally.

Provider names for commands are `gemini`, `openai`, and `anthropic` (Claude).
Only selected providers need configuration. Confirm API billing/credits in your
provider account before sending paid requests.

### 4. Generate the experimental CSVs

Check that `data_files/dailyActivity_merged.csv` exists, then run:

```powershell
python manipulate_dailyactivity.py
```

This overwrites these generated files in `experimental_data/daily_activity/`:

| File | Meaning |
|---|---|
| `baseline.csv` | Original measurements with parsed dates |
| `missing_10_percent.csv` | Approximately 10% of measurement cells removed |
| `noisy_data_internal.csv` | Noisy values plus internal matching/experimental metadata |
| `noisy_data.csv` | Noisy values without that metadata |

The noisy generator selects approximately 30% of each noise group. Selected
numerical-noise rows target two distinct measurements; timestamp rows shift
their date. A fixed seed makes the same inputs/code reproducible. Rerunning
unchanged code will not randomly give a failing participant different changes.
Skip regeneration when you want to keep the existing experimental CSVs.

Optional: `python process_dailyactivity.py` produces processed CSVs in
`llm_inputs/daily_activity/` and a dataset-wide structural report in
`evaluation/daily_activity/`. The API pipeline reads `experimental_data` directly,
so that processing step is not required for API runs.

### 5. Preview and validate one participant's date window

```powershell
python -m llm_pipeline --participant 1503960366 --start 2016-03-30 --days 7
```

This example selects March 30 through April 5, 2016. With the current generated
data, it has seven daily records, nine removed measurements, and two changed
noisy measurements. Different inputs or generator settings can change those counts.
Change `--participant`, `--start`, and `--days` for other selections. A window
selects available records; it does not invent records for absent days. Check the
reported record count if your design requires a full week.

No API requests are made. The terminal prints a new `llm_runs/<run>/` path.
Open **that run's** `validation.txt` and the three `prompt.txt` files.

Both conditions must pass for this participant/window:

- Missing: at least two previously present measurement cells removed.
- Noisy: at least two measurement cells changed relative to baseline.
- Timestamp changes do not count toward either measurement minimum.

Two cells can be in the same column on different days; this rule does not require
two different measurement types. Reports also show changed days, changed dates,
the threshold, per-condition pass status, and each before/after value.

If the report says **BLOCKED**, prompts/reports are saved but no API requests can
be sent. Choose another participant or date window and preview again, or revise
the generation method deliberately and regenerate. The program does not select
another window or change data automatically. A passing report confirms enough
changed cells, not that the error severity suits the study.

### 6. Send to one provider first

Use the same participant, start, and days as your passing preview. For Gemini:

```powershell
python -m llm_pipeline --participant 1503960366 --start 2016-03-30 --days 7 --send --providers gemini
```

For OpenAI or Claude separately:

```powershell
python -m llm_pipeline --participant 1503960366 --start 2016-03-30 --days 7 --send --providers openai
python -m llm_pipeline --participant 1503960366 --start 2016-03-30 --days 7 --send --providers anthropic
```

Each command sends three independent requests: baseline, missing, and noisy.
Run only the providers you intend to test; these requests may incur charges.
Validation runs again before sending. This command creates a new run and rebuilds
prompts from the current CSVs; it does not submit an earlier run's saved files.
Keep CSVs and selection arguments unchanged between preview and send.

When all three accounts are ready, send to all three with one command:

```powershell
python -m llm_pipeline --participant 1503960366 --start 2016-03-30 --days 7 --send --providers gemini openai anthropic
```

This sends nine requests. Each provider receives identical prompt text for each
condition, with no conversation history. The participant ID and condition labels
are excluded from the prompt. Instructions and the entire selected table are sent
together in each request.

### 7. Find and review results

Open the new run path printed by the send command:

```text
llm_runs/<run>/
  validation.txt          Readable comparison and PASS/BLOCKED result
  validation.json         Same validation in structured form
  manifest.json           Selection, models, versions, prompt hashes, outcomes
  baseline/
    prompt.txt            Exact input text
    gemini.txt            Returned explanation (if successful)
    gemini.json           Full response details or failure metadata
  missing/                Same structure
  noisy/                  Same structure
```

Other selected providers create `openai.*` and `anthropic.*` files. Check all three
conditions for `ok` in `manifest.json`. Inspect response completion/stop fields in
the provider JSON files too: a nonempty response can still be truncated. Failed
calls may have a JSON error record without a response `.txt` file.

Every rerun creates another folder and resends every selected call; it does not
resume failed calls or overwrite earlier runs. Old responses still correspond to
their old saved prompts, even after you regenerate the experimental CSVs.

### 8. Troubleshoot a stopped or failed run

| Result | Action |
|---|---|
| Validation `BLOCKED` | Read the report; select a qualifying window or revise generation before sending |
| No records / reference mismatch / duplicate reference dates | Check participant, dates, and the three source CSVs; structural errors can stop before a run folder is created |
| Missing environment variable | Fill the selected provider's key and model entries in `.env` |
| `AuthenticationError`, HTTP 401 | Check the full secret key; replace an invalid key |
| `RateLimitError`, HTTP 429 | Check provider quota, billing, and rate limits; the manifest does not retain detailed API error messages |
| Connection error | Check internet access and execution-environment network permissions |
| Empty response or incomplete/truncated output | Inspect the provider JSON and model settings before using the response |

Exit code `0` means preview passed or all requested calls returned nonempty text.
Exit code `1` means validation blocked or a call failed/returned empty text. Command
argument/configuration and structural selection errors can exit with code `2`.

## Setup

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
if (-not (Test-Path .env)) { Copy-Item .env.example .env }
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

Each run also saves `validation.txt` (readable comparison) and `validation.json`
(structured details). These internal reports contain the participant ID, changed
days/cells, removed measurements, timestamp changes, and every before/after value
relative to baseline. They are not included in API prompts. Records are matched
by original dates; duplicate reference dates are rejected as ambiguous.

For each participant's selected date window, missing must remove at least two
previously present measurement cells and noisy must change at least two
measurement cells compared with baseline. These may be on the same day or in the
same measurement column on different days. Timestamp shifts do not count toward
this minimum. Both reports record the threshold and per-condition pass status.
Otherwise preview exits with
status 1 after saving reports and prompts, and `--send` is blocked before any API
requests. Choose another window or revise the condition data. Existing baseline
missing values and corruption flags alone do not count as changes. Passing this
check establishes the presence of changes, not their experimental severity.

The daily activity generator now selects approximately 30% of rows in each noise
group, with two distinct measurement columns targeted per selected numerical-noise
row. Timestamp rows still receive a date shift only. Random selection and rounding
can still leave individual windows below the minimum; validation blocks those
windows rather than silently modifying them to pass. Existing saved runs retain
their original prompts and responses after CSV regeneration.

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
