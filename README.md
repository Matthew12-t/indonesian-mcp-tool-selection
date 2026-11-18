# Indonesian MCP tool selection study

Source code and aggregate results for **“Language Effects on MCP Tool Selection: A Paired Evaluation of Three Local Language Models”** by Indah Pratiwi Hutahaean (Universitas Komputer Indonesia).

The experiment compares English and Indonesian tool descriptions against English, Indonesian, and Indonesian–English code-mixed requests. It uses 43 tools from five MCP servers, 150 labeled requests, three repeats, and three locally hosted models. Only the first structured tool call is scored; tools are not executed.

## Contents

- `notebooks/01_tool_snapshot.py`: snapshot MCP tool definitions.
- `notebooks/00_build_dataset.py`, `00a_translations.py`, `00b_build_dataset.py`: construct and verify the translated tool catalog and paired requests.
- `notebooks/mcp-tool-*/experiment.py`: exact model-specific Kaggle scripts used for the completed runs; the adjacent metadata files record their Kaggle configuration.
- `notebooks/02_experiment.py`: common experiment source.
- `notebooks/03_analyze_results.py`: validate downloaded input and run hashes, require exactly 2,700 unique calls per model, and write aggregate and paired summaries.
- `results/`: aggregate CSV files produced from the completed, downloaded Kaggle outputs.

## Results

All three runs completed with 2,700 calls each and no recorded API errors. Mean strict tool-selection accuracy across six language conditions was **87.4%** for Qwen3 8B, **88.1%** for Llama 3.1 8B, and **0.0%** for Mistral 7B. Mistral returned ordinary text, often mentioning a tool, but did not produce a structured tool call in any of its 2,700 responses under this setup. The CSV files contain the condition-level results and task-cluster bootstrap contrasts.

## Reproducing the analysis

The dataset used for the runs is currently a **private** Kaggle dataset (`matthew10101/mcp-tool-selection-indonesian`); it and the raw model responses are intentionally absent from this repository. With access to the dataset and the completed kernel outputs, place the four dataset JSON files in `dataset_downloaded/` and the raw JSONL plus run manifest for each model in `experiments/{qwen3_8b,llama3.1_8b,mistral_7b}/`. Then run:

```bash
python notebooks/03_analyze_results.py dataset_downloaded experiments analysis
```

The analysis exits if a dataset or raw-output checksum differs from its manifest, if a run does not contain 2,700 calls, or if any expected model/description/query/repeat/task combination is missing.

The original runs are available on Kaggle to their account's authorized viewers: [Qwen3 8B](https://www.kaggle.com/code/matthew10101/mcp-tool-qwen3-8b), [Llama 3.1 8B](https://www.kaggle.com/code/matthew10101/mcp-tool-llama31-8b), and [Mistral 7B](https://www.kaggle.com/code/matthew10101/mcp-tool-mistral-7b).

## Scope

These scripts and aggregates document the reported experiment. The dataset is constructed rather than sampled from production traffic; the results measure first-call structured invocation under the recorded prompt, Ollama version, and model digests. They do not measure tool execution or multi-turn repair.
