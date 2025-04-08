## Pre-commit Setup

We use pre-commit hooks to maintain code quality and automate documentation updates. Pre-commit runs automatically when you attempt to commit changes, ensuring that all notebooks are clean and documentation is up-to-date.

### Installation

To install pre-commit:

```bash
pip install pre-commit
pre-commit install
```

This will install pre-commit and set up the git hooks defined in our `.pre-commit-config.yaml` file.

### Pre-commit Hooks

We use two primary hooks:

1. **Notebook Cleaning**: This hook removes execution counts and outputs from notebooks to keep diffs clean and focused on content changes rather than execution artifacts.

2. **README Generator**: This hook automatically updates the README.md file based on the notebook file structure, ensuring that our documentation accurately reflects the current state of available examples.

You can run the hooks manually on all files with:

```bash
pre-commit run --all-files
```

Or on staged files only:

```bash
pre-commit run
```

## Community Contributions

If you would like to contribute a notebook and add it to Wherobots Example Notebooks, open a pull request with your contribution and work with the reviewers to get your notebook merged. If merged, it will make it into the next eligible release. Additionally we are happy to work with you to share your work with the broader Apache Sedona and Wherobots user community via our newsletter or other mediums.

## Wherobots Contributions

If you are a member of the Wherobots org, the following instructions apply.

To release a version of these notebooks, make a tag of the commit to release, naming it based on the release you want to target.

```
git tag v1.6.0
git push origin v1.6.0
```

Then, use the Github UI to make a release from the tag.

If a release for notebooks has already been published, remake the tag:

```
git tag -d v1.6.0
git push --delete origin v1.6.0
git tag v1.6.0
git push origin v1.6.0
```

then delete the old release in the Github UI after the tag is made. Create the new release in the Github UI, marking the previous tag to compare against.