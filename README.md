# Inspector
Generate text and visual summaries of GitHub Workflows in repos.

This will generate and overview of the entire repository, and individual workflow diagrams for each workflow.



Tagging:

```
git tag -a -m "Testing Release" v0.5
git push --follow-tags
```

Usage:

```
name: Execute Repository Test Action
on:
  push:
    branches:
      - "feature-*"
jobs:
  run_steps:
    runs-on: ubuntu-20.04
    steps:
      - name: Generate CI documentation.
        uses: Compton-NIST/Inspector@v0.5
```


Usage (setting artifact name):

```
name: Execute Repository Test Action
on:
  push:
    branches:
      - "feature-*"
jobs:
  run_steps:
    runs-on: ubuntu-20.04
    steps:
      - name: Generate CI documentation.
        uses: Compton-NIST/Inspector@v0.5
        with:
          artifact_name: _docs
```