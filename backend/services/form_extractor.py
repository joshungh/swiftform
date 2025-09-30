"""
Non-AI form extraction tools
"""
import PyPDF2
from pypdf import PdfReader
from pdfplumber import PDF
import json
from typing import Dict, List, Any
import re

class FormExtractor:
    """Extract form fields without AI"""

    def extract_pdf_acroform_fields(self, pdf_path: str) -> List[Dict]:
        """Extract native PDF form fields (AcroForm)"""
        fields = []

        try:
            reader = PdfReader(pdf_path)

            if reader.get_form_text_fields():
                for field_name, field_value in reader.get_form_text_fields().items():
                    fields.append({
                        "name": "xf:string",
                        "props": {
                            "xfName": self._sanitize_field_name(field_name),
                            "xfLabel": self._humanize_label(field_name),
                            "xfDefaultValue": field_value or ""
                        }
                    })

            # Get fields from AcroForm
            if '/AcroForm' in reader.trailer['/Root']:
                acroform = reader.trailer['/Root']['/AcroForm']
                if '/Fields' in acroform:
                    for field in reader.get_fields().values():
                        field_type = field.get('/FT')
                        field_name = field.get('/T')
                        field_value = field.get('/V')

                        xf_type = self._map_pdf_field_type(field_type)

                        fields.append({
                            "name": xf_type,
                            "props": {
                                "xfName": self._sanitize_field_name(field_name),
                                "xfLabel": self._humanize_label(field_name),
                                "xfDefaultValue": field_value or ""
                            }
                        })

        except Exception as e:
            print(f"Error extracting PDF fields: {e}")

        return fields

    def extract_from_table_structure(self, pdf_path: str) -> Dict:
        """Extract form structure from tables in PDF"""
        form_schema = {
            "name": "xf:form",
            "props": {
                "xfPageNavigation": "toc",
                "children": []
            }
        }

        try:
            with PDF.open(pdf_path) as pdf:
                for page_num, page in enumerate(pdf.pages, 1):
                    tables = page.extract_tables()

                    if tables:
                        page_schema = {
                            "name": "xf:page",
                            "props": {
                                "xfName": f"page_{page_num}",
                                "xfLabel": f"Page {page_num}",
                                "children": []
                            }
                        }

                        for table_idx, table in enumerate(tables):
                            # Analyze table structure
                            fields = self._analyze_table_for_fields(table)
                            page_schema["props"]["children"].extend(fields)

                        if page_schema["props"]["children"]:
                            form_schema["props"]["children"].append(page_schema)

        except Exception as e:
            print(f"Error extracting table structure: {e}")

        return form_schema

    def extract_using_templates(self, text: str, template_name: str = "inspection") -> Dict:
        """Use predefined templates to extract form fields"""

        templates = {
            "inspection": {
                "patterns": [
                    {"label": "Inspector Name", "pattern": r"Inspector(?:'s)?\s+Name\s*:?\s*([^\n]+)", "type": "xf:string"},
                    {"label": "Inspection Date", "pattern": r"(?:Inspection\s+)?Date\s*:?\s*([^\n]+)", "type": "xf:date"},
                    {"label": "Site Name", "pattern": r"Site\s+Name\s*:?\s*([^\n]+)", "type": "xf:string"},
                    {"label": "Site Address", "pattern": r"(?:Site\s+)?Address\s*:?\s*([^\n]+)", "type": "xf:text"},
                    {"label": "Weather Condition", "pattern": r"Weather\s*:?\s*([^\n]+)", "type": "xf:string"},
                    {"label": "Compliance Status", "pattern": r"Compliance\s*:?\s*([^\n]+)", "type": "xf:boolean"},
                ],
                "sections": [
                    "General Information",
                    "Site Details",
                    "Weather Information",
                    "Compliance"
                ]
            },
            "contact": {
                "patterns": [
                    {"label": "Full Name", "pattern": r"(?:Full\s+)?Name\s*:?\s*([^\n]+)", "type": "xf:string"},
                    {"label": "Email", "pattern": r"Email\s*:?\s*([^\n]+)", "type": "xf:string", "format": "email"},
                    {"label": "Phone", "pattern": r"Phone\s*:?\s*([^\n]+)", "type": "xf:string", "format": "phone"},
                    {"label": "Address", "pattern": r"Address\s*:?\s*([^\n]+)", "type": "xf:text"},
                ],
                "sections": [
                    "Contact Information"
                ]
            }
        }

        template = templates.get(template_name, templates["inspection"])

        # Build form from template
        form_schema = {
            "name": "xf:form",
            "props": {
                "xfPageNavigation": "toc",
                "children": []
            }
        }

        # Group fields by section
        for section in template["sections"]:
            page = {
                "name": "xf:page",
                "props": {
                    "xfName": self._sanitize_field_name(section),
                    "xfLabel": section,
                    "children": []
                }
            }

            # Add fields to section
            for field_def in template["patterns"]:
                field = {
                    "name": field_def["type"],
                    "props": {
                        "xfName": self._sanitize_field_name(field_def["label"]),
                        "xfLabel": field_def["label"]
                    }
                }

                if "format" in field_def:
                    field["props"]["xfFormat"] = field_def["format"]

                # Try to find value in text
                match = re.search(field_def["pattern"], text, re.IGNORECASE)
                if match:
                    field["props"]["xfDefaultValue"] = match.group(1).strip()

                page["props"]["children"].append(field)

            form_schema["props"]["children"].append(page)

        return form_schema

    def extract_using_keywords(self, text: str) -> Dict:
        """Extract fields based on keyword detection"""

        # Keywords that indicate form fields
        field_keywords = {
            "date_fields": ["date", "dated", "when", "time", "schedule"],
            "name_fields": ["name", "inspector", "supervisor", "contact", "person"],
            "location_fields": ["address", "location", "site", "place", "where"],
            "boolean_fields": ["yes/no", "y/n", "true/false", "compliance", "completed", "approved"],
            "select_fields": ["choose", "select", "option", "type", "category", "status"],
            "number_fields": ["amount", "quantity", "number", "count", "total", "#"],
            "text_fields": ["description", "notes", "comments", "remarks", "details"]
        }

        form_schema = {
            "name": "xf:form",
            "props": {
                "xfPageNavigation": "toc",
                "children": [{
                    "name": "xf:page",
                    "props": {
                        "xfName": "main",
                        "xfLabel": "Form Fields",
                        "children": []
                    }
                }]
            }
        }

        lines = text.split('\n')
        fields = []

        for line in lines:
            line_lower = line.lower()

            # Check each keyword category
            for field_type, keywords in field_keywords.items():
                for keyword in keywords:
                    if keyword in line_lower:
                        # Extract label from line
                        label = line.split(':')[0].strip() if ':' in line else line.strip()

                        if label and len(label) < 50:  # Reasonable label length
                            xf_type = self._get_xf_type_from_keyword(field_type)

                            field = {
                                "name": xf_type,
                                "props": {
                                    "xfName": self._sanitize_field_name(label),
                                    "xfLabel": label
                                }
                            }

                            # Add specific props based on type
                            if "date" in field_type:
                                field["props"]["xfPrepopulateValueType"] = "date_today"
                            elif "name" in field_type and "inspector" in line_lower:
                                field["props"]["xfPrepopulateValueType"] = "user_name"

                            fields.append(field)
                            break

        # Remove duplicates
        seen = set()
        unique_fields = []
        for field in fields:
            field_key = field["props"]["xfName"]
            if field_key not in seen:
                seen.add(field_key)
                unique_fields.append(field)

        form_schema["props"]["children"][0]["props"]["children"] = unique_fields

        return form_schema

    def _analyze_table_for_fields(self, table: List[List]) -> List[Dict]:
        """Analyze table structure to extract form fields"""
        fields = []

        if not table or len(table) < 2:
            return fields

        # Check if first row looks like headers
        headers = table[0]

        for header in headers:
            if header and isinstance(header, str):
                # Skip if it looks like data rather than a header
                if any(char.isdigit() for char in header) and len(header) > 10:
                    continue

                field = {
                    "name": "xf:string",
                    "props": {
                        "xfName": self._sanitize_field_name(header),
                        "xfLabel": header.strip()
                    }
                }
                fields.append(field)

        return fields

    def _map_pdf_field_type(self, pdf_type: str) -> str:
        """Map PDF field types to xf types"""
        mapping = {
            '/Tx': 'xf:string',  # Text field
            '/Btn': 'xf:boolean',  # Button/Checkbox
            '/Ch': 'xf:select',  # Choice/Dropdown
            '/Sig': 'xf:signature'  # Signature
        }
        return mapping.get(pdf_type, 'xf:string')

    def _get_xf_type_from_keyword(self, field_type: str) -> str:
        """Map keyword categories to xf field types"""
        mapping = {
            "date_fields": "xf:date",
            "name_fields": "xf:string",
            "location_fields": "xf:text",
            "boolean_fields": "xf:boolean",
            "select_fields": "xf:select",
            "number_fields": "xf:number",
            "text_fields": "xf:text"
        }
        return mapping.get(field_type, "xf:string")

    def _sanitize_field_name(self, name: str) -> str:
        """Convert field name to valid xfName format"""
        if not name:
            return "field"

        # Convert to lowercase and replace spaces with underscores
        name = name.lower().strip()
        name = re.sub(r'[^\w\s]', '', name)  # Remove special characters
        name = re.sub(r'\s+', '_', name)  # Replace spaces with underscores
        name = re.sub(r'_+', '_', name)  # Remove multiple underscores

        return name or "field"

    def _humanize_label(self, name: str) -> str:
        """Convert field name to human-readable label"""
        if not name:
            return "Field"

        # Replace underscores with spaces and capitalize
        label = name.replace('_', ' ').replace('-', ' ')
        label = ' '.join(word.capitalize() for word in label.split())

        return label