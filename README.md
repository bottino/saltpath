# saltpath

Gets the course of a sailing ship based on a GPX file.

## Setup

Use [uv](https://docs.astral.sh/uv/)

```bash
uv sync
```

Then, to do a simple acquisition in the current directory, run:

```bash
uv run saltpath.py <your-gpx-file> .
```

You can find the different options like so:

```bash
uv run saltpath.py --help
```
