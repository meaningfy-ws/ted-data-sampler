# ted-data-sampler

Generator of test data sets for Mapping Suites.

## Requirements

- Python (>=3.9.20, <3.12)
- Poetry for dependency management

## Installation

1. Clone the repository:
```bash
git clone https://github.com/meaningfy/ted-data-sampler.git
cd ted-data-sampler
```

2. Install dependencies using Poetry:
```bash
poetry install
```

## Usage

The project provides several CLI commands:

- `data-sampler-cli`: Generate sample data sets
- `data-coverage-cli`: Analyze data coverage
- `detect-eforms-cli`: Detect eForms notices
- `query-xpaths-cli`: Query XPaths in notices

To run any command, use Poetry:

```bash
poetry run data-sampler-cli
poetry run data-coverage-cli
poetry run detect-eforms-cli
poetry run query-xpaths-cli
```

## Development

To activate the virtual environment:

```bash
poetry shell
```

To run tests:

```bash
poetry run pytest
```

## License

This project is licensed under the terms specified in the LICENSE file.
