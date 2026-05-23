# run-radar-run

CLI tool for running a self-hosted tech radar. Ingests a directory of YAML blip definitions and publishes them via pluggable publisher backends (Docker-based).

## Project layout

```
runradarrun/          # main package
  main.py             # CLI entrypoint (argparse + publisher auto-discovery)
  model.py            # data model: Ring, Quadrant, Blip, Radar, AbstractPublisher
  ingest.py           # reads radar directory → Radar object
  output.py           # terminal output (blessed), Docker log streaming
  publishers/
    twbyor.py         # Thoughtworks Build Your Own Radar publisher
    zalando.py        # Zalando Tech Radar publisher
radar/                # sample radar definition (the project's own radar)
tests/                # pytest tests
```

## Radar directory format

A radar directory must contain `specs.yaml` (or `specs.yml`) defining rings and quadrants, then one YAML file per blip at `<quadrant_id>/<ring_id>/<name>.yaml`.

Rings are keyed by position: `inner`, `mid_inner`, `mid_outer`, `outer` (3–4 required).
Quadrants are keyed by position: `top_left`, `top_right`, `bottom_left`, `bottom_right` (exactly 4).

Blip YAML shape:
```yaml
blip:
  name: Some Tool
  is_new: false        # omit or true = new blip; false = was already in this ring
  description: ...
  references: []
  tags: []
```

## Adding a publisher

Drop a new module in `runradarrun/publishers/`. It must define a `Publisher` class that:
- Extends `AbstractPublisher` from `runradarrun.model`
- Implements `cli_id()` (classmethod returning the CLI name)
- Implements `make_output() -> str`
- Optionally implements `run()` and `cleanup()`

Publishers are auto-discovered via `pkgutil` — no registration needed.

## Development

```bash
poetry install          # install deps
poetry run pytest       # run tests
poetry run flake8 .     # lint (max line length 160, see .flake8)
tox                     # full test matrix (py312, py313)
```

Tests live in `tests/`. The test suite is minimal — add tests for any new ingestion logic or model behaviour.

## Releasing

```bash
tox -e release -- patch   # or minor / major
```

This runs tests, bumps the version (`bump2version`), builds, pushes tags, and publishes to PyPI. Must be on `main`.
