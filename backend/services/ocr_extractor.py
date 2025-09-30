"""
OCR-based form extraction (requires tesseract)
"""
import pytesseract
from PIL import Image
import cv2
import numpy as np
from typing import Dict, List
import re

class OCRFormExtractor:
    """Extract forms using OCR and computer vision"""

    def extract_form_from_image(self, image_path: str) -> Dict:
        """Extract form fields from scanned documents"""

        # Use pytesseract to extract text
        text = pytesseract.image_to_string(image_path)

        # Use layout analysis
        data = pytesseract.image_to_data(image_path, output_type=pytesseract.Output.DICT)

        form_fields = self._detect_form_fields_from_layout(data)

        return self._build_form_schema(form_fields)

    def detect_checkboxes(self, image_path: str) -> List[Dict]:
        """Detect checkboxes in forms using computer vision"""
        img = cv2.imread(image_path, 0)

        # Apply threshold
        _, thresh = cv2.threshold(img, 127, 255, cv2.THRESH_BINARY_INV)

        # Find contours
        contours, _ = cv2.findContours(thresh, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

        checkboxes = []
        for contour in contours:
            x, y, w, h = cv2.boundingRect(contour)

            # Check if contour is square-ish (likely a checkbox)
            aspect_ratio = float(w) / h
            if 0.8 <= aspect_ratio <= 1.2 and 10 <= w <= 50:
                checkboxes.append({
                    "type": "checkbox",
                    "position": (x, y),
                    "size": (w, h)
                })

        return checkboxes

    def _detect_form_fields_from_layout(self, ocr_data: Dict) -> List[Dict]:
        """Detect form fields based on OCR layout analysis"""
        fields = []

        n_boxes = len(ocr_data['text'])
        for i in range(n_boxes):
            text = ocr_data['text'][i].strip()
            if text:
                # Look for patterns that indicate form fields
                if ':' in text or text.endswith('?'):
                    fields.append({
                        "label": text.replace(':', '').replace('?', ''),
                        "type": self._guess_field_type(text),
                        "position": {
                            "x": ocr_data['left'][i],
                            "y": ocr_data['top'][i],
                            "width": ocr_data['width'][i],
                            "height": ocr_data['height'][i]
                        }
                    })

        return fields

    def _guess_field_type(self, text: str) -> str:
        """Guess field type based on text"""
        text_lower = text.lower()

        if any(word in text_lower for word in ['date', 'when']):
            return 'xf:date'
        elif any(word in text_lower for word in ['yes', 'no', 'y/n']):
            return 'xf:boolean'
        elif any(word in text_lower for word in ['email']):
            return 'xf:string'
        elif any(word in text_lower for word in ['address', 'description', 'notes']):
            return 'xf:text'
        else:
            return 'xf:string'

    def _build_form_schema(self, fields: List[Dict]) -> Dict:
        """Build xf schema from detected fields"""
        form_schema = {
            "name": "xf:form",
            "props": {
                "xfPageNavigation": "toc",
                "children": [{
                    "name": "xf:page",
                    "props": {
                        "xfName": "extracted_form",
                        "xfLabel": "Extracted Form",
                        "children": []
                    }
                }]
            }
        }

        for field in fields:
            xf_field = {
                "name": field["type"],
                "props": {
                    "xfName": field["label"].lower().replace(' ', '_'),
                    "xfLabel": field["label"]
                }
            }
            form_schema["props"]["children"][0]["props"]["children"].append(xf_field)

        return form_schema