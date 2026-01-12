## Description

<!-- Describe your changes here -->

## Checklist

- [ ] I have tested these changes in Wherobots Cloud
- [ ] Notebooks follow the [style guide](../CONTRIBUTING.md#style-guide)

---

## For Release PRs (Wherobots Team Only)

If this PR is part of a wbc-images release, tags must be created after merging:

- [ ] I will create tags from `main` after merge (or tags are not needed for this PR)

**Tagging instructions:** Both v1 and v2 tags should typically point to the same commit unless you know otherwise.

```bash
git checkout main && git pull
git tag v1.X.Y && git tag v2.X.Y-preview
git push origin v1.X.Y v2.X.Y-preview
```

See [CONTRIBUTING.md](../CONTRIBUTING.md#wherobots-contributions) for details.
