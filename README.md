# git-analyser

Git repository analyser — part of the analyser family.

Walks git history to extract commit patterns, file churn, contributor signals, and change velocity. Dispatches file content to code-analyser for per-file quality signals across the history.

**Status:** Coming soon. Name reserved.

## Installation

```bash
pip install git-analyser
```

## Usage

```bash
git-analyser .                    # analyse current repo
git-analyser path/to/repo --json
git-analyser serve                # FastAPI server on port 8007
```

## Analyser family

| Tool | Purpose | Port |
|---|---|---|
| document-analyser | PDF, Word, text | 8000 |
| speech-analyser | Audio, video transcription | 8001 |
| video-analyser | Video quality, scenes, OCR | 8002 |
| records-analyser | CSV, Excel, JSON | 8003 |
| code-analyser | Source code, multi-language | 8004 |
| wordpress-analyser | WP themes and plugins | 8005 |
| folder-analyser | Project structure | 8006 |
| git-analyser | Git history and churn | 8007 |
