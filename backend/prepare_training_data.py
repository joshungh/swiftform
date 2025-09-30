#!/usr/bin/env python3
"""
Script to prepare training data by pairing PDFs with their XF schemas
Run this to create proper training pairs for OpenAI fine-tuning
"""

import os
import json
from pathlib import Path
from services.training_data_manager import TrainingDataManager
from services.bmp_parser import BMPFormParser
from services.enhanced_bmp_parser import EnhancedBMPParser


def load_existing_schemas():
    """Load any existing XF schemas you have"""
    schemas_dir = Path("existing_schemas")
    schemas = {}

    if schemas_dir.exists():
        for schema_file in schemas_dir.glob("*.json"):
            with open(schema_file, 'r') as f:
                # Use filename (without extension) as key
                schemas[schema_file.stem] = json.load(f)

    return schemas


def generate_schema_for_pdf(pdf_path: str) -> dict:
    """Generate XF schema for a PDF using existing parsers"""
    try:
        # Try enhanced parser first
        parser = EnhancedBMPParser()
        schema = parser.parse_pdf_complete(pdf_path)

        if not schema.get("props", {}).get("children"):
            # Fallback to basic parser
            parser = BMPFormParser()
            schema = parser.parse_pdf_to_xf(pdf_path)

        return schema
    except Exception as e:
        print(f"Error generating schema for {pdf_path}: {e}")
        return None


