## Proposed LLM Input Pipeline

### Objective

The goal of this pipeline is to investigate how wearable data quality affects AI-generated health explanations. Three mass-market large language models (LLMs) will be evaluated: ChatGPT, Claude, and Gemini.

### Proposed Pipeline

**1. Data Selection**

The processed Fitbit datasets will be used as input. Each dataset contains three experimental conditions:

- **Baseline:** Original wearable measurements without intentional manipulation.
- **Missing Data:** Measurements with approximately 10% of selected values removed.
- **Noisy Data:** Measurements containing artificially introduced errors, such as timestamp shifts, random variations, and spikes.

For the initial experiment, a participant and a fixed time period (e.g., seven days) will be selected from the daily activity dataset. The same underlying records will be used across all three conditions to support fair comparisons.

**2. Input Preparation**

A Python script will extract the selected wearable measurements and convert them into a standardized text table.

Each input will contain relevant information such as dates, step counts, activity duration, distance travelled, and calories burned.

Participant identifiers and internal manipulation metadata will be excluded. The original, missing, and noisy measurements will be preserved without correcting the introduced errors.

**3. Standardized Prompt**

All three LLMs will receive the same instructions asking them to explain the wearable data in simple, understandable language.

The prompt will request an overview of activity patterns, noticeable trends, and any limitations in the measurements.

The models will not be informed whether the supplied data is original, missing, or noisy. This will help determine whether they independently recognize uncertainty or potentially unreliable measurements.

**4. LLM Interaction**

The prepared prompts will be manually submitted through the regular chat interfaces of:

- ChatGPT (OpenAI)
- Claude (Anthropic)
- Gemini

A new conversation will be used for each experimental condition to minimize the influence of previous interactions. Available personalization settings will be minimized, and the model/version and testing date will be recorded where possible.

**5. Response Collection**

The AI-generated explanations will be saved for later analysis.

Each response will be associated with its LLM, experimental condition, participant/time window, and date of generation.

The original response text will be preserved without editing.

**6. Planned Evaluation**

The explanations will later be compared to investigate whether changes in wearable data quality affect their accuracy, clarity, uncertainty communication, and reliability.

The study will also consider how the explanations might influence users' understanding and trust in AI-generated health information.

### Expected Outcome

The proposed pipeline will provide a consistent method for presenting wearable data of different quality levels to three consumer-facing LLMs.

It will support comparisons of how these systems interpret wearable measurements and whether they communicate potential data limitations appropriately.