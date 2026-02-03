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
from pathlib import Path
from typing import Any, Iterable, List, Optional, Sequence, Tuple

from jsonschema import validate, ValidationError

LEVEL_COLOR_PALETTES = [
    ("#f9d0d0", "#fde8e8"),  # Level 1 - reds
    ("#d6f2dc", "#edf9f0"),  # Level 2 - greens
    ("#d8e8fb", "#edf3fe"),  # Level 3 - blues
    ("#ebd8fb", "#f5edfe"),  # Level 4 - purples
]

VALUE_COLORS = ("#e4e4e4", "#f4f4f4")

def strip_jsonc_comments(text: str) -> str:
    """Strip // and /* */ comments from JSONC while preserving strings."""
    lines = text.split('\n')
    result = []
    
    for line in lines:
        # Process character by character to handle strings correctly
        cleaned = []
        in_string = False
        escape_next = False
        i = 0
        
        while i < len(line):
            char = line[i]
            
            # Handle escape sequences
            if escape_next:
                cleaned.append(char)
                escape_next = False
                i += 1
                continue
            
            # Handle backslash (escape character)
            if char == '\\' and in_string:
                cleaned.append(char)
                escape_next = True
                i += 1
                continue
            
            # Handle quote (string delimiter)
            if char == '"':
                cleaned.append(char)
                in_string = not in_string
                i += 1
                continue
            
            # If we're in a string, just copy the character
            if in_string:
                cleaned.append(char)
                i += 1
                continue
            
            # Check for // comment (only outside strings)
            if i + 1 < len(line) and line[i:i+2] == '//':
                # Rest of line is a comment, stop processing
                break
            
            # Check for /* comment (only outside strings)
            if i + 1 < len(line) and line[i:i+2] == '/*':
                # Find the closing */
                close_idx = line.find('*/', i + 2)
                if close_idx != -1:
                    # Skip past the comment
                    i = close_idx + 2
                    continue
                else:
                    # Comment continues to end of line
                    break
            
            # Regular character outside string and comment
            cleaned.append(char)
            i += 1
        
        result.append(''.join(cleaned))
    
    return '\n'.join(result)


def flatten_fields(data: Any, path: Optional[Sequence[str]] = None) -> List[Tuple[List[str], Any]]:
    """Return ([path segments], value) entries for each leaf node."""
    if path is None:
        path = []
    entries: List[Tuple[List[str], Any]] = []

    if isinstance(data, dict):
        for key, value in data.items():
            entries.extend(flatten_fields(value, [*path, str(key)]))
    elif isinstance(data, list):
        for idx, value in enumerate(data):
            entries.extend(flatten_fields(value, [*path, f"[{idx}]"]))
    else:
        entries.append(([str(part) for part in path], data))

    return entries


