# ted-data-sampler

Generator of test data sets for Mapping Suites. Provides CLI tools for downloading TED notices from ted.europa.eu and loading them into MongoDB.

## Requirements

- Python (>=3.9.20, <3.12)
- Poetry for dependency management

## Installation

```bash
make install
```

## Configuration

Create a `.env` file in the project root with the following variables:

```env
MONGO_DB_AUTH_URL=mongodb://admin:admin@localhost:27017/
OUTPUT_FOLDER=./output
NOTICES_INPUT_FOLDER=./input/notices
NOTICES_DOWNLOAD_FOLDER=./input/notices
YEAR_MONTH_RANGE=2024:1-2024:2
```

## Commands

### Download Notices

Download TED notices from ted.europa.eu packages.

```bash
poetry run download-notices-cli -o ./input/notices -r "2024:1-2024:6"
```

Or with Make:

```bash
make download-notices
```

Arguments:
- `-o, --output`: Path to output folder
- `-r, --range`: Year-month range (e.g., `2024:1-2025:6`)

---

### Load Notices

Load XML notices from folder to MongoDB.

```bash
poetry run load-notices-cli -i ./input/notices
```

Or with Make:

```bash
make load-notices-from-folder
```

Arguments:
- `-i, --input`: Path to input folder with XML files

---

### Data Sampler

Generate sample data sets from MongoDB.

```bash
poetry run data-sampler-cli -o ./output -n eforms
```

Or with Make:

```bash
make sample-data-eforms
```

Arguments:
- `-o, --output`: Path to output folder
- `-n, --notice_source`: Notice source (`eforms` or `standard_forms`)

---

### Data Coverage

Analyze XPath coverage based on eForms SDK and stored notices.

```bash
poetry run data-coverage-cli -o ./output -i ./notices -n eforms
```

Arguments:
- `-o, --output`: Path to output folder
- `-i, --input_notices`: Path to notices folder (recursive)
- `-n, --sdk_versions`: SDK versions (comma-separated)

---

### Detect eForms

Detect eForms notices from folder of notices.

```bash
poetry run detect-eforms-cli -o ./output.txt -d ./notices
```

Arguments:
- `-o, --output_file`: Path to output file
- `-d, --notices_folder`: Path to notices folder (recursive)

---

### Query XPaths

Query given list of XPaths in XML files and store results in tabular format.

```bash
poetry run query-xpaths-cli -o ./output.txt -i ./notices.txt -x ./xpaths.txt
```

Arguments:
- `-o, --output_file`: Path to output file
- `-i, --notices_file_list`: Path to file with list of notices
- `-x, --xpaths_file`: File with list of XPaths to query

## Development

Run tests:

```bash
poetry run pytest
```

Activate virtual environment:

```bash
poetry shell
```

## License

This project is licensed under the terms specified in the LICENSE file.
