from typing import Dict, List, Any, Optional
from pydantic import BaseModel, Field, validator
from datetime import datetime
from enum import Enum

class FieldType(str, Enum):
    STRING = "xf:string"
    TEXT = "xf:text"
    NUMBER = "xf:number"
    DATE = "xf:date"
    TIME = "xf:time"
    BOOLEAN = "xf:boolean"
    SELECT = "xf:select"
    TERNARY = "xf:ternary"
    GROUP = "xf:group"
    PAGE = "xf:page"
    FORM = "xf:form"
    HIDDEN = "xf:hidden"
    FILE = "xf:file"
    SIGNATURE = "xf:signature"

class PrepopulateType(str, Enum):
    DATE_TODAY = "date_today"
    TIME_TODAY = "time_today"
    USER_NAME = "user_name"
    USER_EMAIL = "user_email"
    USER_PHONE = "user_phone"
    USER_TITLE = "user_title"
    LOCATION_NAME = "location_name"
    LOCATION_ADDRESS = "location_address"
    LOCATION_SITE_ID = "location_site_id"
    LAST_REPORT = "last_report"
    SELECT_LAST_REPORT = "select_last_report"
    BOOLEAN_LAST_REPORT = "boolean_last_report"
    CUSTOM = "custom"

class FormField(BaseModel):
    name: FieldType
    props: Dict[str, Any]

    @validator('props')
    def validate_props(cls, v, values):
        field_type = values.get('name')

        if not v.get('xfName') and field_type not in [FieldType.FORM, FieldType.PAGE]:
            raise ValueError('xfName is required for all fields except form and page')

        if field_type == FieldType.SELECT and 'xfOptions' not in v:
            v['xfOptions'] = "Option 1\nOption 2\nOption 3"

        return v

class FormPage(BaseModel):
    name: str = Field(default="xf:page")
    props: Dict[str, Any]

    @validator('props')
    def validate_page_props(cls, v):
        if 'xfName' not in v:
            raise ValueError('xfName is required for pages')
        if 'xfLabel' not in v:
            raise ValueError('xfLabel is required for pages')
        if 'children' not in v:
            v['children'] = []
        return v

class FormSchema(BaseModel):
    name: str = Field(default="xf:form")
    props: Dict[str, Any]

    @validator('props')
    def validate_form_props(cls, v):
        if 'children' not in v:
            v['children'] = []
        if 'xfPageNavigation' not in v:
            v['xfPageNavigation'] = 'toc'
        return v

    @classmethod
    def validate_schema(cls, schema: Dict[str, Any]) -> tuple[bool, List[str]]:
        """Validate a form schema and return errors if any"""
        errors = []

        if not schema.get('name'):
            errors.append("Missing 'name' field in schema")
        elif schema['name'] != 'xf:form':
            errors.append(f"Invalid root name: {schema['name']}, expected 'xf:form'")

        props = schema.get('props', {})
        if not props:
            errors.append("Missing 'props' field in schema")
            return False, errors

        children = props.get('children', [])
        if not children:
            errors.append("Form must have at least one page")

        for i, page in enumerate(children):
            page_errors = cls._validate_page(page, i)
            errors.extend(page_errors)

        return len(errors) == 0, errors

    @staticmethod
    def _validate_page(page: Dict[str, Any], page_index: int) -> List[str]:
        """Validate a single page"""
        errors = []

        if not page.get('name'):
            errors.append(f"Page {page_index}: Missing 'name' field")
        elif page['name'] != 'xf:page':
            errors.append(f"Page {page_index}: Invalid name '{page['name']}', expected 'xf:page'")

        props = page.get('props', {})
        if not props:
            errors.append(f"Page {page_index}: Missing 'props' field")
            return errors

        if not props.get('xfName'):
            errors.append(f"Page {page_index}: Missing 'xfName' property")

        if not props.get('xfLabel'):
            errors.append(f"Page {page_index}: Missing 'xfLabel' property")

        children = props.get('children', [])
        for j, field in enumerate(children):
            field_errors = FormSchema._validate_field(field, f"Page {page_index}, Field {j}")
            errors.extend(field_errors)

        return errors

    @staticmethod
    def _validate_field(field: Dict[str, Any], location: str) -> List[str]:
        """Validate a single field"""
        errors = []

        if not field.get('name'):
            errors.append(f"{location}: Missing 'name' field")
            return errors

        valid_types = [ft.value for ft in FieldType]
        if field['name'] not in valid_types:
            errors.append(f"{location}: Invalid field type '{field['name']}'")

        props = field.get('props', {})
        if not props:
            errors.append(f"{location}: Missing 'props' field")
            return errors

        if field['name'] == 'xf:group':
            if not props.get('xfLabel'):
                errors.append(f"{location}: Group missing 'xfLabel'")

            children = props.get('children', [])
            for k, child in enumerate(children):
                child_errors = FormSchema._validate_field(child, f"{location}, Child {k}")
                errors.extend(child_errors)

        elif field['name'] not in ['xf:form', 'xf:page']:
            if not props.get('xfName'):
                errors.append(f"{location}: Field missing 'xfName'")

            if not props.get('xfLabel') and field['name'] != 'xf:hidden':
                errors.append(f"{location}: Field missing 'xfLabel'")

            if field['name'] == 'xf:select' and not props.get('xfOptions'):
                errors.append(f"{location}: Select field missing 'xfOptions'")

        return errors

class FormSubmission(BaseModel):
    form_id: str
    submission_id: str
    data: Dict[str, Any]
    submitted_at: datetime
    user_id: Optional[str] = None
    status: str = "submitted"

class FormTemplate(BaseModel):
    template_id: str
    name: str
    description: Optional[str] = None
    category: Optional[str] = None
    schema: FormSchema
    created_at: datetime
    updated_at: datetime
    is_public: bool = False
    tags: List[str] = []

class ProcessingJob(BaseModel):
    job_id: str
    file_id: str
    status: str  # pending, processing, completed, failed
    ai_model: Optional[str] = None
    custom_instructions: Optional[str] = None
    result: Optional[Dict[str, Any]] = None
    error: Optional[str] = None
    created_at: datetime
    completed_at: Optional[datetime] = None
    processing_time: Optional[float] = None

class DocumentMetadata(BaseModel):
    file_id: str
    filename: str
    file_type: str
    file_size: int
    uploaded_at: datetime
    processed: bool = False
    metadata: Dict[str, Any] = {}

def create_default_form() -> Dict[str, Any]:
    """Create a default form schema"""
    return {
        "name": "xf:form",
        "props": {
            "xfPageNavigation": "toc",
            "children": [
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "general_info",
                        "xfLabel": "General Information",
                        "children": [
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "title",
                                    "xfLabel": "Title",
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
                                    "xfName": "description",
                                    "xfLabel": "Description"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }