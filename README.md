# IP Container JSON schema

This repository includes a schema file for the ISOLDE project IP Container JSON, a Python utility for validating JSONC (JSON with Comments) files against the schema, and two examples of JSONC files.

## Validation utility usage

```bash
python parse_json.py --ip <json_file> [--schema <schema_file>]
```

### Arguments

- `--ip` (required): Path to the JSONC file to validate
- `--schema` (optional): Path to the JSON schema file (default: `20251114.jsonschema`)

### Examples

```bash
# Validate with default schema
python parse_json.py --ip examples/UNIBO_tpu.jsonc

# Validate with custom schema
python parse_json.py --schema custom.jsonschema --ip examples/UNIBO_tpu.jsonc
```

## Output

- ✅ Success: "JSON is schema-compliant"
- ❌ Failure: Detailed error message with:
  - Error location (path in JSON structure)
  - Line and column numbers
  - Context around the error

## Requirements

- Python 3.6+
- `jsonschema` package

Install dependencies:
```bash
pip install jsonschema
```

## License

Apache-2.0