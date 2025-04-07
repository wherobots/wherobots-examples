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