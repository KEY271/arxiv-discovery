# arXiv-discovery

Lightweight tool to discover arXiv papers using [Sentence Transformers](https://huggingface.co/sentence-transformers). Score and rank papers based on their relevance to your research interests. The results are presented in a user-friendly HTML format.

## Requirements
- uv (installation: https://docs.astral.sh/uv/getting-started/installation/)

## Installation
Clone the repository and install dependencies:

```bash
git clone https://github.com/KEY271/arxiv-discovery.git
cd arxiv-discovery
uv sync
```

## Quickstart
Copy the example settings file, and edit it.

```bash
cp settings.example.json5 settings.json5
# Edit settings.json5.
```

Load python virtual environment and run the tool:

```bash
source .venv/bin/activate
python main.py
```

Then `out/results_{date}.json5` will be generated. To view the results in your browser, run:

```bash
python show.py
```

A sample of the output HTML:
![Sample Output](/images/sample_output.png)
