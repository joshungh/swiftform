"""
BMP Inspection Report PDF Parser
Converts PDF inspection forms to xf:* JSON format
"""
import re
import PyPDF2
from typing import Dict, List, Any, Optional
import json

class BMPFormParser:
    """Parser specifically for BMP Inspection Report PDFs"""

    def __init__(self):
        self.form_sections = []
        self.current_page = None

    def parse_pdf_to_xf(self, pdf_path: str) -> Dict[str, Any]:
        """Main method to convert PDF to xf:* format"""

        # Initialize the form structure
        form_schema = {
            "name": "xf:form",
            "props": {
                "xfPageNavigation": "toc",
                "children": []
            }
        }

        # Extract text from PDF
        text_content = self.extract_pdf_text(pdf_path)

        # Parse sections from text
        sections = self.identify_sections(text_content)

        # Build form pages from sections
        for section_name, section_content in sections.items():
            page = self.build_page_from_section(section_name, section_content)
            if page:
                form_schema["props"]["children"].append(page)

        return form_schema

    def extract_pdf_text(self, pdf_path: str) -> str:
        """Extract all text from PDF"""
        text = ""
        try:
            with open(pdf_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page in pdf_reader.pages:
                    text += page.extract_text() + "\n"
        except Exception as e:
            print(f"Error extracting PDF text: {e}")
        return text

    def identify_sections(self, text: str) -> Dict[str, str]:
        """Identify major sections in the BMP inspection form"""
        sections = {}

        # Common sections in BMP inspection reports
        section_patterns = [
            (r"General Information", "general_info"),
            (r"Weather.*Information", "weather_info"),
            (r"Site.*Information|Site.*Details", "site_details"),
            (r"BMP.*Inspection|Inspection.*Checklist", "bmp_inspection"),
            (r"Erosion.*Control", "erosion_control"),
            (r"Sediment.*Control", "sediment_control"),
            (r"Good.*Housekeeping", "housekeeping"),
            (r"Non.*Stormwater", "non_stormwater"),
            (r"Corrective.*Action", "corrective_actions"),
            (r"Inspector.*Information", "inspector_info")
        ]

        lines = text.split('\n')
        current_section = "general_info"
        sections[current_section] = []

        for line in lines:
            # Check if this line starts a new section
            for pattern, section_key in section_patterns:
                if re.search(pattern, line, re.IGNORECASE):
                    current_section = section_key
                    if current_section not in sections:
                        sections[current_section] = []
                    break

            # Add line to current section
            if current_section in sections:
                sections[current_section].append(line)

        # Convert lists to strings
        return {k: '\n'.join(v) for k, v in sections.items()}

    def build_page_from_section(self, section_key: str, content: str) -> Optional[Dict]:
        """Build an xf:page from section content"""

        # Section name mapping
        section_names = {
            "general_info": "General Information",
            "weather_info": "Weather Information",
            "site_details": "Site Details",
            "bmp_inspection": "BMP Inspection",
            "erosion_control": "Erosion Control",
            "sediment_control": "Sediment Control",
            "housekeeping": "Good Housekeeping",
            "non_stormwater": "Non-Stormwater Discharges",
            "corrective_actions": "Corrective Actions",
            "inspector_info": "Inspector Information"
        }

        page = {
            "name": "xf:page",
            "props": {
                "xfName": section_key,
                "xfLabel": section_names.get(section_key, section_key.replace('_', ' ').title()),
                "children": []
            }
        }

        # Extract fields based on section type
        if section_key == "general_info":
            page["props"]["children"] = self.extract_general_info_fields(content)
        elif section_key == "weather_info":
            page["props"]["children"] = self.extract_weather_fields(content)
        elif section_key == "site_details":
            page["props"]["children"] = self.extract_site_fields(content)
        elif section_key == "inspector_info":
            page["props"]["children"] = self.extract_inspector_fields(content)
        elif section_key in ["bmp_inspection", "erosion_control", "sediment_control", "housekeeping"]:
            page["props"]["children"] = self.extract_checklist_fields(content, section_key)
        elif section_key == "corrective_actions":
            page["props"]["children"] = self.extract_corrective_action_fields(content)
        else:
            page["props"]["children"] = self.extract_generic_fields(content)

        return page if page["props"]["children"] else None

    def extract_general_info_fields(self, content: str) -> List[Dict]:
        """Extract fields from General Information section"""
        fields = []

        # Date field
        if re.search(r"date|Date|DATE", content, re.IGNORECASE):
            fields.append({
                "name": "xf:date",
                "props": {
                    "xfName": "inspection_date",
                    "xfLabel": "Inspection Date",
                    "xfPrepopulateValueType": "date_today",
                    "xfPrepopulateValueEnabled": True
                }
            })

        # Time field
        if re.search(r"time|Time|TIME", content, re.IGNORECASE):
            fields.append({
                "name": "xf:time",
                "props": {
                    "xfName": "inspection_time",
                    "xfLabel": "Inspection Time",
                    "xfPrepopulateValueType": "time_today",
                    "xfPrepopulateValueEnabled": True
                }
            })

        # WDID field
        if re.search(r"WDID|wdid", content):
            fields.append({
                "name": "xf:string",
                "props": {
                    "xfName": "wdid",
                    "xfLabel": "WDID#",
                    "xfPrepopulateValueType": "custom:program_location_type_data",
                    "xfPrepopulateCustomValue": "regulatory_identifier",
                    "xfPrepopulateValueEnabled": True
                }
            })

        # Inspection Type
        inspection_types = self.extract_options(content, "Inspection Type")
        if inspection_types:
            fields.append({
                "name": "xf:select",
                "props": {
                    "xfName": "inspection_type",
                    "xfLabel": "Inspection Type",
                    "xfOptions": "\n".join(inspection_types),
                    "xfMultiple": True,
                    "xfPrepopulateValueType": "select_last_report",
                    "xfPrepopulateValueEnabled": True
                }
            })

        # QSD field
        if re.search(r"QSD|qsd", content):
            fields.append({
                "name": "xf:select",
                "props": {
                    "xfName": "qsd",
                    "xfLabel": "QSD on-site visual inspection",
                    "xfOptions": "QSD Initial Inspection\nQSD Semi-Annual\nQSD Replacement (QSD)",
                    "xfMultiple": True,
                    "xfPrepopulateValueType": "select_last_report",
                    "xfPrepopulateValueEnabled": True
                }
            })

        return fields

    def extract_weather_fields(self, content: str) -> List[Dict]:
        """Extract weather-related fields"""
        fields = []

        # Weather condition
        fields.append({
            "name": "xf:select",
            "props": {
                "xfName": "weather_condition",
                "xfLabel": "Weather Condition",
                "xfOptions": "Clear\nCloudy\nRainy\nSnowy\nWindy",
                "xfPrepopulateValueType": "select_last_report",
                "xfPrepopulateValueEnabled": True
            }
        })

        # Temperature
        if re.search(r"temperature|temp", content, re.IGNORECASE):
            fields.append({
                "name": "xf:number",
                "props": {
                    "xfName": "temperature",
                    "xfLabel": "Temperature (°F)"
                }
            })

        # Precipitation
        if re.search(r"precipitation|rainfall", content, re.IGNORECASE):
            fields.append({
                "name": "xf:boolean",
                "props": {
                    "xfName": "precipitation_24hr",
                    "xfLabel": "Precipitation in last 24 hours?"
                }
            })

            fields.append({
                "name": "xf:number",
                "props": {
                    "xfName": "precipitation_amount",
                    "xfLabel": "Precipitation Amount (inches)",
                    "xfWhen": "precipitation_24hr",
                    "xfWhenEnabled": True
                }
            })

        return fields

    def extract_site_fields(self, content: str) -> List[Dict]:
        """Extract site detail fields"""
        fields = []

        # Project/Site Name
        fields.append({
            "name": "xf:string",
            "props": {
                "xfName": "project_name",
                "xfLabel": "Project Name",
                "xfPrepopulateValueType": "location_name",
                "xfPrepopulateValueEnabled": True
            }
        })

        # Site Address
        fields.append({
            "name": "xf:text",
            "props": {
                "xfName": "site_address",
                "xfLabel": "Site Address",
                "xfPrepopulateValueType": "location_address",
                "xfPrepopulateValueEnabled": True
            }
        })

        # Construction Stage
        if re.search(r"stage|phase", content, re.IGNORECASE):
            fields.append({
                "name": "xf:select",
                "props": {
                    "xfName": "construction_stage",
                    "xfLabel": "Construction Stage",
                    "xfOptions": "Pre-Construction\nClearing and Grading\nUtilities Installation\nVertical Construction\nFinal Stabilization",
                    "xfPrepopulateValueType": "select_last_report",
                    "xfPrepopulateValueEnabled": True
                }
            })

        # Disturbed Area
        if re.search(r"disturbed.*area|acres", content, re.IGNORECASE):
            fields.append({
                "name": "xf:number",
                "props": {
                    "xfName": "disturbed_area",
                    "xfLabel": "Disturbed Area (acres)"
                }
            })

        return fields

    def extract_inspector_fields(self, content: str) -> List[Dict]:
        """Extract inspector information fields"""
        fields = []

        fields.append({
            "name": "xf:string",
            "props": {
                "xfName": "inspector_name",
                "xfLabel": "Inspector Name",
                "xfPrepopulateValueType": "user_name",
                "xfPrepopulateValueEnabled": True
            }
        })

        fields.append({
            "name": "xf:string",
            "props": {
                "xfName": "inspector_title",
                "xfLabel": "Inspector Title",
                "xfPrepopulateValueType": "user_title",
                "xfPrepopulateValueEnabled": True
            }
        })

        fields.append({
            "name": "xf:string",
            "props": {
                "xfName": "inspector_phone",
                "xfLabel": "Inspector Phone",
                "xfPrepopulateValueType": "user_phone",
                "xfPrepopulateValueEnabled": True
            }
        })

        # Signature field
        fields.append({
            "name": "xf:signature",
            "props": {
                "xfName": "inspector_signature",
                "xfLabel": "Inspector Signature"
            }
        })

        return fields

    def extract_checklist_fields(self, content: str, section_key: str) -> List[Dict]:
        """Extract checklist items as ternary fields"""
        fields = []

        # Common BMP checklist items
        checklist_items = {
            "erosion_control": [
                ("Slope Protection", "slope_protection"),
                ("Fiber Rolls", "fiber_rolls"),
                ("Silt Fence", "silt_fence"),
                ("Erosion Control Blankets", "erosion_blankets"),
                ("Hydroseeding", "hydroseeding")
            ],
            "sediment_control": [
                ("Sediment Basin", "sediment_basin"),
                ("Sediment Trap", "sediment_trap"),
                ("Storm Drain Inlet Protection", "inlet_protection"),
                ("Track-out Control", "track_out_control"),
                ("Stabilized Construction Entrance", "construction_entrance")
            ],
            "housekeeping": [
                ("Material Storage", "material_storage"),
                ("Waste Management", "waste_management"),
                ("Spill Prevention", "spill_prevention"),
                ("Equipment Maintenance", "equipment_maintenance")
            ]
        }

        items = checklist_items.get(section_key, [])

        for label, field_name in items:
            # Check if item appears in content
            if re.search(label, content, re.IGNORECASE) or len(items) <= 5:
                fields.append({
                    "name": "xf:ternary",
                    "props": {
                        "xfName": field_name,
                        "xfLabel": label,
                        "xfPrepopulateValueType": "ternary_last_report",
                        "xfPrepopulateValueEnabled": True
                    }
                })

                # Add comment field for each item
                fields.append({
                    "name": "xf:text",
                    "props": {
                        "xfName": f"{field_name}_comments",
                        "xfLabel": f"{label} - Comments",
                        "xfWhen": field_name,
                        "xfWhenEnabled": True,
                        "xfWhenContextValueType": "{{TYPE_FALSE}}"
                    }
                })

        return fields

    def extract_corrective_action_fields(self, content: str) -> List[Dict]:
        """Extract corrective action fields"""
        fields = []

        fields.append({
            "name": "xf:boolean",
            "props": {
                "xfName": "corrective_actions_needed",
                "xfLabel": "Corrective Actions Needed?"
            }
        })

        fields.append({
            "name": "xf:text",
            "props": {
                "xfName": "corrective_action_description",
                "xfLabel": "Description of Corrective Actions",
                "xfWhen": "corrective_actions_needed",
                "xfWhenEnabled": True
            }
        })

        fields.append({
            "name": "xf:date",
            "props": {
                "xfName": "corrective_action_due_date",
                "xfLabel": "Due Date",
                "xfWhen": "corrective_actions_needed",
                "xfWhenEnabled": True
            }
        })

        fields.append({
            "name": "xf:string",
            "props": {
                "xfName": "responsible_party",
                "xfLabel": "Responsible Party",
                "xfWhen": "corrective_actions_needed",
                "xfWhenEnabled": True
            }
        })

        return fields

    def extract_generic_fields(self, content: str) -> List[Dict]:
        """Extract generic fields from content"""
        fields = []

        # Look for common patterns
        lines = content.split('\n')
        for line in lines:
            # Check for field patterns like "Field Name: _____"
            match = re.match(r'^([^:]+?):\s*[_\s]*$', line)
            if match:
                field_label = match.group(1).strip()
                field_name = field_label.lower().replace(' ', '_')

                # Determine field type based on label
                if any(word in field_label.lower() for word in ['date', 'when']):
                    field_type = "xf:date"
                elif any(word in field_label.lower() for word in ['time']):
                    field_type = "xf:time"
                elif any(word in field_label.lower() for word in ['yes', 'no']):
                    field_type = "xf:boolean"
                elif any(word in field_label.lower() for word in ['description', 'notes', 'comments']):
                    field_type = "xf:text"
                else:
                    field_type = "xf:string"

                fields.append({
                    "name": field_type,
                    "props": {
                        "xfName": field_name,
                        "xfLabel": field_label
                    }
                })

        return fields

    def extract_options(self, content: str, field_label: str) -> List[str]:
        """Extract options for select fields"""
        options = []

        # Look for checkbox patterns
        checkbox_pattern = r'[☐☑✓✗□■]\s*([^\n☐☑✓✗□■]+)'
        matches = re.findall(checkbox_pattern, content)

        if matches:
            options = [match.strip() for match in matches if len(match.strip()) > 2]

        # If no checkboxes found, look for common inspection types
        if not options and "inspection" in field_label.lower():
            options = [
                "Weekly",
                "Monthly",
                "Pre-Storm Event",
                "During Storm Event",
                "Post-Storm Event",
                "Inactive Monthly",
                "Final Inspection",
                "Other"
            ]

        return options