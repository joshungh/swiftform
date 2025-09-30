#!/usr/bin/env python3
"""
Recreate mappings.json with current PDFs and schemas
"""

import json
from pathlib import Path
from datetime import datetime

training_dir = Path("training_pairs")
pdfs_dir = training_dir / "pdfs"
schemas_dir = training_dir / "schemas"

# Get all PDFs and their matching schemas
pdf_files = sorted(pdfs_dir.glob("*.pdf"))
mappings = []

for pdf_path in pdf_files:
    pdf_name = pdf_path.stem
    schema_file = f"{pdf_name}.json"
    schema_path = schemas_dir / schema_file

    if schema_path.exists():
        mappings.append({
            "pdf": pdf_path.name,
            "schema": schema_file,
            "name": pdf_name
        })
        print(f"✓ Mapped: {pdf_path.name} -> {schema_file}")

# Save mappings
mappings_data = {
    "pairs": mappings,
    "created": datetime.now().isoformat(),
    "total": len(mappings)
}

mappings_file = training_dir / "mappings.json"
with open(mappings_file, 'w') as f:
    json.dump(mappings_data, f, indent=2)

print(f"\n✓ Created mappings.json with {len(mappings)} pairs")