def export_to_ods(flattened: Iterable[Tuple[List[str], Any]], output_path: str) -> None:
    try:
        from odf.opendocument import OpenDocumentSpreadsheet
        from odf.table import Table, TableColumn, TableRow, TableCell
        from odf.text import P
        from odf.style import Style, TextProperties, TableColumnProperties, TableCellProperties
    except ImportError as exc:
        raise RuntimeError(
            "Exporting to ODS requires the 'odfpy' package. Install it with 'pip install odfpy'."
        ) from exc

    doc = OpenDocumentSpreadsheet()
    header_style = Style(name="HeaderCellStyle", family="table-cell")
    header_style.addElement(TextProperties(fontweight="bold"))
    doc.styles.addElement(header_style)

    flattened_entries = list(flattened)
    max_depth = max((len(parts) for parts, _ in flattened_entries), default=0)

    def chars_to_cm(char_count: int) -> float:
        # rough conversion to keep columns readable while not overly wide
        return max(2.0, char_count * 0.25 + 0.5)

    column_widths = [0] * max_depth
    value_column_width = 0

    for parts, value in flattened_entries:
        for idx in range(max_depth):
            segment = parts[idx] if idx < len(parts) else ""
            column_widths[idx] = max(column_widths[idx], len(segment))
        value_text = "" if value is None else str(value)
        value_column_width = max(value_column_width, len(value_text))

    table = Table(name="IP Card")
    for idx, width in enumerate(column_widths):
        column_style = Style(name=f"ColLevel{idx + 1}", family="table-column")
        column_style.addElement(TableColumnProperties(columnwidth=f"{chars_to_cm(width):.2f}cm"))
        doc.automaticstyles.addElement(column_style)
        table.addElement(TableColumn(stylename=column_style))

    value_column_style = Style(name="ColValue", family="table-column")
    value_column_style.addElement(TableColumnProperties(columnwidth=f"{chars_to_cm(value_column_width):.2f}cm"))
    doc.automaticstyles.addElement(value_column_style)
    table.addElement(TableColumn(stylename=value_column_style))

    header = TableRow()
    header_styles: List[Style] = []
    for idx in range(max_depth):
        base_color = ["#b30000", "#0f8a2c", "#0f4c81", "#5a189a"]
        color = base_color[idx] if idx < len(base_color) else "#333333"
        header_style = Style(name=f"HeaderLevel{idx + 1}", family="table-cell")
        header_style.addElement(
            TableCellProperties(backgroundcolor=color)
        )
        header_style.addElement(TextProperties(fontweight="bold", color="#ffffff"))
        doc.styles.addElement(header_style)
        header_styles.append(header_style)

    value_header_style = Style(name="HeaderValue", family="table-cell")
    value_header_style.addElement(TableCellProperties(backgroundcolor="#000000"))
    value_header_style.addElement(TextProperties(fontweight="bold", color="#ffffff"))
    doc.styles.addElement(value_header_style)

    for level in range(max_depth):
        label = f"Level {level + 1}"
        cell = TableCell(stylename=header_styles[level], valuetype="string")
        cell.addElement(P(text=label))
        header.addElement(cell)
    value_header_cell = TableCell(stylename=value_header_style, valuetype="string")
    value_header_cell.addElement(P(text="Value"))
    header.addElement(value_header_cell)
    table.addElement(header)

    shaded_levels = min(max_depth, len(LEVEL_COLOR_PALETTES))
    level_states = [{"prev": None, "index": 0} for _ in range(shaded_levels)]
    level_cell_styles: dict[Tuple[int, int], Style] = {}
    value_cell_styles: dict[int, Style] = {}
    value_state = {"prev_nonempty": False, "index": 0}

    def get_level_cell_style(level: int, color_index: int) -> Style:
        key = (level, color_index)
        style = level_cell_styles.get(key)
        if style is None:
            color = LEVEL_COLOR_PALETTES[level][color_index]
            style = Style(name=f"Level{level + 1}Shade{color_index}", family="table-cell")
            style.addElement(TableCellProperties(backgroundcolor=color))
            doc.automaticstyles.addElement(style)
            level_cell_styles[key] = style
        return style

    def get_value_cell_style(color_index: int) -> Style:
        style = value_cell_styles.get(color_index)
        if style is None:
            color = VALUE_COLORS[color_index]
            style = Style(name=f"ValueShade{color_index}", family="table-cell")
            style.addElement(TableCellProperties(backgroundcolor=color))
            doc.automaticstyles.addElement(style)
            value_cell_styles[color_index] = style
        return style

    for parts, value in flattened_entries:
        row = TableRow()
        for depth in range(max_depth):
            segment = parts[depth] if depth < len(parts) else ""
            cell_kwargs = {"valuetype": "string"}
            if segment and depth < shaded_levels:
                state = level_states[depth]
                if state["prev"] is None:
                    state["index"] = 0
                elif segment != state["prev"]:
                    state["index"] = 1 - state["index"]
                state["prev"] = segment
                cell_kwargs["stylename"] = get_level_cell_style(depth, state["index"])
            elif depth < shaded_levels:
                level_states[depth]["prev"] = None

            cell = TableCell(**cell_kwargs)
            cell.addElement(P(text=segment))
            row.addElement(cell)

        value_text = "" if value is None else str(value)
        value_kwargs = {"valuetype": "string"}
        if value_text:
            if value_state["prev_nonempty"]:
                value_state["index"] = 1 - value_state["index"]
            else:
                value_state["index"] = 0
            value_state["prev_nonempty"] = True
            value_kwargs["stylename"] = get_value_cell_style(value_state["index"])
        else:
            value_state["prev_nonempty"] = False
        value_cell = TableCell(**value_kwargs)
        value_cell.addElement(P(text=value_text))
        row.addElement(value_cell)
        table.addElement(row)

    doc.spreadsheet.addElement(table)

    out_path = Path(output_path)
    doc.save(str(out_path), addsuffix=not out_path.suffix)


