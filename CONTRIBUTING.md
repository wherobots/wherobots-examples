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

## Style Guide

When writing example notebooks, follow these guidelines.

### Prose/Markdown style

#### Technical points

- Opening image
  - If this is a solution notebook, start with a banner that repeats the imagery used for the notebook's thumbnail. It should be about 1200x220 px. (See [Generate PMTiles using Wherobots](https://github.com/wherobots/wherobots-examples/blob/main/Analyzing_Data/PMTiles-railroad.ipynb) for an example.)
  - Otherwise, start with this small logo: `![Wherobots logo](../assets/img/header-logo.png)`
- Headings
  - Use `#` (H1) once in a notebook, as the title that immediately follows the opening image.
  - Use `##` (H2) for most section headings, and `###` (H3) if a second level makes sense.
  - Anything smaller should probably be omitted or simply emphasized with bold text.
  - If there's text that comes after the heading, put them in the same cell.
- Put code blocks in markdown cells *only* when it is not also used in one of the code cells.
  - Examples: a Pythonic alternative to SQL or something that should be avoided
  - Function or variable names should be enclosed in `code formatting`.
- Use bold only for
  - Presenting or defining a new term.
  - Creating hierarchy when adding another heading level would get cluttered.
- Use `>` indents for definitions.

#### Writing style

- Focus on the scenario at hand. Use links to docs or other resources for expanded coverage of a topic.
- Focus on education and reader empowerment. Avoid a promotional tone.
- Use few or no emojis.
  - Never use emojis instead of markdown-formattted bullets or numbers. Emoji bullets can impede accessibility for people using screen readers.

### Code blocks and style

- Precede code cells with with a markdown cell with a `##` H2 or `###` H3 headline to facilitate rapid scanning.

For example:

> ### Isochrone implementation example
> 
> ```
> ST_Isochrone(geometry, 1, 'car', false)
> ```

  - Do include a brief description for new topics. 
  - Don't describe anything covered in the Getting Started notebooks (e.g. getting the `sedona` context).
  - Describe the code block before (above) the code block. Use comments to call out specific, interesting parameters or functions.
- Comments should be one short line and support or expand what's in prose, as opposed to repeating it.
- Whenever possible, cells should output something. If the cell isn't designed to output already (e.g. a map), provide context or confirmation of what happened with calls like `show`, `count`, or `printSchema`.
- Always use [`wkls`](https://github.com/wherobots/wkls) instead of hard-coding admin boundaries.
