#!/usr/bin/env python3
"""
Validate PDF-to-XF Schema training pairs
Checks that each PDF has a corresponding schema and they're valid
"""

import os
import json
from pathlib import Path
from typing import Dict, List, Tuple


def validate_json_schema(schema_path: Path) -> Tuple[bool, str]:
    """Validate that a schema file contains valid JSON and required structure"""
    try:
        with open(schema_path, 'r') as f:
            schema = json.load(f)

        # Check for required top-level structure
        if not isinstance(schema, dict):
            return False, "Schema is not a JSON object"

        if schema.get("name") != "xf:form":
            return False, "Schema must have name='xf:form'"

        if "props" not in schema:
            return False, "Schema missing 'props' field"

        if "children" not in schema.get("props", {}):
            return False, "Schema missing props.children"

        children = schema["props"]["children"]
        if not isinstance(children, list):
            return False, "props.children must be an array"

        if len(children) == 0:
            return False, "Schema has no pages defined"

        # Count fields
        field_count = count_fields(schema)

        return True, f"Valid (contains {field_count} fields)"

    except json.JSONDecodeError as e:
        return False, f"Invalid JSON: {e}"
    except Exception as e:
        return False, f"Error reading file: {e}"


def count_fields(node: Dict) -> int:
    """Count the number of fields in a schema"""
    count = 0

    if isinstance(node, dict):
        name = node.get("name", "")

        # Count actual fields (not containers)
        if name.startswith("xf:") and name not in ["xf:form", "xf:page", "xf:group"]:
            count += 1
        elif name == "composite:deficiencies":
            count += 1

        # Recurse into children
        props = node.get("props", {})
        children = props.get("children", [])
        if isinstance(children, list):
            for child in children:
                count += count_fields(child)

    return count


def main():
    """Main validation function"""

    print("=== Validating PDF-to-XF Schema Training Pairs ===\n")

    training_dir = Path("training_pairs")
    pdfs_dir = training_dir / "pdfs"
    schemas_dir = training_dir / "schemas"

    # Check directories exist
    if not pdfs_dir.exists():
        print("❌ PDFs directory not found: training_pairs/pdfs/")
        return

    if not schemas_dir.exists():
        print("❌ Schemas directory not found: training_pairs/schemas/")
        return

    # Get all PDFs
    pdf_files = sorted(pdfs_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files\n")

    # Check each PDF for corresponding schema
    valid_pairs = []
    missing_schemas = []
    invalid_schemas = []

    print("Checking PDF-Schema pairs:")
    print("-" * 60)

    for pdf_path in pdf_files:
        pdf_name = pdf_path.stem
        schema_name = f"{pdf_name}.json"
        schema_path = schemas_dir / schema_name

        print(f"\n📄 {pdf_path.name}")

        if schema_path.exists():
            # Validate the schema
            is_valid, message = validate_json_schema(schema_path)

            if is_valid:
                print(f"   ✅ Schema found and valid: {message}")
                valid_pairs.append({
                    "pdf": pdf_path.name,
                    "schema": schema_name,
                    "message": message
                })
            else:
                print(f"   ⚠️  Schema found but invalid: {message}")
                invalid_schemas.append({
                    "pdf": pdf_path.name,
                    "schema": schema_name,
                    "error": message
                })
        else:
            print(f"   ❌ Missing schema: {schema_name}")
            missing_schemas.append({
                "pdf": pdf_path.name,
                "expected_schema": schema_name
            })

    # Summary
    print("\n" + "=" * 60)
    print("VALIDATION SUMMARY")
    print("=" * 60)

    total = len(pdf_files)
    valid = len(valid_pairs)
    missing = len(missing_schemas)
    invalid = len(invalid_schemas)

    print(f"\nTotal PDFs: {total}")
    print(f"✅ Valid pairs: {valid}")
    print(f"❌ Missing schemas: {missing}")
    print(f"⚠️  Invalid schemas: {invalid}")

    # Show what needs to be fixed
    if missing_schemas:
        print("\n" + "=" * 60)
        print("ACTION REQUIRED: Missing Schemas")
        print("=" * 60)
        print("\nCreate these schema files in training_pairs/schemas/:")
        for item in missing_schemas:
            print(f"  • {item['expected_schema']}")

        print("\nYou can create a schema file by:")
        print("1. Copying and renaming an existing similar schema")
        print("2. Creating a new file with your XF JSON schema")
        print("3. Using the sample schemas as templates")

    if invalid_schemas:
        print("\n" + "=" * 60)
        print("ACTION REQUIRED: Fix Invalid Schemas")
        print("=" * 60)
        for item in invalid_schemas:
            print(f"\n{item['schema']}:")
            print(f"  Error: {item['error']}")

    # Ready to train?
    if valid == total:
        print("\n" + "=" * 60)
        print("✅ ALL PAIRS VALID - READY TO TRAIN!")
        print("=" * 60)
        print("\nYour training data is ready. You can now run:")
        print("  python train_from_pairs.py")

        # Create updated mappings file
        mappings = {
            "pairs": valid_pairs,
            "total": len(valid_pairs),
            "validated": True
        }

        mappings_file = training_dir / "mappings_validated.json"
        with open(mappings_file, 'w') as f:
            json.dump(mappings, f, indent=2)

        print(f"\n✅ Validation results saved to: {mappings_file}")
    else:
        completion = (valid / total) * 100
        print(f"\n📊 Training data is {completion:.0f}% complete")
        print(f"   Add {missing + invalid} more valid schemas to complete")

    # List orphaned schemas (schemas without PDFs)
    schema_files = list(schemas_dir.glob("*.json"))
    pdf_names = {p.stem for p in pdf_files}
    orphaned = []

    for schema_path in schema_files:
        schema_stem = schema_path.stem
        if schema_stem not in pdf_names:
            orphaned.append(schema_path.name)

    if orphaned:
        print("\n" + "=" * 60)
        print("⚠️  Orphaned Schemas (no matching PDF)")
        print("=" * 60)
        for schema in orphaned:
            print(f"  • {schema}")
        print("\nThese schemas don't have matching PDFs and won't be used for training")


if __name__ == "__main__":
    main()