def export_to_latex(data: dict, output_path: str) -> None:
    """Export IP card data to LaTeX table format."""
    
    def escape_latex(text: str) -> str:
        """Escape special LaTeX characters."""
        if text is None:
            return ""
        text = str(text)
        replacements = {
            '\\': r'\textbackslash{}',  # Must be first to avoid double-escaping
            '&': r'\&',
            '%': r'\%',
            '$': r'\$',
            '#': r'\#',
            '_': r'\_',
            '{': r'\{',
            '}': r'\}',
            '~': r'$\sim$',
            '<': r'$<$',
            '>': r'$>$',
            '^': r'\textasciicircum{}',
        }
        for old, new in replacements.items():
            text = text.replace(old, new)
        return text
    
    def format_field_name(key: str) -> str:
        """Convert camelCase field names to human-readable format."""
        import re
        # Insert space before capitals
        result = re.sub(r'([a-z])([A-Z])', r'\1 \2', key)
        # Capitalize first letter
        result = result[0].upper() + result[1:] if result else result
        return result
    
    def process_dict_to_rows(d: dict, section_name: str = None) -> List[Tuple[str, str, str]]:
        """Convert a dictionary to table rows. Returns list of (field, subfield, value) tuples."""
        rows = []
        
        for key, value in d.items():
            field_name = format_field_name(key)
            
            if isinstance(value, dict):
                # Nested dictionary - field name becomes a multirow parent
                subrows = []
                for subkey, subvalue in value.items():
                    subfield_name = format_field_name(subkey)
                    subvalue_str = str(subvalue) if subvalue is not None else ""
                    subrows.append((field_name, subfield_name, subvalue_str))
                
                # First subrow includes the parent field name with multirow
                if subrows:
                    rows.extend(subrows)
            else:
                # Simple key-value pair
                value_str = str(value) if value is not None else ""
                rows.append((field_name, "", value_str))
        
        return rows
    
    latex_lines = []
    
    # Header comments
    latex_lines.append("% Please add the following required packages to your document preamble:")
    latex_lines.append("% \\usepackage{booktabs}")
    latex_lines.append("% \\usepackage{multirow}")
    latex_lines.append("% \\usepackage{longtable}")
    latex_lines.append("% Note: It may be necessary to compile the document several times to get a multi-page table to line up properly")
    latex_lines.append("")
    latex_lines.append("\\begin{table}[h!]")
    latex_lines.append("% \\caption{IP Card}")
    latex_lines.append("% \\resizebox{\\textwidth}{!}{%")
    latex_lines.append("\\centering")
    latex_lines.append("\\scalebox{0.5558}{%")
    latex_lines.append("\\begin{tabular}{@{}lll@{}}")
    latex_lines.append("\\toprule")
    
    # Process each major section
    section_order = [
        ("basicInfo", "Basic Info"),
        ("systemLevelFeatures", "System-Level Features"),
        ("architecture", "Architecture"),
        ("microarchitecture", "Microarchitecture"),
        ("software", "Software"),
        ("integration", "Integration"),
        ("physicalImplementation", "Physical Implementation"),
    ]
    
    for section_key, section_title in section_order:
        if section_key not in data:
            continue
            
        section_data = data[section_key]
        
        # Section header
        latex_lines.append(f"\\multicolumn{{3}}{{c}}{{\\textbf{{{escape_latex(section_title)}}}}} \\\\ \\toprule")
        
        # Process section content
        rows = process_dict_to_rows(section_data, section_title)
        
        # Group rows by field name for multirow handling
        current_field = None
        field_rows = []
        all_field_groups = []
        
        # First, group all rows by field
        for field, subfield, value in rows:
            if field != current_field:
                if field_rows:
                    all_field_groups.append((current_field, field_rows))
                current_field = field
                field_rows = []
            field_rows.append((subfield, value))
        
        # Don't forget the last group
        if field_rows:
            all_field_groups.append((current_field, field_rows))
        
        # Now output all field groups with proper midrule placement
        for idx, (field_name, field_data) in enumerate(all_field_groups):
            if len(field_data) > 1:
                # Use multirow for the field name
                latex_lines.append(f"\\multirow{{{len(field_data)}}}{{*}}{{\\textit{{{escape_latex(field_name)}}}}} & {escape_latex(field_data[0][0])} & {escape_latex(field_data[0][1])} \\\\")
                for subf, val in field_data[1:]:
                    latex_lines.append(f" & {escape_latex(subf)} & {escape_latex(val)} \\\\")
            else:
                # Single row
                if field_data[0][0]:  # Has subfield
                    latex_lines.append(f"\\multirow{{1}}{{*}}{{\\textit{{{escape_latex(field_name)}}}}} & {escape_latex(field_data[0][0])} & {escape_latex(field_data[0][1])} \\\\")
                else:  # No subfield, just field and value
                    latex_lines.append(f"\\textit{{{escape_latex(field_name)}}} & {escape_latex(field_data[0][1])} &  \\\\")
            
            # Add midrule after each field group except the last one in the section
            if idx < len(all_field_groups) - 1:
                latex_lines.append("\\midrule")
        
        # Add toprule after each section (except the last one)
        if section_key != section_order[-1][0]:
            # Check if there are more sections to come
            remaining_sections = section_order[section_order.index((section_key, section_title)) + 1:]
            if any(s[0] in data for s in remaining_sections):
                latex_lines.append("\\toprule")
    
    # Footer
    latex_lines.append("\\bottomrule")
    latex_lines.append("\\end{tabular}%")
    latex_lines.append("}")
    latex_lines.append("\\end{table}")
    
    # Write to file
    out_path = Path(output_path)
    with open(out_path, 'w', encoding='utf-8') as f:
        f.write('\n'.join(latex_lines))


def main(schema: str = "schema.jsonschema", ip: str = None, export_ods: Optional[str] = None, export_latex: Optional[str] = None):
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
        return

    if export_ods:
        try:
            export_to_ods(flatten_fields(data), export_ods)
            print(f"📝 Exported IP card to {export_ods}")
        except RuntimeError as exc:
            print(f"❌ Failed to export to ODS: {exc}")
    
    if export_latex:
        try:
            export_to_latex(data, export_latex)
            print(f"📝 Exported IP card to LaTeX: {export_latex}")
        except Exception as exc:
            print(f"❌ Failed to export to LaTeX: {exc}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Validate JSON file against schema")
    parser.add_argument("--schema", default="schema.jsonschema", type=str, 
                       help="Path to the JSON schema file")
    parser.add_argument("--ip", type=str, required=True,
                       help="Path to the IP JSON file to validate")
    parser.add_argument("--export-ods", type=str,
                       help="Path to export a flattened, human-readable ODS spreadsheet")
    parser.add_argument("--export-latex", type=str,
                       help="Path to export a LaTeX table file")
    
    args = parser.parse_args()
    main(schema=args.schema, ip=args.ip, export_ods=args.export_ods, export_latex=args.export_latex)
