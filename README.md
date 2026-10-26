Run, Radar, Run
===============

Using run-radar-run
-------------------

### Requirements

* Python3.12+
* Docker (for the TWBYOR radar)

### Running the Radar

Install it from PyPI:

```bash
$ pip install run-radar-run
```

Then run it from a directory containing a `radar/` subdirectory (the default input):

```bash
$ run-radar-run
```

Or pass a specific radar directory as an argument:

```bash
$ run-radar-run path/to/radar
```

When working from a clone of this repository, use Poetry instead:

```bash
$ poetry install
$ poetry run run-radar-run
```

Run `run-radar-run --help` for all options (publisher selection, output path, running the radar, etc.).

### Publishers

Publishers are the frameworks you can use to publish your tech radar.

As of early 2025, the publishers available are:

* Thoughtworks' Bring Your Own Radar
* Zalando Tech Radar
