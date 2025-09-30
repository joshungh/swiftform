"""
Training Data Manager for PDF-to-XF Schema Mapping
This module manages the pairing of PDF forms with their corresponding XF schemas
for training OpenAI models to accurately generate schemas from new PDFs.
"""

import os
import json
import hashlib
import PyPDF2
from typing import Dict, List, Any, Optional, Tuple
from datetime import datetime
from pathlib import Path


class TrainingDataManager:
    """Manages PDF-to-XF schema training data pairs"""

    def __init__(self, data_dir: str = "training_data"):
        """
        Initialize the training data manager

        Args:
            data_dir: Directory to store training data pairs
        """
        self.data_dir = Path(data_dir)
        self.pdf_dir = self.data_dir / "pdfs"
        self.schema_dir = self.data_dir / "schemas"
        self.mappings_file = self.data_dir / "mappings.json"

        # Create directories if they don't exist
        self.pdf_dir.mkdir(parents=True, exist_ok=True)
        self.schema_dir.mkdir(parents=True, exist_ok=True)

        # Load existing mappings
        self.mappings = self._load_mappings()

    def _load_mappings(self) -> Dict[str, Any]:
        """Load existing PDF-to-schema mappings"""
        if self.mappings_file.exists():
            with open(self.mappings_file, 'r') as f:
                return json.load(f)
        return {
            "pairs": [],
            "metadata": {
                "created": datetime.now().isoformat(),
                "last_updated": datetime.now().isoformat(),
                "total_pairs": 0
            }
        }

    def _save_mappings(self):
        """Save mappings to disk"""
        self.mappings["metadata"]["last_updated"] = datetime.now().isoformat()
        self.mappings["metadata"]["total_pairs"] = len(self.mappings["pairs"])
        with open(self.mappings_file, 'w') as f:
            json.dump(self.mappings, f, indent=2)

    def _extract_pdf_text(self, pdf_path: str) -> str:
        """Extract text content from PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
        return text

    def _extract_pdf_structure(self, pdf_path: str) -> Dict[str, Any]:
        """Extract structural information from PDF"""
        structure = {
            "num_pages": 0,
            "has_forms": False,
            "field_count": 0,
            "sections": [],
            "tables_detected": False
        }

        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                structure["num_pages"] = len(pdf_reader.pages)

                # Check for form fields
                if pdf_reader.get_form_text_fields():
                    structure["has_forms"] = True
                    structure["field_count"] = len(pdf_reader.get_form_text_fields())

                # Extract section headers (simplified)
                for page in pdf_reader.pages:
                    text = page.extract_text()
                    # Look for common section patterns
                    lines = text.split('\n')
                    for line in lines:
                        if line.isupper() and len(line) > 3 and len(line) < 50:
                            structure["sections"].append(line.strip())

                    # Simple table detection (look for grid-like patterns)
                    if '|' in text or '\t' in text:
                        structure["tables_detected"] = True

        except Exception as e:
            print(f"Error extracting PDF structure: {e}")

        return structure

    def _generate_file_hash(self, file_path: str) -> str:
        """Generate hash for a file to detect duplicates"""
        hash_md5 = hashlib.md5()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_md5.update(chunk)
        return hash_md5.hexdigest()

    def add_training_pair(self,
                         pdf_path: str,
                         xf_schema: Dict[str, Any],
                         form_name: Optional[str] = None,
                         form_type: Optional[str] = None,
                         tags: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Add a PDF-to-XF schema pair to the training data

        Args:
            pdf_path: Path to the PDF file
            xf_schema: The corresponding XF schema for this PDF
            form_name: Optional name for the form
            form_type: Optional type/category (e.g., "inspection", "permit", "compliance")
            tags: Optional tags for categorization

        Returns:
            Training pair metadata
        """
        # Generate unique ID for this pair
        pdf_hash = self._generate_file_hash(pdf_path)
        pair_id = f"pair_{pdf_hash[:12]}_{datetime.now().strftime('%Y%m%d%H%M%S')}"

        # Extract PDF content and structure
        pdf_text = self._extract_pdf_text(pdf_path)
        pdf_structure = self._extract_pdf_structure(pdf_path)

        # Copy PDF to training data directory
        pdf_filename = f"{pair_id}.pdf"
        new_pdf_path = self.pdf_dir / pdf_filename
        with open(pdf_path, 'rb') as src, open(new_pdf_path, 'wb') as dst:
            dst.write(src.read())

        # Save schema
        schema_filename = f"{pair_id}_schema.json"
        schema_path = self.schema_dir / schema_filename
        with open(schema_path, 'w') as f:
            json.dump(xf_schema, f, indent=2)

        # Analyze the XF schema
        schema_analysis = self._analyze_xf_schema(xf_schema)

        # Create training pair entry
        pair_entry = {
            "id": pair_id,
            "pdf_file": pdf_filename,
            "schema_file": schema_filename,
            "form_name": form_name or os.path.basename(pdf_path),
            "form_type": form_type,
            "tags": tags or [],
            "pdf_hash": pdf_hash,
            "pdf_text_preview": pdf_text[:500],  # First 500 chars
            "pdf_structure": pdf_structure,
            "schema_analysis": schema_analysis,
            "added_date": datetime.now().isoformat()
        }

        # Check for duplicates
        existing = next((p for p in self.mappings["pairs"] if p["pdf_hash"] == pdf_hash), None)
        if existing:
            print(f"Warning: PDF with hash {pdf_hash} already exists in training data")
            return existing

        # Add to mappings
        self.mappings["pairs"].append(pair_entry)
        self._save_mappings()

        return pair_entry

    def _analyze_xf_schema(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze an XF schema to extract key characteristics"""
        analysis = {
            "total_fields": 0,
            "field_types": {},
            "pages": 0,
            "has_groups": False,
            "has_multivalue": False,
            "has_conditional": False,
            "has_required": False,
            "has_deficiencies": False,
            "field_names": []
        }

        def count_fields(node, depth=0):
            if isinstance(node, dict):
                name = node.get("name", "")
                props = node.get("props", {})

                # Count pages
                if name == "xf:page":
                    analysis["pages"] += 1

                # Count field types
                if name.startswith("xf:"):
                    field_type = name.replace("xf:", "")
                    if field_type not in ["form", "page"]:
                        analysis["total_fields"] += 1
                        analysis["field_types"][field_type] = analysis["field_types"].get(field_type, 0) + 1

                        # Record field name
                        field_name = props.get("xfName", "")
                        if field_name:
                            analysis["field_names"].append(field_name)

                # Check for special features
                if name == "xf:group":
                    analysis["has_groups"] = True
                if name == "xf:multivalue":
                    analysis["has_multivalue"] = True
                if name == "composite:deficiencies":
                    analysis["has_deficiencies"] = True

                if props.get("xfRequired"):
                    analysis["has_required"] = True
                if props.get("xfWhenEnabled"):
                    analysis["has_conditional"] = True

                # Recurse into children
                children = props.get("children", [])
                if isinstance(children, list):
                    for child in children:
                        count_fields(child, depth + 1)

        count_fields(schema)
        return analysis

    def prepare_training_data(self) -> List[Dict[str, Any]]:
        """
        Prepare training data in OpenAI fine-tuning format

        Returns:
            List of training examples in OpenAI format
        """
        training_examples = []

        for pair in self.mappings["pairs"]:
            # Load the schema
            schema_path = self.schema_dir / pair["schema_file"]
            with open(schema_path, 'r') as f:
                xf_schema = json.load(f)

            # Create system message with context
            system_message = """You are an expert at converting PDF forms into XF schemas.
You understand form structure, field types, and how to map PDF content to the appropriate XF schema elements.
Key rules:
1. Extract ALL fields from the PDF
2. Use appropriate xf:* types (string, text, date, boolean, ternary, select, etc.)
3. Organize fields into logical pages/sections
4. Include validation rules (xfRequired, xfFormat, etc.)
5. Add prepopulation hints where applicable
6. Use composite:deficiencies for deficiency tracking sections
7. Return ONLY valid JSON in the XF schema format"""

            # Create user message with PDF content and context
            user_message = f"""Convert this PDF form into an XF schema.

Form Type: {pair.get('form_type', 'general')}
Form Name: {pair.get('form_name', 'unknown')}
PDF Structure: {json.dumps(pair['pdf_structure'], indent=2)}

PDF Content (preview):
{pair['pdf_text_preview']}

Tags: {', '.join(pair.get('tags', []))}

Generate the complete XF schema for this form."""

            # Assistant response is the actual XF schema
            assistant_message = json.dumps(xf_schema, indent=2)

            # Create training example
            training_example = {
                "messages": [
                    {"role": "system", "content": system_message},
                    {"role": "user", "content": user_message},
                    {"role": "assistant", "content": assistant_message}
                ]
            }

            training_examples.append(training_example)

        return training_examples

    def export_for_training(self, output_file: str = "training_data.jsonl") -> str:
        """
        Export training data in JSONL format for OpenAI fine-tuning

        Args:
            output_file: Path to save the JSONL file

        Returns:
            Path to the exported file
        """
        training_data = self.prepare_training_data()

        output_path = self.data_dir / output_file
        with open(output_path, 'w') as f:
            for example in training_data:
                f.write(json.dumps(example) + '\n')

        print(f"Exported {len(training_data)} training examples to {output_path}")
        return str(output_path)

    def get_similar_forms(self, pdf_path: str, top_k: int = 3) -> List[Dict[str, Any]]:
        """
        Find similar forms in the training data based on structure

        Args:
            pdf_path: Path to the PDF to compare
            top_k: Number of similar forms to return

        Returns:
            List of similar training pairs
        """
        # Extract structure of the input PDF
        input_structure = self._extract_pdf_structure(pdf_path)
        input_text = self._extract_pdf_text(pdf_path)

        # Calculate similarity scores
        similarities = []
        for pair in self.mappings["pairs"]:
            score = 0

            # Compare structure
            if pair["pdf_structure"]["num_pages"] == input_structure["num_pages"]:
                score += 10
            if pair["pdf_structure"]["has_forms"] == input_structure["has_forms"]:
                score += 5
            if pair["pdf_structure"]["tables_detected"] == input_structure["tables_detected"]:
                score += 5

            # Compare sections (simplified string matching)
            input_sections = set(input_structure.get("sections", []))
            pair_sections = set(pair["pdf_structure"].get("sections", []))
            if input_sections and pair_sections:
                intersection = input_sections.intersection(pair_sections)
                score += len(intersection) * 2

            # Compare text similarity (very simplified)
            if pair["pdf_text_preview"] in input_text or input_text[:500] in pair["pdf_text_preview"]:
                score += 15

            similarities.append({
                "pair": pair,
                "score": score
            })

        # Sort by score and return top k
        similarities.sort(key=lambda x: x["score"], reverse=True)
        return [s["pair"] for s in similarities[:top_k]]

    def list_training_pairs(self) -> List[Dict[str, Any]]:
        """List all training pairs"""
        return self.mappings["pairs"]

    def remove_training_pair(self, pair_id: str) -> bool:
        """Remove a training pair by ID"""
        initial_count = len(self.mappings["pairs"])
        self.mappings["pairs"] = [p for p in self.mappings["pairs"] if p["id"] != pair_id]

        if len(self.mappings["pairs"]) < initial_count:
            self._save_mappings()

            # Also remove files
            for pair in self.mappings["pairs"]:
                if pair["id"] == pair_id:
                    pdf_path = self.pdf_dir / pair["pdf_file"]
                    schema_path = self.schema_dir / pair["schema_file"]
                    if pdf_path.exists():
                        pdf_path.unlink()
                    if schema_path.exists():
                        schema_path.unlink()
                    break

            return True
        return False

    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about the training data"""
        stats = {
            "total_pairs": len(self.mappings["pairs"]),
            "form_types": {},
            "field_type_distribution": {},
            "avg_fields_per_form": 0,
            "avg_pages_per_form": 0,
            "tags": {},
            "features": {
                "with_groups": 0,
                "with_multivalue": 0,
                "with_conditional": 0,
                "with_required": 0,
                "with_deficiencies": 0
            }
        }

        total_fields = 0
        total_pages = 0

        for pair in self.mappings["pairs"]:
            # Count form types
            form_type = pair.get("form_type", "uncategorized")
            stats["form_types"][form_type] = stats["form_types"].get(form_type, 0) + 1

            # Count tags
            for tag in pair.get("tags", []):
                stats["tags"][tag] = stats["tags"].get(tag, 0) + 1

            # Aggregate schema analysis
            analysis = pair.get("schema_analysis", {})
            total_fields += analysis.get("total_fields", 0)
            total_pages += analysis.get("pages", 0)

            # Count field types
            for field_type, count in analysis.get("field_types", {}).items():
                stats["field_type_distribution"][field_type] = stats["field_type_distribution"].get(field_type, 0) + count

            # Count features
            if analysis.get("has_groups"):
                stats["features"]["with_groups"] += 1
            if analysis.get("has_multivalue"):
                stats["features"]["with_multivalue"] += 1
            if analysis.get("has_conditional"):
                stats["features"]["with_conditional"] += 1
            if analysis.get("has_required"):
                stats["features"]["with_required"] += 1
            if analysis.get("has_deficiencies"):
                stats["features"]["with_deficiencies"] += 1

        # Calculate averages
        if stats["total_pairs"] > 0:
            stats["avg_fields_per_form"] = round(total_fields / stats["total_pairs"], 2)
            stats["avg_pages_per_form"] = round(total_pages / stats["total_pairs"], 2)

        return stats