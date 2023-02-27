# Inspector
Generate text and visual summaries of GitHub Workflows in repos.

This will generate and overview of the entire repository, and individual workflow diagrams for each workflow.


To Run:

```
pip install -r requirements.txt
python app.py
```

To use the GitHub workflow, two environment variables are required:

- REPOS - A list of repositories separated by a comma.  A single repository is acceptable.
- WORKFLOW_GITHUB_TOKEN - This is a developer token that should have read access to the repositories in the list.

For example:

```
WORKFLOW_GITHUB_TOKEN=ght_mygithubtokenvalue123
REPOS=usnistgov/OSCAL,usnistgov/oscal-content,usnistgov/liboscal-java,usnistgov/oscal-cli,usnistgov/oscal-tools
```

These can be set in the repository to execute the action, or for local use, the value can be placed into a `.env` file.  See `sample.env`.