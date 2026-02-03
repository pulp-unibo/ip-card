# IP Container JSON schema

This repository includes a schema file for the ISOLDE project IP Container JSON, a Python utility for validating JSONC (JSON with Comments) files against the schema, and two examples of JSONC files.

## Validation utility usage

```bash
python parse_json.py --ip <json_file> [--schema <schema_file>] [--export-ods <spreadsheet.ods>] [--export-latex <table.tex>]
```

### Arguments

- `--ip` (required): Path to the JSONC file to validate
- `--schema` (optional): Path to the JSON schema file (default: `20251114.jsonschema`)
- `--export-ods` (optional): When provided, exports the parsed IP card to a two-column ODS spreadsheet
- `--export-latex` (optional): When provided, exports the parsed IP card to a LaTeX table format

### Examples

```bash
# Validate with default schema
python parse_json.py --ip examples/UNIBO_tpu.jsonc

# Validate with custom schema
python parse_json.py --schema custom.jsonschema --ip examples/UNIBO_tpu.jsonc

# Validate and export to ODS
python parse_json.py --ip examples/UNIBO_tpu.jsonc --export-ods IP_card.ods

# Validate and export to LaTeX
python parse_json.py --ip examples/UNIBO_tpu.jsonc --export-latex IP_card.tex

# Export to both formats
python parse_json.py --ip examples/UNIBO_tpu.jsonc --export-ods IP_card.ods --export-latex IP_card.tex
```

## Output

- ✅ Success: "JSON is schema-compliant"
- ❌ Failure: Detailed error message with:
  - Error location (path in JSON structure)
  - Line and column numbers
  - Context around the error

## Requirements

- Python 3.6+
- `jsonschema`
- Optional (for ODS export): `odfpy`

Install dependencies:
```bash
pip install jsonschema
# add odfpy when ODS export is needed
pip install odfpy
```

### LaTeX Export Format

The LaTeX export generates a formatted table using the `booktabs`, `multirow`, and optionally `longtable` packages. The output includes:
- Properly escaped LaTeX special characters
- Section headers with bold formatting
- Nested fields displayed using multirow for better readability
- Professional table formatting with toprule, midrule, and bottomrule
- Scalable output that can be adjusted via the `\scalebox` parameter

To compile the generated LaTeX file, ensure your document preamble includes:
```latex
\usepackage{booktabs}
\usepackage{multirow}
\usepackage{longtable}  % Optional, for multi-page tables
```

## License

Apache-2.0
