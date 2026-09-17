# Wherobots Examples — Sedona-Sail dev runtime

This branch is the example set shipped with the **`0.0.1-jameswillis` dev runtime**, which runs
[sedona-sail](https://github.com/james-willis/sail) — [Sail](https://github.com/lakehq/sail) with the
[SedonaDB](https://sedona.apache.org/sedonadb/) spatial kernels — in place of a JVM Spark cluster.
It contains a single notebook: start a Sail session and run SpatialBench Q3. The full example
library lives on [`main`](https://github.com/wherobots/wherobots-examples).

## Contributing

See [CONTRIBUTING.md](CONTRIBUTING.md) for contribution guidelines, pre-commit setup, documentation publishing workflow, local preview instructions, and style guide.

## Repository structure

```
.
|-- CONTRIBUTING.md
|-- Getting_Started
|   `-- Sedona_Sail_SpatialBench_Q3.ipynb
`-- Makefile

```

### Assets folder

The following describes the purpose of each assets' subfolder:

- `.../assets/conf` - Map style configurations and other notebook settings
- `.../assets/img` -  Images used in the notebooks.
