# Basic usage

Analyse a git repository's commit history and contributor patterns.

## Install

```bash
pip install git-analyser
```

## CLI

Pass a local path or remote URL to a git repository:

```bash
git-analyser ./my-repo
git-analyser ./my-repo --json
git-analyser https://github.com/owner/repo.git
```

## Python

```python
from git_analyser.core import analyse_repo

result = analyse_repo("./my-repo")
print(result.commit_count, result.authors)
print(result.learning_signals)
print(result.suspicious_flags)
```

## HTTP

Start the server, then POST a JSON body with a `repo` field (a path or URL):

```bash
git-analyser serve --port 8007

curl -H 'Content-Type: application/json' \
  -d '{"repo": "./my-repo"}' \
  http://localhost:8007/analyse
```
