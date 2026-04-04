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

# Gap Filler (Pass 2) configuration
MISSING_XPATHS_FILE=./input/missing_xpaths.json
NOTICES_LIST_FILE=./input/notices_list.txt
FILL_GAPS_OUTPUT=./output/gap_filler
EXCLUDE_FILE=./output/selected_notices.txt
DETECT_EFORMS_OUTPUT=./input/eforms_notices.txt
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

Run in background:

```bash
make download-notices-nohup
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

Run in background:

```bash
make load-notices-from-folder-nohup
```

Arguments:
- `-i, --input`: Path to input folder with XML files

---

### Detect eForms

Detect eForms notices from a folder of notices.

```bash
poetry run detect-eforms-cli -o ./input/eforms_notices.txt -d ./input/notices
```

Or with Make:

```bash
make detect-eforms
```

This generates a list of file paths to eForms notices, which is used as input for subsequent sampling steps.

Arguments:
- `-o, --output_file`: Path to output file (list of notice paths)
- `-d, --notices_folder`: Path to notices folder (recursive)

---

### Data Sampler (Pass 1)

Generate sample data sets from MongoDB using basic structural XPath coverage.

```bash
poetry run data-sampler-cli -o ./output -n eforms
```

Or with Make:

```bash
make sample-data-eforms
```

Run in background:

```bash
make sample-data-eforms-nohup
```

Arguments:
- `-o, --output`: Path to output folder
- `-n, --notice_source`: Notice source (`eforms` or `standard_forms`)

---

### Gap Filler (Pass 2) — Find Supplementary Notices

After Pass 1, some XPath entries (particularly those with conditions/predicates) may remain uncovered. The Gap Filler algorithm finds additional notices that cover these missing XPaths using real XPath execution.

#### Prerequisites

1. **Run Pass 1** to get initial coverage
2. **Export missing XPaths from Mapping Workbench** — The Mapping Workbench can export a list of uncovered XPath entries. Save this as a JSON file with the following format:

```json
[
  {
    "sdk_element_id": "BT-27-Procedure",
    "type": "FIELD",
    "absolute_xpath": "/*/cac:TenderingTerms/cac:AwardingTerms/cac:AwardingCriterion[cbc:AwardingCriterionTypeCode/@listName='award-criterion-type']/cbc:Description",
    "xpath_condition": "not(exists(ext:UBLExtensions/ext:UBLExtension/ext:ExtensionContent/efext:EformsExtension/efac:FieldsPrivacy[efbc:FieldIdentifierCode/text()='awa-cri-ord']) and cbc:Description/text() = 'unpublished')",
    "abs_xpath_reduced": "cac:TenderingTerms/cac:AwardingTerms/cac:AwardingCriterion/cbc:Description",
    "iterator_xpath": "/*/cac:TenderingTerms/cac:AwardingTerms/cac:AwardingCriterion"
  }
]
```

3. **Create notice list file** — A text file with one notice path per line:
   ```
   /path/to/notices/notice1.xml
   /path/to/notices/notice2.xml
   ```

4. (Optional) **Create exclude file** — If running after Pass 1, list the already-selected notices to avoid duplicates:
   ```
   /path/to/selected/notice1.xml
   ```

#### Run Gap Filler

```bash
poetry run fill-gaps-cli -x ./input/missing_xpaths.json -n ./input/notices_list.txt -o ./output/gap_filler
```

Or with Make:

```bash
make fill-gaps
```

Run in background (with PID output for monitoring/killing):

```bash
make fill-gaps-nohup
```

#### Output Files

The Gap Filler creates the following files in the output folder:

| File | Description |
|------|-------------|
| `result_notices.txt` | Selected notice paths (one per line) |
| `remaining_uncovered.txt` | Entry IDs that could not be covered by any notice |
| `coverage_report.json` | Detailed coverage mapping with statistics |
| `logs.log` | Runtime log messages (for monitoring progress) |

#### Monitoring

When running in background:
```bash
# Check logs in real-time
tail -f ./output/gap_filler/logs.log

# Get process PID (shown when starting)
# Kill if needed
kill <PID>
```

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

### Query XPaths

Query given list of XPaths in XML files and store results in tabular format.

```bash
poetry run query-xpaths-cli -o ./output.txt -i ./notices.txt -x ./xpaths.txt
```

Arguments:
- `-o, --output_file`: Path to output file
- `-i, --notices_file_list`: Path to file with list of notices
- `-x, --xpaths_file`: File with list of XPaths to query

---

## Full Sampling Pipeline Example

This example shows the complete workflow for generating test data with full XPath coverage:

```bash
# 1. Download notices for a specific time period
make download-notices YEAR_MONTH_RANGE="2024:1-2024:6"

# 2. Detect eForms notices from the downloaded folder
make detect-eforms NOTICES_INPUT_FOLDER=./input/notices DETECT_EFORMS_OUTPUT=./input/eforms_notices.txt

# 3. Run Pass 1 - Basic sampling (from MongoDB or directly from files)
#    This generates initial coverage using structural XPaths
make sample-data-eforms OUTPUT_FOLDER=./output/pass1

# 4. Run Pass 2 - Gap Filler to cover conditional XPaths
#    First, get missing XPaths from Mapping Workbench and save to JSON
#    Then run:
make fill-gaps MISSING_XPATHS_FILE=./input/missing_xpaths.json \
                  NOTICES_LIST_FILE=./input/eforms_notices.txt \
                  FILL_GAPS_OUTPUT=./output/gap_filler \
                  EXCLUDE_FILE=./output/pass1/selected_notices.txt

# 5. Combine results from Pass 1 and Pass 2 for complete test data set
```

---

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
