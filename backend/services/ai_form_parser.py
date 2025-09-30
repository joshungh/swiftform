"""
AI-Powered Form Parser using Claude or OpenAI
Extracts form fields from PDFs using AI for better accuracy
"""
import os
import json
import PyPDF2
from typing import Dict, List, Any, Optional
from datetime import datetime

class AIFormParser:
    """AI-powered parser for intelligent form extraction"""

    def __init__(self, provider: str = "claude", api_key: Optional[str] = None, model_name: Optional[str] = None):
        """
        Initialize AI parser

        Args:
            provider: "claude" or "openai"
            api_key: API key for the provider
            model_name: Specific model name to use (e.g., 'gpt-4', 'ft:gpt-3.5-turbo...')
        """
        self.provider = provider
        self.api_key = api_key or os.getenv(f"{provider.upper()}_API_KEY")
        self.model_name = model_name

        if provider == "claude":
            try:
                import anthropic
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except ImportError:
                raise ImportError("Please install anthropic: pip install anthropic")
        elif provider == "openai":
            try:
                import openai
                openai.api_key = self.api_key
                self.client = openai
            except ImportError:
                raise ImportError("Please install openai: pip install openai")
        else:
            raise ValueError(f"Unsupported provider: {provider}")

    def parse_pdf_with_ai(self, pdf_path: str) -> Dict[str, Any]:
        """Parse PDF using AI to extract form schema"""

        # Extract text from PDF
        text = self.extract_pdf_text(pdf_path)

        # Create prompt for AI
        prompt = self.create_extraction_prompt(text)

        # Get AI response
        if self.provider == "claude":
            form_schema = self.parse_with_claude(prompt)
        else:
            form_schema = self.parse_with_openai(prompt)

        return form_schema

    def extract_pdf_text(self, pdf_path: str) -> str:
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

    def create_extraction_prompt(self, text: str) -> str:
        """Create prompt for AI to extract form fields"""

        prompt = f"""You are a form extraction expert. Analyze this document and create a form schema in the xf:* JSON format.

DOCUMENT TEXT:
{text[:15000]}  # Limit to avoid token limits

INSTRUCTIONS:
1. Extract ALL fields, checkboxes, text areas, and data entry points from this document
2. Organize them into logical pages/sections
3. Use the correct xf:* element types:
   - xf:string for short text fields
   - xf:text for long text/comments
   - xf:date for date fields
   - xf:time for time fields
   - xf:boolean for yes/no questions
   - xf:ternary for yes/no/NA questions
   - xf:select for multiple choice (with xfOptions)
   - xf:number for numeric fields
   - xf:signature for signature fields
   - xf:hidden for hidden fields
   - xf:group for grouping related fields
   - xf:multivalue for repeating sections
   - composite:deficiencies for deficiency tracking

4. Add these attributes where appropriate:
   - xfRequired: true for required fields
   - xfPrepopulateValueType and xfPrepopulateValueEnabled for fields that can be prepopulated
   - xfWhen and xfWhenEnabled for conditional fields
   - xfDefaultValue for fields with default values
   - xfPresetOptionGroup: "bmp:all" for BMP-related deficiency fields
   - xfCorrectiveActionOptionGroup for corrective action categories

5. For deficiency fields, use this structure:
   {{
      "name": "composite:deficiencies",
      "props": {{
         "xfName": "deficiency",
         "xfWhen": "present",
         "xfToggleLabel": "Action Required?",
         "xfWhenEnabled": true,
         "xfDisableLevel": true,
         "xfCustomBtnLabel": "+ Deficiency",
         "xfDisableDateDue": true,
         "xfPresetOptionGroup": "bmp:all",
         "xfCustomLabelEnabled": true,
         "xfDisableDescription": true,
         "xfWhenContextControl": "q1",
         "xfDisableDateResolved": false,
         "xfDisablePhotoDateTime": true,
         "xfPrepopulateValueType": "current_deficiencies",
         "xfWhenContextValueType": "{{{{TYPE_FALSE}}}}",
         "xfDisableDateIdentified": false,
         "xfPrepopulateValueEnabled": true,
         "xfEnableCorrectiveActionList": true,
         "xfCorrectiveActionOptionGroup": "deficiencyCorrectiveActionCategory:XXX",
         "xfDeficiencyCorrectiveActionLabel": "Corrective Action"
      }}
   }}

6. Return ONLY valid JSON in this exact format:
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
                        // Field objects here
                    ]
                }}
            }}
        ]
    }}
}}

IMPORTANT:
- Extract EVERY field you can identify
- Preserve the exact field labels from the document
- Group related fields logically
- Use "bmp:all" for all xfPresetOptionGroup values in deficiency fields
- Return ONLY the JSON, no explanations
"""
        return prompt

    def parse_with_claude(self, prompt: str) -> Dict[str, Any]:
        """Use Claude API to parse the document"""
        try:
            response = self.client.messages.create(
                model="claude-3-sonnet-20240229",
                max_tokens=4000,
                temperature=0,
                messages=[{
                    "role": "user",
                    "content": prompt
                }]
            )

            # Extract JSON from response
            response_text = response.content[0].text

            # Try to parse JSON from response
            import re
            json_match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if json_match:
                return json.loads(json_match.group())
            else:
                # Return a default structure if parsing fails
                return self.get_fallback_schema()

        except Exception as e:
            print(f"Claude API error: {e}")
            return self.get_fallback_schema()

    def parse_with_openai(self, prompt: str) -> Dict[str, Any]:
        """Use OpenAI API to parse the document"""
        try:
            # Determine which model to use
            if self.model_name:
                model = self.model_name
            else:
                model = "gpt-4-turbo-preview"  # Default model

            if hasattr(self.client, 'ChatCompletion'):  # OpenAI v0.x
                response = self.client.ChatCompletion.create(
                    model=model,
                    messages=[{
                        "role": "system",
                        "content": "You are a form extraction expert. Return only valid JSON."
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                response_text = response.choices[0].message.content
            else:  # OpenAI v1.x
                from openai import OpenAI
                client = OpenAI(api_key=self.api_key)
                response = client.chat.completions.create(
                    model=model,
                    messages=[{
                        "role": "system",
                        "content": "You are a form extraction expert. Return only valid JSON."
                    }, {
                        "role": "user",
                        "content": prompt
                    }],
                    temperature=0,
                    response_format={"type": "json_object"}
                )
                response_text = response.choices[0].message.content

            return json.loads(response_text)

        except Exception as e:
            print(f"OpenAI API error: {e}")
            return self.get_fallback_schema()

    def get_fallback_schema(self) -> Dict[str, Any]:
        """Return a fallback schema if AI parsing fails"""
        return {
            "name": "xf:form",
            "props": {
                "xfPageNavigation": "toc",
                "children": [
                    {
                        "name": "xf:page",
                        "props": {
                            "xfName": "general",
                            "xfLabel": "General Information",
                            "children": [
                                {
                                    "name": "xf:string",
                                    "props": {
                                        "xfName": "document_name",
                                        "xfLabel": "Document Name",
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