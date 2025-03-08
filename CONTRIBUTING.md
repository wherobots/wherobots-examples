## Community Contributions

If you would like to contribute a notebook and see it added to Wherobots Example Notebooks, simply open a PR and work with the reviewers to get your notebook merged. It will make it into the next release.

## Wherobots Contributions

To release a version of these notebooks, make a tag of the commit to release, naming it based on the release you want to target.

```
git tag v1.6.0
git push origin v1.6.0
```

Then use the Github UI to make a release from the tag.

If a release for notebooks has already been published, remake the tag

```
git tag -d v1.6.0
git push --delete origin v1.6.0
git tag v1.6.0
git push origin v1.6.0
```

then delete the old release in the Github UI after the tag is made. Create the new release in the Github UI, marking the previous tag to compare against.