def create_sample_schemas():
    """Create sample XF schemas for common form types"""

    # Sample inspection form schema
    inspection_schema = {
        "name": "xf:form",
        "props": {
            "xfPageNavigation": "toc",
            "children": [
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "site_information",
                        "xfLabel": "Site Information",
                        "children": [
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "permit_number",
                                    "xfLabel": "Permit Number",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "site_name",
                                    "xfLabel": "Site/Facility Name",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "site_address",
                                    "xfLabel": "Site Address"
                                }
                            },
                            {
                                "name": "xf:date",
                                "props": {
                                    "xfName": "inspection_date",
                                    "xfLabel": "Inspection Date",
                                    "xfPrepopulateValueType": "date_today",
                                    "xfPrepopulateValueEnabled": True
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "inspector_name",
                                    "xfLabel": "Inspector Name",
                                    "xfPrepopulateValueType": "user_name",
                                    "xfPrepopulateValueEnabled": True
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "bmp_inspection",
                        "xfLabel": "BMP Inspection",
                        "children": [
                            {
                                "name": "xf:group",
                                "props": {
                                    "xfLabel": "Erosion Control",
                                    "children": [
                                        {
                                            "name": "xf:ternary",
                                            "props": {
                                                "xfName": "silt_fence",
                                                "xfLabel": "Silt Fence"
                                            }
                                        },
                                        {
                                            "name": "xf:ternary",
                                            "props": {
                                                "xfName": "erosion_blankets",
                                                "xfLabel": "Erosion Control Blankets"
                                            }
                                        },
                                        {
                                            "name": "xf:ternary",
                                            "props": {
                                                "xfName": "check_dams",
                                                "xfLabel": "Check Dams"
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "name": "xf:group",
                                "props": {
                                    "xfLabel": "Sediment Control",
                                    "children": [
                                        {
                                            "name": "xf:ternary",
                                            "props": {
                                                "xfName": "sediment_basin",
                                                "xfLabel": "Sediment Basin"
                                            }
                                        },
                                        {
                                            "name": "xf:ternary",
                                            "props": {
                                                "xfName": "inlet_protection",
                                                "xfLabel": "Storm Drain Inlet Protection"
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "name": "composite:deficiencies",
                                "props": {
                                    "xfName": "deficiencies",
                                    "xfWhen": "present",
                                    "xfToggleLabel": "Deficiencies Found?",
                                    "xfWhenEnabled": True,
                                    "xfPresetOptionGroup": "bmp:all",
                                    "xfCorrectiveActionOptionGroup": "deficiencyCorrectiveActionCategory:bmp",
                                    "xfDeficiencyCorrectiveActionLabel": "Corrective Action Required"
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "comments",
                        "xfLabel": "Comments & Sign-off",
                        "children": [
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "inspection_notes",
                                    "xfLabel": "Inspection Notes"
                                }
                            },
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "corrective_actions",
                                    "xfLabel": "Required Corrective Actions"
                                }
                            },
                            {
                                "name": "xf:signature",
                                "props": {
                                    "xfName": "inspector_signature",
                                    "xfLabel": "Inspector Signature",
                                    "xfRequired": True
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    # Sample permit application schema
    permit_schema = {
        "name": "xf:form",
        "props": {
            "xfPageNavigation": "toc",
            "children": [
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "applicant_info",
                        "xfLabel": "Applicant Information",
                        "children": [
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "company_name",
                                    "xfLabel": "Company Name",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "contact_name",
                                    "xfLabel": "Contact Name",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "phone",
                                    "xfLabel": "Phone Number",
                                    "xfFormat": "phone"
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "email",
                                    "xfLabel": "Email Address",
                                    "xfFormat": "email",
                                    "xfRequired": True
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "project_details",
                        "xfLabel": "Project Details",
                        "children": [
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "project_name",
                                    "xfLabel": "Project Name",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "project_description",
                                    "xfLabel": "Project Description",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:select",
                                "props": {
                                    "xfName": "project_type",
                                    "xfLabel": "Project Type",
                                    "xfOptions": "New Construction\nRenovation\nDemolition\nLand Development\nOther"
                                }
                            },
                            {
                                "name": "xf:number",
                                "props": {
                                    "xfName": "disturbed_area",
                                    "xfLabel": "Total Disturbed Area (acres)",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:date",
                                "props": {
                                    "xfName": "start_date",
                                    "xfLabel": "Estimated Start Date"
                                }
                            },
                            {
                                "name": "xf:date",
                                "props": {
                                    "xfName": "end_date",
                                    "xfLabel": "Estimated End Date"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    return {
        "inspection_form": inspection_schema,
        "permit_application": permit_schema
    }


def main():
    """Main function to prepare training data"""

    # Initialize training data manager
    manager = TrainingDataManager()

    print("=== PDF-to-XF Schema Training Data Preparation ===\n")

    # Check for existing PDFs in example-forms directory
    pdf_dir = Path("example-forms")
    if not pdf_dir.exists():
        print(f"Creating {pdf_dir} directory...")
        pdf_dir.mkdir(exist_ok=True)

    pdf_files = list(pdf_dir.glob("*.pdf"))
    print(f"Found {len(pdf_files)} PDF files in {pdf_dir}\n")

    # Load existing schemas if available
    existing_schemas = load_existing_schemas()
    if existing_schemas:
        print(f"Found {len(existing_schemas)} existing XF schemas\n")

    # Create sample schemas for demonstration
    sample_schemas = create_sample_schemas()

    # Process each PDF
    for pdf_path in pdf_files:
        pdf_name = pdf_path.stem
        print(f"Processing: {pdf_path.name}")

        # Try to find matching schema
        schema = None
        form_type = None
        tags = []

        # Check if we have an existing schema for this PDF
        if pdf_name in existing_schemas:
            schema = existing_schemas[pdf_name]
            print(f"  - Found existing schema for {pdf_name}")

        # Otherwise, try to determine form type and use appropriate sample schema
        elif "inspection" in pdf_name.lower() or "swppp" in pdf_name.lower():
            schema = sample_schemas["inspection_form"]
            form_type = "inspection"
            tags = ["BMP", "compliance", "environmental"]
            print(f"  - Using inspection form schema template")

        elif "permit" in pdf_name.lower() or "application" in pdf_name.lower():
            schema = sample_schemas["permit_application"]
            form_type = "permit"
            tags = ["permit", "application"]
            print(f"  - Using permit application schema template")

        else:
            # Generate schema using parser
            print(f"  - Generating schema using parser...")
            schema = generate_schema_for_pdf(str(pdf_path))
            form_type = "general"
            tags = ["auto-generated"]

        if schema:
            # Add the training pair
            try:
                pair = manager.add_training_pair(
                    pdf_path=str(pdf_path),
                    xf_schema=schema,
                    form_name=pdf_name,
                    form_type=form_type,
                    tags=tags
                )
                print(f"  ✓ Added training pair: {pair['id']}")
                print(f"    - Fields: {pair['schema_analysis']['total_fields']}")
                print(f"    - Pages: {pair['schema_analysis']['pages']}")
            except Exception as e:
                print(f"  ✗ Error adding training pair: {e}")
        else:
            print(f"  ✗ Could not generate schema for {pdf_path.name}")

        print()

    # Export training data for OpenAI
    print("Exporting training data for OpenAI fine-tuning...")
    output_file = manager.export_for_training()
    print(f"✓ Training data exported to: {output_file}\n")

    # Show statistics
    stats = manager.get_statistics()
    print("=== Training Data Statistics ===")
    print(f"Total training pairs: {stats['total_pairs']}")
    print(f"Average fields per form: {stats['avg_fields_per_form']}")
    print(f"Average pages per form: {stats['avg_pages_per_form']}")

    if stats['form_types']:
        print("\nForm types:")
        for form_type, count in stats['form_types'].items():
            print(f"  - {form_type}: {count}")

    if stats['field_type_distribution']:
        print("\nField type distribution:")
        for field_type, count in sorted(stats['field_type_distribution'].items(), key=lambda x: x[1], reverse=True)[:10]:
            print(f"  - {field_type}: {count}")

    print("\n✓ Training data preparation complete!")
    print("\nNext steps:")
    print("1. Review the generated training pairs in 'training_data/mappings.json'")
    print("2. Manually create or adjust XF schemas for better accuracy")
    print("3. Run the training script to create a new fine-tuned model")
    print("4. Use: python train_with_paired_data.py")


if __name__ == "__main__":
    main()