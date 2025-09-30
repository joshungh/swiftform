"""
Enhanced BMP Inspection Report PDF Parser
Extracts ALL fields from PDF inspection forms to xf:* JSON format
"""
import re
import PyPDF2
from typing import Dict, List, Any, Optional, Tuple
import json

class EnhancedBMPParser:
    """Enhanced parser for complete BMP Inspection Report extraction"""

    def __init__(self):
        self.checkbox_pattern = r'[☐☑✓✗□■×X]\s*([^\n☐☑✓✗□■×]+)'
        self.field_pattern = r'([^:]+?):\s*([^\n]+)?'

    def parse_pdf_complete(self, pdf_path: str) -> Dict[str, Any]:
        """Extract complete form structure from PDF"""

        # Initialize form
        form_schema = {
            "name": "xf:form",
            "props": {
                "xfPageNavigation": "toc",
                "children": []
            }
        }

        # Extract all text from PDF
        full_text = self.extract_all_text(pdf_path)

        # Parse into sections
        sections = self.parse_sections(full_text)

        # Build pages from sections
        for section_name, section_data in sections.items():
            page = self.build_complete_page(section_name, section_data)
            if page and page["props"]["children"]:
                form_schema["props"]["children"].append(page)

        return form_schema

    def extract_all_text(self, pdf_path: str) -> str:
        """Extract all text from PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num, page in enumerate(pdf_reader.pages):
                    page_text = page.extract_text()
                    text += f"\n--- PAGE {page_num + 1} ---\n{page_text}"
        except Exception as e:
            print(f"Error extracting PDF: {e}")
        return text

    def parse_sections(self, text: str) -> Dict[str, Dict]:
        """Parse text into detailed sections"""
        sections = {
            "header": {"title": "Inspection Header", "content": []},
            "general_info": {"title": "General Information", "content": []},
            "site_info": {"title": "Site Information", "content": []},
            "weather": {"title": "Weather Information", "content": []},
            "inspector": {"title": "Inspector Information", "content": []},
            "bmps": {"title": "BMP Inspection", "content": []},
            "erosion_control": {"title": "Erosion Control", "content": []},
            "sediment_control": {"title": "Sediment Control", "content": []},
            "good_housekeeping": {"title": "Good Housekeeping", "content": []},
            "non_stormwater": {"title": "Non-Stormwater Management", "content": []},
            "corrective_actions": {"title": "Corrective Actions", "content": []},
            "notes": {"title": "Notes and Comments", "content": []}
        }

        lines = text.split('\n')
        current_section = "header"

        for line in lines:
            line = line.strip()
            if not line:
                continue

            # Detect section changes
            line_lower = line.lower()
            if "general information" in line_lower:
                current_section = "general_info"
            elif "site information" in line_lower:
                current_section = "site_info"
            elif "weather" in line_lower:
                current_section = "weather"
            elif "inspector" in line_lower:
                current_section = "inspector"
            elif "bmp" in line_lower and "inspection" in line_lower:
                current_section = "bmps"
            elif "erosion" in line_lower:
                current_section = "erosion_control"
            elif "sediment" in line_lower:
                current_section = "sediment_control"
            elif "housekeeping" in line_lower:
                current_section = "good_housekeeping"
            elif "non-stormwater" in line_lower or "non stormwater" in line_lower:
                current_section = "non_stormwater"
            elif "corrective" in line_lower:
                current_section = "corrective_actions"
            elif "notes" in line_lower or "comments" in line_lower:
                current_section = "notes"

            # Add line to current section
            if current_section in sections:
                sections[current_section]["content"].append(line)

        return sections

    def build_complete_page(self, section_key: str, section_data: Dict) -> Optional[Dict]:
        """Build complete xf:page with all fields"""

        page = {
            "name": "xf:page",
            "props": {
                "xfName": section_key,
                "xfLabel": section_data["title"],
                "children": []
            }
        }

        content = "\n".join(section_data["content"])

        # Extract fields based on section
        if section_key == "header":
            fields = self.extract_header_fields(content)
        elif section_key == "general_info":
            fields = self.extract_general_fields(content)
        elif section_key == "site_info":
            fields = self.extract_site_fields(content)
        elif section_key == "weather":
            fields = self.extract_weather_fields(content)
        elif section_key == "inspector":
            fields = self.extract_inspector_fields(content)
        elif section_key in ["bmps", "erosion_control", "sediment_control", "good_housekeeping"]:
            fields = self.extract_bmp_checklist(content, section_key)
        elif section_key == "non_stormwater":
            fields = self.extract_non_stormwater_fields(content)
        elif section_key == "corrective_actions":
            fields = self.extract_corrective_fields(content)
        else:
            fields = self.extract_generic_fields(content)

        page["props"]["children"] = fields
        return page if fields else None

    def extract_header_fields(self, content: str) -> List[Dict]:
        """Extract header fields including date, time, and inspection types"""
        fields = []

        # Date and Time
        date_match = re.search(r'Date.*?:\s*([0-9/]+)', content)
        if date_match:
            fields.append({
                "name": "xf:date",
                "props": {
                    "xfName": "inspection_date",
                    "xfLabel": "Inspection Date",
                    "xfDefaultValue": date_match.group(1),
                    "xfPrepopulateValueType": "date_today",
                    "xfPrepopulateValueEnabled": True
                }
            })

        time_match = re.search(r'Time.*?:\s*([0-9:]+\s*[AP]M)', content, re.IGNORECASE)
        if time_match:
            fields.append({
                "name": "xf:time",
                "props": {
                    "xfName": "inspection_time",
                    "xfLabel": "Inspection Time",
                    "xfDefaultValue": time_match.group(1),
                    "xfPrepopulateValueType": "time_today",
                    "xfPrepopulateValueEnabled": True
                }
            })

        # Inspection Types - extract all checkbox options
        inspection_types = [
            "Weekly",
            "Monthly (QSP/QSD)",
            "Pre-Qualifying Precipitation Event (QSP/QSD)",
            "During Qualifying Precipitation Event",
            "Post-Qualifying Precipitation Event",
            "Inactive Monthly (QSP/QSD)",
            "Final Inspection (QSP/QSD)",
            "Other (QSD/QSP) COI",
            "Other (QSD/QSP) - NAL Exceedance (w/in 14 days)",
            "Other (QSD/QSP) - As Requested by WB"
        ]

        fields.append({
            "name": "xf:select",
            "props": {
                "xfName": "inspection_type",
                "xfLabel": "Inspection Type",
                "xfOptions": "\n".join(inspection_types),
                "xfMultiple": True,
                "xfOutputClass": ["checkboxes-stacked"],
                "xfPrepopulateValueType": "select_last_report",
                "xfPrepopulateValueEnabled": True
            }
        })

        # QSD inspection types
        qsd_types = [
            "QSD Initial Inspection",
            "QSD Semi-Annual",
            "QSD Replacement (QSD)"
        ]

        fields.append({
            "name": "xf:select",
            "props": {
                "xfName": "qsd_inspection",
                "xfLabel": "QSD on-site visual inspection",
                "xfOptions": "\n".join(qsd_types),
                "xfMultiple": True,
                "xfPrepopulateValueType": "select_last_report",
                "xfPrepopulateValueEnabled": True
            }
        })

        return fields

    def extract_general_fields(self, content: str) -> List[Dict]:
        """Extract general information fields"""
        fields = []

        # Site Name
        site_match = re.search(r'Site Name.*?:\s*([^\n]+)', content)
        if site_match:
            fields.append({
                "name": "xf:string",
                "props": {
                    "xfName": "site_name",
                    "xfLabel": "Construction Site Name",
                    "xfDefaultValue": site_match.group(1).strip(),
                    "xfPrepopulateValueType": "location_name",
                    "xfPrepopulateValueEnabled": True
                }
            })

        # Construction Stage
        stages = [
            "Grading and Land Development",
            "Vertical Construction",
            "Inactive Construction Site",
            "Streets and Utilities",
            "Final Landscaping and Site Stabilization",
            "Demolition",
            "Other"
        ]

        fields.append({
            "name": "xf:select",
            "props": {
                "xfName": "construction_stage",
                "xfLabel": "Construction Stage",
                "xfOptions": "\n".join(stages),
                "xfPrepopulateValueType": "select_last_report",
                "xfPrepopulateValueEnabled": True
            }
        })

        # Activities completed
        fields.append({
            "name": "xf:text",
            "props": {
                "xfName": "activities_completed",
                "xfLabel": "General construction activities completed since the last inspection",
                "xfPrepopulateValueType": "last_report",
                "xfPrepopulateValueEnabled": True
            }
        })

        # Exposed area
        fields.append({
            "name": "xf:number",
            "props": {
                "xfName": "exposed_area_percent",
                "xfLabel": "Approximate Area of Site that is Exposed (%)"
            }
        })

        # Photos taken
        fields.append({
            "name": "xf:boolean",
            "props": {
                "xfName": "photos_taken",
                "xfLabel": "Photos Taken?",
                "xfPrepopulateValueType": "boolean_last_report",
                "xfPrepopulateValueEnabled": True
            }
        })

        return fields

    def extract_site_fields(self, content: str) -> List[Dict]:
        """Extract detailed site information"""
        fields = []

        # Extract any address information
        fields.append({
            "name": "xf:text",
            "props": {
                "xfName": "site_address",
                "xfLabel": "Site Address",
                "xfPrepopulateValueType": "location_address",
                "xfPrepopulateValueEnabled": True
            }
        })

        # WDID if present
        wdid_match = re.search(r'WDID.*?:\s*([^\n]+)', content)
        if wdid_match:
            fields.append({
                "name": "xf:string",
                "props": {
                    "xfName": "wdid",
                    "xfLabel": "WDID#",
                    "xfDefaultValue": wdid_match.group(1).strip(),
                    "xfPrepopulateValueType": "custom:program_location_type_data",
                    "xfPrepopulateCustomValue": "regulatory_identifier",
                    "xfPrepopulateValueEnabled": True
                }
            })

        return fields

    def extract_weather_fields(self, content: str) -> List[Dict]:
        """Extract comprehensive weather information"""
        fields = []

        # Storm beginning estimate
        storm_begin = re.search(r'Storm Beginning.*?:\s*([^\n]+)', content)
        if storm_begin:
            fields.append({
                "name": "xf:date",
                "props": {
                    "xfName": "storm_begin_date",
                    "xfLabel": "Estimate Storm Beginning",
                    "xfDefaultValue": storm_begin.group(1).strip()
                }
            })

        # Storm duration
        storm_duration = re.search(r'Storm Duration.*?:\s*([^\n]+)', content)
        if storm_duration:
            fields.append({
                "name": "xf:time",
                "props": {
                    "xfName": "storm_duration",
                    "xfLabel": "Estimate Storm Duration",
                    "xfDefaultValue": storm_duration.group(1).strip()
                }
            })

        # Time since last storm
        fields.append({
            "name": "xf:string",
            "props": {
                "xfName": "time_since_last_storm",
                "xfLabel": "Estimate time since last storm"
            }
        })

        # Rain gauge
        rain_gauge = re.search(r'Rain gauge.*?:\s*([^\n]+)', content)
        if rain_gauge:
            fields.append({
                "name": "xf:string",
                "props": {
                    "xfName": "rain_gauge_reading",
                    "xfLabel": "Rain gauge reading and location",
                    "xfDefaultValue": rain_gauge.group(1).strip()
                }
            })

        # Qualifying precipitation event
        fields.append({
            "name": "xf:boolean",
            "props": {
                "xfName": "qualifying_precipitation",
                "xfLabel": "Is a 'Qualifying Precipitation Event' predicted or did one occur?",
                "xfPrepopulateValueType": "boolean_last_report",
                "xfPrepopulateValueEnabled": True
            }
        })

        # Exception documentation
        fields.append({
            "name": "xf:boolean",
            "props": {
                "xfName": "using_exemption",
                "xfLabel": "Using Exemption?",
                "xfPrepopulateValueType": "boolean_last_report",
                "xfPrepopulateValueEnabled": True
            }
        })

        fields.append({
            "name": "xf:text",
            "props": {
                "xfName": "exception_documentation",
                "xfLabel": "Exception Documentation",
                "xfWhen": "using_exemption",
                "xfWhenEnabled": True
            }
        })

        return fields

    def extract_inspector_fields(self, content: str) -> List[Dict]:
        """Extract inspector information"""
        fields = []

        # Inspector name
        inspector_name = re.search(r'Inspector Name.*?:\s*([^\n]+)', content)
        if inspector_name:
            fields.append({
                "name": "xf:string",
                "props": {
                    "xfName": "inspector_name",
                    "xfLabel": "Inspector Name",
                    "xfDefaultValue": inspector_name.group(1).strip(),
                    "xfPrepopulateValueType": "user_name",
                    "xfPrepopulateValueEnabled": True
                }
            })

        # Inspector title
        inspector_title = re.search(r'Inspector Title.*?:\s*([^\n]+)', content)
        if inspector_title:
            fields.append({
                "name": "xf:string",
                "props": {
                    "xfName": "inspector_title",
                    "xfLabel": "Inspector Title",
                    "xfDefaultValue": inspector_title.group(1).strip(),
                    "xfPrepopulateValueType": "user_title",
                    "xfPrepopulateValueEnabled": True
                }
            })

        # Inspector certification
        fields.append({
            "name": "xf:string",
            "props": {
                "xfName": "inspector_certification",
                "xfLabel": "Inspector Certification"
            }
        })

        # Date
        fields.append({
            "name": "xf:date",
            "props": {
                "xfName": "inspector_date",
                "xfLabel": "Date",
                "xfPrepopulateValueType": "date_today",
                "xfPrepopulateValueEnabled": True
            }
        })

        # Signature
        fields.append({
            "name": "xf:signature",
            "props": {
                "xfName": "inspector_signature",
                "xfLabel": "Inspector Signature"
            }
        })

        return fields

    def extract_bmp_checklist(self, content: str, section_key: str) -> List[Dict]:
        """Extract BMP checklist items with ternary fields and comments"""
        fields = []

        # Find all items that look like checklist items
        lines = content.split('\n')

        for line in lines:
            # Look for numbered items (e.g., "1. Item description")
            numbered_match = re.match(r'^\d+\.\s+(.+?)(?:\s*[☐☑✓✗□■×]|$)', line)
            if numbered_match:
                item_text = numbered_match.group(1).strip()
                field_name = self.create_field_name(item_text)

                # Add ternary field for the BMP item
                fields.append({
                    "name": "xf:ternary",
                    "props": {
                        "xfName": field_name,
                        "xfLabel": item_text,
                        "xfPrepopulateValueType": "ternary_last_report",
                        "xfPrepopulateValueEnabled": True
                    }
                })

                # Add comment field
                fields.append({
                    "name": "xf:text",
                    "props": {
                        "xfName": f"{field_name}_comments",
                        "xfLabel": f"{item_text} - Comments/Corrective Actions",
                        "xfWhen": field_name,
                        "xfWhenEnabled": True,
                        "xfWhenContextValueType": "{{TYPE_FALSE}}"
                    }
                })

            # Also look for checkbox patterns
            checkbox_match = re.match(self.checkbox_pattern, line)
            if checkbox_match and not numbered_match:
                item_text = checkbox_match.group(1).strip()
                if len(item_text) > 3:  # Filter out too short items
                    field_name = self.create_field_name(item_text)

                    fields.append({
                        "name": "xf:boolean",
                        "props": {
                            "xfName": field_name,
                            "xfLabel": item_text,
                            "xfPrepopulateValueType": "boolean_last_report",
                            "xfPrepopulateValueEnabled": True
                        }
                    })

        return fields

    def extract_non_stormwater_fields(self, content: str) -> List[Dict]:
        """Extract non-stormwater management fields"""
        fields = []

        # Non-stormwater discharges observed
        fields.append({
            "name": "xf:boolean",
            "props": {
                "xfName": "non_stormwater_observed",
                "xfLabel": "Were non-stormwater discharges observed?",
                "xfPrepopulateValueType": "boolean_last_report",
                "xfPrepopulateValueEnabled": True
            }
        })

        # Types of non-stormwater discharges
        discharge_types = [
            "Potable Water",
            "Irrigation Drainage",
            "Air Conditioning Condensate",
            "Springs",
            "Uncontaminated Ground Water",
            "Other"
        ]

        fields.append({
            "name": "xf:select",
            "props": {
                "xfName": "discharge_types",
                "xfLabel": "Types of Non-Stormwater Discharges",
                "xfOptions": "\n".join(discharge_types),
                "xfMultiple": True,
                "xfWhen": "non_stormwater_observed",
                "xfWhenEnabled": True
            }
        })

        # Description
        fields.append({
            "name": "xf:text",
            "props": {
                "xfName": "non_stormwater_description",
                "xfLabel": "Description of Non-Stormwater Discharges",
                "xfWhen": "non_stormwater_observed",
                "xfWhenEnabled": True
            }
        })

        return fields

    def extract_corrective_fields(self, content: str) -> List[Dict]:
        """Extract corrective action fields"""
        fields = []

        # Corrective actions needed
        fields.append({
            "name": "xf:boolean",
            "props": {
                "xfName": "corrective_actions_needed",
                "xfLabel": "Are corrective actions needed?"
            }
        })

        # Create a repeating section for corrective actions
        fields.append({
            "name": "xf:group",
            "props": {
                "xfLabel": "Corrective Actions",
                "xfWhen": "corrective_actions_needed",
                "xfWhenEnabled": True,
                "children": [
                    {
                        "name": "xf:text",
                        "props": {
                            "xfName": "corrective_action_description",
                            "xfLabel": "Description of Corrective Action"
                        }
                    },
                    {
                        "name": "xf:select",
                        "props": {
                            "xfName": "corrective_action_priority",
                            "xfLabel": "Priority",
                            "xfOptions": "High\nMedium\nLow"
                        }
                    },
                    {
                        "name": "xf:date",
                        "props": {
                            "xfName": "corrective_action_due_date",
                            "xfLabel": "Due Date"
                        }
                    },
                    {
                        "name": "xf:string",
                        "props": {
                            "xfName": "responsible_party",
                            "xfLabel": "Responsible Party"
                        }
                    },
                    {
                        "name": "xf:boolean",
                        "props": {
                            "xfName": "action_completed",
                            "xfLabel": "Action Completed?"
                        }
                    },
                    {
                        "name": "xf:date",
                        "props": {
                            "xfName": "completion_date",
                            "xfLabel": "Completion Date",
                            "xfWhen": "action_completed",
                            "xfWhenEnabled": True
                        }
                    }
                ]
            }
        })

        return fields

    def extract_generic_fields(self, content: str) -> List[Dict]:
        """Extract any remaining fields using pattern matching"""
        fields = []
        seen_fields = set()

        lines = content.split('\n')
        for line in lines:
            # Look for field patterns
            field_match = re.match(self.field_pattern, line)
            if field_match:
                label = field_match.group(1).strip()
                value = field_match.group(2).strip() if field_match.group(2) else ""

                if label and len(label) < 50 and label not in seen_fields:
                    seen_fields.add(label)
                    field_name = self.create_field_name(label)
                    field_type = self.determine_field_type(label, value)

                    field = {
                        "name": field_type,
                        "props": {
                            "xfName": field_name,
                            "xfLabel": label
                        }
                    }

                    if value:
                        field["props"]["xfDefaultValue"] = value

                    fields.append(field)

        return fields

    def create_field_name(self, label: str) -> str:
        """Create valid xfName from label"""
        # Remove special characters and convert to snake_case
        name = re.sub(r'[^\w\s]', '', label)
        name = name.lower().strip()
        name = re.sub(r'\s+', '_', name)
        name = re.sub(r'_+', '_', name)
        return name[:50]  # Limit length

    def determine_field_type(self, label: str, value: str = "") -> str:
        """Determine appropriate field type based on label and value"""
        label_lower = label.lower()

        if any(word in label_lower for word in ['date', 'when']):
            return "xf:date"
        elif any(word in label_lower for word in ['time', 'duration']):
            return "xf:time"
        elif any(word in label_lower for word in ['yes', 'no', '?']):
            return "xf:boolean"
        elif any(word in label_lower for word in ['select', 'choose', 'type']):
            return "xf:select"
        elif any(word in label_lower for word in ['description', 'comments', 'notes', 'explain']):
            return "xf:text"
        elif any(word in label_lower for word in ['number', 'count', 'amount', 'percent', '%']):
            return "xf:number"
        elif any(word in label_lower for word in ['email']):
            return "xf:string"
        elif any(word in label_lower for word in ['signature', 'sign']):
            return "xf:signature"
        else:
            # Default based on length
            return "xf:text" if len(value) > 50 else "xf:string"