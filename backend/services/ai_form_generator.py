import os
import json
from typing import Dict, List, Any, Optional
from datetime import datetime
import openai
import anthropic
from dotenv import load_dotenv

load_dotenv()

class AIFormGenerator:
    """Service for generating form schemas using AI"""

    def __init__(self):
        self.openai_api_key = os.getenv("OPENAI_API_KEY")
        self.anthropic_api_key = os.getenv("ANTHROPIC_API_KEY")

        if self.openai_api_key:
            openai.api_key = self.openai_api_key

        if self.anthropic_api_key:
            self.anthropic_client = anthropic.Anthropic(api_key=self.anthropic_api_key)

    async def generate_form(
        self,
        document_content: Dict[str, Any],
        ai_model: str = "gpt-4",
        custom_instructions: Optional[str] = None
    ) -> Dict[str, Any]:
        """Generate form schema from parsed document content"""

        structured_content = self._prepare_content_for_ai(document_content)

        prompt = self._build_prompt(structured_content, custom_instructions)

        if ai_model.startswith("gpt"):
            return await self._generate_with_openai(prompt, ai_model)
        elif ai_model.startswith("claude"):
            return await self._generate_with_anthropic(prompt, ai_model)
        else:
            return self._generate_with_rules(structured_content)

    def _prepare_content_for_ai(self, document_content: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare document content for AI processing"""
        prepared = {
            "document_type": document_content.get("type"),
            "sections": [],
            "fields": [],
            "tables": [],
            "structure": []
        }

        if document_content["type"] == "pdf":
            for page in document_content.get("pages", []):
                prepared["fields"].extend(page.get("form_fields", []))
                for table in page.get("tables", []):
                    prepared["tables"].append({
                        "headers": table.get("headers", []),
                        "row_count": len(table.get("data", [])),
                        "sample_data": table.get("data", [])[:3]
                    })

                text = page.get("text", "")
                if text:
                    prepared["sections"].append({
                        "page": page.get("page_number"),
                        "text_preview": text[:500]
                    })

        elif document_content["type"] == "word":
            prepared["fields"] = document_content.get("form_fields", [])
            prepared["sections"] = [
                {"title": h["text"], "level": h["level"]}
                for h in document_content.get("headers", [])
            ]
            prepared["tables"] = [
                {"headers": t.get("headers", []), "row_count": len(t.get("data", []))}
                for t in document_content.get("tables", [])
            ]

        elif document_content["type"] == "excel":
            for sheet in document_content.get("sheets", []):
                prepared["fields"].extend(sheet.get("form_fields", []))
                prepared["tables"].append({
                    "sheet": sheet["name"],
                    "headers": sheet.get("headers", []),
                    "row_count": len(sheet.get("data", []))
                })

        return prepared

    def _build_prompt(self, content: Dict[str, Any], custom_instructions: Optional[str]) -> str:
        """Build AI prompt for form generation"""
        prompt = f"""You are an expert at analyzing documents and generating form schemas in the xf:* format.

Document Content:
{json.dumps(content, indent=2)[:3000]}

Your task is to generate a complete form schema in the following JSON format:

{{
  "name": "xf:form",
  "props": {{
    "xfPageNavigation": "toc",
    "children": [
      {{
        "name": "xf:page",
        "props": {{
          "xfName": "page_name",
          "xfLabel": "Page Label",
          "children": [
            // Form fields here
          ]
        }}
      }}
    ]
  }}
}}

Field types to use:
- xf:string - Single line text
- xf:text - Multi-line text
- xf:number - Numeric input
- xf:date - Date picker
- xf:time - Time picker
- xf:boolean - Yes/No checkbox
- xf:select - Dropdown/select with options
- xf:ternary - Yes/No/N/A
- xf:group - Group container for related fields
- xf:hidden - Hidden field

Each field should have these properties:
- xfName: unique field identifier (snake_case)
- xfLabel: Display label
- xfRequired: true/false (optional)
- xfDefaultValue: default value (optional)
- xfOptions: for select fields (newline separated)
- xfWhen: conditional display based on other field (optional)
- xfPrepopulateValueType: prepopulation type (optional)

Analyze the document and create appropriate:
1. Pages/sections based on document structure
2. Groups for related fields
3. Appropriate field types based on content
4. Meaningful labels and names
5. Logical field ordering

"""

        if custom_instructions:
            prompt += f"\nAdditional Instructions:\n{custom_instructions}\n"

        prompt += "\nGenerate only valid JSON output, no explanations:"

        return prompt

    async def _generate_with_openai(self, prompt: str, model: str = "gpt-4") -> Dict[str, Any]:
        """Generate form using OpenAI GPT models"""
        try:
            response = openai.ChatCompletion.create(
                model=model,
                messages=[
                    {"role": "system", "content": "You are a form schema generator. Output only valid JSON."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                max_tokens=4000
            )

            content = response.choices[0].message.content
            return json.loads(content)

        except json.JSONDecodeError:
            return self._get_fallback_schema()
        except Exception as e:
            print(f"OpenAI generation failed: {e}")
            return self._get_fallback_schema()

    async def _generate_with_anthropic(self, prompt: str, model: str = "claude-3-opus-20240229") -> Dict[str, Any]:
        """Generate form using Anthropic Claude models"""
        try:
            message = self.anthropic_client.messages.create(
                model=model,
                max_tokens=4000,
                temperature=0.3,
                system="You are a form schema generator. Output only valid JSON.",
                messages=[
                    {"role": "user", "content": prompt}
                ]
            )

            content = message.content[0].text
            return json.loads(content)

        except json.JSONDecodeError:
            return self._get_fallback_schema()
        except Exception as e:
            print(f"Anthropic generation failed: {e}")
            return self._get_fallback_schema()

    def _generate_with_rules(self, content: Dict[str, Any]) -> Dict[str, Any]:
        """Generate form using rule-based approach (fallback)"""
        form_schema = {
            "name": "xf:form",
            "props": {
                "xfPageNavigation": "toc",
                "children": []
            }
        }

        pages_by_section = {}

        for field in content.get("fields", []):
            section_name = self._determine_section(field)

            if section_name not in pages_by_section:
                page = {
                    "name": "xf:page",
                    "props": {
                        "xfName": section_name.lower().replace(" ", "_"),
                        "xfLabel": section_name,
                        "children": []
                    }
                }
                pages_by_section[section_name] = page
                form_schema["props"]["children"].append(page)

            field_schema = self._convert_field_to_schema(field)
            if field_schema:
                pages_by_section[section_name]["props"]["children"].append(field_schema)

        for table in content.get("tables", []):
            if table.get("headers"):
                table_fields = self._convert_table_to_fields(table)
                if table_fields and pages_by_section:
                    first_page = list(pages_by_section.values())[0]
                    first_page["props"]["children"].extend(table_fields)

        if not form_schema["props"]["children"]:
            form_schema["props"]["children"].append({
                "name": "xf:page",
                "props": {
                    "xfName": "main",
                    "xfLabel": "Form",
                    "children": []
                }
            })

        return form_schema

    def _determine_section(self, field: Dict[str, Any]) -> str:
        """Determine which section a field belongs to"""
        label = field.get("label", "").lower()

        if any(word in label for word in ["personal", "contact", "name", "email", "phone"]):
            return "Personal Information"
        elif any(word in label for word in ["date", "time", "schedule", "appointment"]):
            return "Schedule Information"
        elif any(word in label for word in ["address", "location", "site", "place"]):
            return "Location Details"
        elif any(word in label for word in ["comment", "note", "description", "detail"]):
            return "Additional Information"
        else:
            return "General Information"

    def _convert_field_to_schema(self, field: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Convert extracted field to xf:* schema format"""
        field_type = field.get("type", "text_field")
        label = field.get("label", "").strip()

        if not label:
            return None

        field_name = label.lower().replace(" ", "_").replace(":", "")
        field_name = ''.join(c if c.isalnum() or c == '_' else '' for c in field_name)

        type_mapping = {
            "date": "xf:date",
            "time": "xf:time",
            "email": "xf:string",
            "phone": "xf:string",
            "name": "xf:string",
            "address": "xf:text",
            "checkbox": "xf:boolean",
            "radio": "xf:select",
            "select": "xf:select",
            "number": "xf:number",
            "text_field": "xf:string",
            "label_field": "xf:string"
        }

        xf_type = type_mapping.get(field_type, "xf:string")

        schema = {
            "name": xf_type,
            "props": {
                "xfName": field_name,
                "xfLabel": label
            }
        }

        if field_type == "email":
            schema["props"]["xfFormat"] = "email"
        elif field_type == "phone":
            schema["props"]["xfFormat"] = "phone"

        if field_type in ["radio", "select"]:
            schema["props"]["xfOptions"] = "Option 1\nOption 2\nOption 3"

        return schema

    def _convert_table_to_fields(self, table: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Convert table to form fields"""
        fields = []
        headers = table.get("headers", [])

        if not headers:
            return fields

        group = {
            "name": "xf:group",
            "props": {
                "xfLabel": table.get("name", "Table Data"),
                "children": []
            }
        }

        for header in headers[:10]:
            if header and isinstance(header, str):
                field_name = header.lower().replace(" ", "_")
                field_name = ''.join(c if c.isalnum() or c == '_' else '' for c in field_name)

                field = {
                    "name": "xf:string",
                    "props": {
                        "xfName": field_name,
                        "xfLabel": header
                    }
                }
                group["props"]["children"].append(field)

        if group["props"]["children"]:
            fields.append(group)

        return fields

    def _get_fallback_schema(self) -> Dict[str, Any]:
        """Return a basic fallback schema"""
        return {
            "name": "xf:form",
            "props": {
                "xfPageNavigation": "toc",
                "children": [
                    {
                        "name": "xf:page",
                        "props": {
                            "xfName": "general_information",
                            "xfLabel": "General Information",
                            "children": [
                                {
                                    "name": "xf:string",
                                    "props": {
                                        "xfName": "form_title",
                                        "xfLabel": "Form Title",
                                        "xfRequired": True
                                    }
                                },
                                {
                                    "name": "xf:date",
                                    "props": {
                                        "xfName": "date",
                                        "xfLabel": "Date",
                                        "xfPrepopulateValueType": "date_today",
                                        "xfPrepopulateValueEnabled": True
                                    }
                                },
                                {
                                    "name": "xf:text",
                                    "props": {
                                        "xfName": "notes",
                                        "xfLabel": "Notes"
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

    def enhance_with_ai_suggestions(self, schema: Dict[str, Any]) -> Dict[str, Any]:
        """Enhance generated schema with AI suggestions"""
        for page in schema.get("props", {}).get("children", []):
            if page.get("name") == "xf:page":
                for field in page.get("props", {}).get("children", []):
                    self._add_field_enhancements(field)

        return schema

    def _add_field_enhancements(self, field: Dict[str, Any]) -> None:
        """Add enhancements to individual fields"""
        if not field.get("props"):
            return

        field_name = field["props"].get("xfName", "")
        field_label = field["props"].get("xfLabel", "")

        if "date" in field_name.lower():
            field["props"]["xfPrepopulateValueType"] = "date_today"
            field["props"]["xfPrepopulateValueEnabled"] = True

        if "time" in field_name.lower():
            field["props"]["xfPrepopulateValueType"] = "time_today"
            field["props"]["xfPrepopulateValueEnabled"] = True

        if any(word in field_name.lower() for word in ["name", "email", "phone"]):
            field["props"]["xfRequired"] = True

        if "email" in field_name.lower():
            field["props"]["xfFormat"] = "email"
            field["props"]["xfFormatEnabled"] = True

        if "phone" in field_name.lower() or "tel" in field_name.lower():
            field["props"]["xfFormat"] = "phone"
            field["props"]["xfFormatEnabled"] = True