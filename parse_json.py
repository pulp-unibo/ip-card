#
# Copyright (C) 2025 University of Bologna.
#
# Author: Francesco Conti f.conti@unibo.it
#
# ----------------------------------------------------------------------
# SPDX-License-Identifier: Apache-2.0
#
# Licensed under the Apache License, Version 2.0 (the License); you may
# not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
# www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an AS IS BASIS, WITHOUT
# WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.

import json
import argparse
from jsonschema import validate, ValidationError

def strip_jsonc_comments(text: str) -> str:
    import re
    lines = text.split('\n')
    result = []
    
    for line in lines:
        # Remove // comments but preserve the line structure
        line = re.sub(r'//.*$', '', line)
        # Remove /* */ comments on the same line
        line = re.sub(r'/\*.*?\*/', '', line)
        result.append(line)
    
    return '\n'.join(result)


def main(schema: str = "schema.jsonschema", ip: str = None):
    if ip is None:
        raise ValueError("IP argument is required")
    
    # Load schema
    try:
        with open(schema, "r", encoding="utf-8") as f:
            schema_data = json.load(f)
    except FileNotFoundError:
        print(f"❌ Schema file not found: {schema}")
        return
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON in schema file: {e}")
        return

    # Load IP json
    try:
        with open(ip, "r", encoding="utf-8") as f:
            raw = f.read()
    except FileNotFoundError:
        print(f"❌ IP file not found: {ip}")
        return
    
    nocomments = strip_jsonc_comments(raw)
    
    try:
        data = json.loads(nocomments)
    except json.JSONDecodeError as e:
        print(f"❌ Invalid JSON after comment removal: {e}")
        print(f"Error at line {e.lineno}, column {e.colno}")
        # Show the problematic area
        lines = nocomments.split('\n')
        start_line = max(0, e.lineno - 3)
        end_line = min(len(lines), e.lineno + 2)
        print("Context around error:")
        for i in range(start_line, end_line):
            marker = ">>> " if i == e.lineno - 1 else "    "
            print(f"{marker}{i+1:3d}: {lines[i]}")
        return

    try:
        validate(instance=data, schema=schema_data)
        print("✅ JSON is schema-compliant")
    except ValidationError as e:
        print("❌ JSON is NOT compliant")
        print("Path:", list(e.path))      # where in the JSON the error occurred
        print("Message:", e.message)      # human-readable error


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate JSON file against schema")
    parser.add_argument("--schema", default="schema.jsonschema", type=str, 
                       help="Path to the JSON schema file")
    parser.add_argument("--ip", type=str, required=True,
                       help="Path to the IP JSON file to validate")
    
    args = parser.parse_args()
    main(schema=args.schema, ip=args.ip)
