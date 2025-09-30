#!/usr/bin/env python3
"""
Tool to set up PDF-to-XF Schema training pairs
This helps you create the exact XF schemas for each PDF and pair them properly
"""

import os
import json
import shutil
from pathlib import Path
from datetime import datetime


def create_sample_xf_schemas():
    """Create sample XF schemas based on PDF names"""

    schemas = {}

    # DOTCEM-2075SW.pdf - Environmental compliance form
    schemas["DOTCEM-2075SW"] = {
        "name": "xf:form",
        "props": {
            "xfPageNavigation": "toc",
            "children": [
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "project_info",
                        "xfLabel": "Project Information",
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
                                "name": "xf:string",
                                "props": {
                                    "xfName": "permit_number",
                                    "xfLabel": "NPDES Permit Number",
                                    "xfRequired": True
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
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "site_conditions",
                        "xfLabel": "Site Conditions",
                        "children": [
                            {
                                "name": "xf:select",
                                "props": {
                                    "xfName": "weather_conditions",
                                    "xfLabel": "Weather Conditions",
                                    "xfOptions": "Clear\nCloudy\nRain\nSnow\nWindy"
                                }
                            },
                            {
                                "name": "xf:boolean",
                                "props": {
                                    "xfName": "discharge_occurring",
                                    "xfLabel": "Is discharge occurring from site?"
                                }
                            },
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "site_description",
                                    "xfLabel": "Site Description"
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "bmps",
                        "xfLabel": "BMP Assessment",
                        "children": [
                            {
                                "name": "xf:ternary",
                                "props": {
                                    "xfName": "perimeter_controls",
                                    "xfLabel": "Perimeter Controls"
                                }
                            },
                            {
                                "name": "xf:ternary",
                                "props": {
                                    "xfName": "sediment_controls",
                                    "xfLabel": "Sediment Controls"
                                }
                            },
                            {
                                "name": "xf:ternary",
                                "props": {
                                    "xfName": "erosion_controls",
                                    "xfLabel": "Erosion Controls"
                                }
                            },
                            {
                                "name": "composite:deficiencies",
                                "props": {
                                    "xfName": "deficiencies",
                                    "xfToggleLabel": "Deficiencies Found?",
                                    "xfWhenEnabled": True,
                                    "xfPresetOptionGroup": "bmp:all"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    # Stormwater Inspection Reports
    stormwater_schema = {
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
                                    "xfName": "facility_name",
                                    "xfLabel": "Facility Name",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "permit_id",
                                    "xfLabel": "Permit ID",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:date",
                                "props": {
                                    "xfName": "inspection_date",
                                    "xfLabel": "Date of Inspection",
                                    "xfPrepopulateValueType": "date_today",
                                    "xfPrepopulateValueEnabled": True
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "inspector",
                                    "xfLabel": "Inspector Name",
                                    "xfPrepopulateValueType": "user_name",
                                    "xfPrepopulateValueEnabled": True
                                }
                            },
                            {
                                "name": "xf:time",
                                "props": {
                                    "xfName": "inspection_time",
                                    "xfLabel": "Time of Inspection"
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "weather",
                        "xfLabel": "Weather & Site Conditions",
                        "children": [
                            {
                                "name": "xf:select",
                                "props": {
                                    "xfName": "weather",
                                    "xfLabel": "Current Weather",
                                    "xfOptions": "Clear\nPartly Cloudy\nCloudy\nRain - Light\nRain - Heavy\nSnow"
                                }
                            },
                            {
                                "name": "xf:number",
                                "props": {
                                    "xfName": "temp",
                                    "xfLabel": "Temperature (°F)"
                                }
                            },
                            {
                                "name": "xf:boolean",
                                "props": {
                                    "xfName": "recent_rain",
                                    "xfLabel": "Rain in last 48 hours?"
                                }
                            },
                            {
                                "name": "xf:number",
                                "props": {
                                    "xfName": "rainfall_amount",
                                    "xfLabel": "Rainfall Amount (inches)",
                                    "xfWhen": "recent_rain",
                                    "xfWhenEnabled": True
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "control_measures",
                        "xfLabel": "Control Measures",
                        "children": [
                            {
                                "name": "xf:group",
                                "props": {
                                    "xfLabel": "Erosion & Sediment Controls",
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
                                                "xfName": "sediment_trap",
                                                "xfLabel": "Sediment Trap/Basin"
                                            }
                                        },
                                        {
                                            "name": "xf:ternary",
                                            "props": {
                                                "xfName": "inlet_protection",
                                                "xfLabel": "Inlet Protection"
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
                                    "xfLabel": "Good Housekeeping",
                                    "children": [
                                        {
                                            "name": "xf:ternary",
                                            "props": {
                                                "xfName": "material_storage",
                                                "xfLabel": "Material Storage Areas"
                                            }
                                        },
                                        {
                                            "name": "xf:ternary",
                                            "props": {
                                                "xfName": "waste_containers",
                                                "xfLabel": "Waste Containers"
                                            }
                                        },
                                        {
                                            "name": "xf:ternary",
                                            "props": {
                                                "xfName": "vehicle_fueling",
                                                "xfLabel": "Vehicle Fueling Areas"
                                            }
                                        }
                                    ]
                                }
                            },
                            {
                                "name": "composite:deficiencies",
                                "props": {
                                    "xfName": "deficiencies",
                                    "xfToggleLabel": "Deficiencies Identified?",
                                    "xfWhenEnabled": True,
                                    "xfPresetOptionGroup": "bmp:all",
                                    "xfCorrectiveActionOptionGroup": "deficiencyCorrectiveActionCategory:stormwater"
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "certification",
                        "xfLabel": "Certification",
                        "children": [
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "comments",
                                    "xfLabel": "Additional Comments"
                                }
                            },
                            {
                                "name": "xf:signature",
                                "props": {
                                    "xfName": "inspector_signature",
                                    "xfLabel": "Inspector Signature",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:date",
                                "props": {
                                    "xfName": "signature_date",
                                    "xfLabel": "Date",
                                    "xfPrepopulateValueType": "date_today",
                                    "xfPrepopulateValueEnabled": True
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    # Apply stormwater schema to all stormwater inspection reports
    schemas["Cloud Compli - Stormwater Inspection Report 8-22-25"] = stormwater_schema
    schemas["20B-015 - Stormwater Inspection Report 8-19-25"] = stormwater_schema

    # BMP Inspection Reports
    bmp_schema = {
        "name": "xf:form",
        "props": {
            "xfPageNavigation": "toc",
            "children": [
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "site_info",
                        "xfLabel": "Site Information",
                        "children": [
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "site_name",
                                    "xfLabel": "Site Name",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "location",
                                    "xfLabel": "Location/Address",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "project_number",
                                    "xfLabel": "Project Number"
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
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "bmp_checklist",
                        "xfLabel": "BMP Inspection Checklist",
                        "children": [
                            {
                                "name": "xf:multivalue",
                                "props": {
                                    "xfName": "bmps",
                                    "xfLabel": "Best Management Practices",
                                    "xfMin": 1,
                                    "children": [
                                        {
                                            "name": "xf:group",
                                            "props": {
                                                "children": [
                                                    {
                                                        "name": "xf:string",
                                                        "props": {
                                                            "xfName": "bmp_type",
                                                            "xfLabel": "BMP Type"
                                                        }
                                                    },
                                                    {
                                                        "name": "xf:string",
                                                        "props": {
                                                            "xfName": "bmp_location",
                                                            "xfLabel": "Location"
                                                        }
                                                    },
                                                    {
                                                        "name": "xf:select",
                                                        "props": {
                                                            "xfName": "condition",
                                                            "xfLabel": "Condition",
                                                            "xfOptions": "Good\nFair\nPoor\nNeeds Maintenance\nNeeds Replacement"
                                                        }
                                                    },
                                                    {
                                                        "name": "xf:boolean",
                                                        "props": {
                                                            "xfName": "functioning",
                                                            "xfLabel": "Functioning Properly?"
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
                            },
                            {
                                "name": "composite:deficiencies",
                                "props": {
                                    "xfName": "deficiencies",
                                    "xfToggleLabel": "Deficiencies Observed?",
                                    "xfWhenEnabled": True,
                                    "xfPresetOptionGroup": "bmp:all",
                                    "xfDeficiencyCorrectiveActionLabel": "Required Corrective Action"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    # Apply BMP schema to BMP inspection reports
    schemas["1687 PENSACOLA ST - Rose Terrace - T-Mobile - BMP Inspection Report - Custom 9-18-25"] = bmp_schema
    schemas["Crawford Canyon Park Sidewalk Extension - BMP Inspection Report - Custom 9-19-25"] = bmp_schema
    schemas["CloudCompli Test - BMP Inspection Report - Custom 9-26-25"] = bmp_schema

    # Other inspection reports
    schemas["Quarterly Site Inspection Report 9.5"] = stormwater_schema
    schemas["Sniktaw SEC Water Sample - [Sniktaw] GDOT EROSION CONTROL Inspection 9-04-25"] = stormwater_schema

    # Investigation report
    schemas["Investigation_7838"] = {
        "name": "xf:form",
        "props": {
            "xfPageNavigation": "toc",
            "children": [
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "investigation_details",
                        "xfLabel": "Investigation Details",
                        "children": [
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "investigation_id",
                                    "xfLabel": "Investigation ID",
                                    "xfDefaultValue": "7838",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:date",
                                "props": {
                                    "xfName": "investigation_date",
                                    "xfLabel": "Investigation Date"
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "investigator",
                                    "xfLabel": "Investigator Name"
                                }
                            },
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "description",
                                    "xfLabel": "Investigation Description"
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "findings",
                        "xfLabel": "Findings",
                        "children": [
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "findings_summary",
                                    "xfLabel": "Summary of Findings"
                                }
                            },
                            {
                                "name": "xf:select",
                                "props": {
                                    "xfName": "severity",
                                    "xfLabel": "Severity Level",
                                    "xfOptions": "Low\nMedium\nHigh\nCritical"
                                }
                            },
                            {
                                "name": "xf:boolean",
                                "props": {
                                    "xfName": "violation_found",
                                    "xfLabel": "Violation Found?"
                                }
                            },
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "recommendations",
                                    "xfLabel": "Recommendations"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    # Land Use Report
    schemas["Jacks Crab Shack - Land Use Report 8-15-25"] = {
        "name": "xf:form",
        "props": {
            "xfPageNavigation": "toc",
            "children": [
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "property_info",
                        "xfLabel": "Property Information",
                        "children": [
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "property_name",
                                    "xfLabel": "Property Name",
                                    "xfDefaultValue": "Jacks Crab Shack",
                                    "xfRequired": True
                                }
                            },
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "property_address",
                                    "xfLabel": "Property Address"
                                }
                            },
                            {
                                "name": "xf:string",
                                "props": {
                                    "xfName": "parcel_number",
                                    "xfLabel": "Parcel Number"
                                }
                            },
                            {
                                "name": "xf:select",
                                "props": {
                                    "xfName": "zoning",
                                    "xfLabel": "Zoning Classification",
                                    "xfOptions": "Residential\nCommercial\nIndustrial\nMixed Use\nAgricultural"
                                }
                            }
                        ]
                    }
                },
                {
                    "name": "xf:page",
                    "props": {
                        "xfName": "land_use",
                        "xfLabel": "Land Use Assessment",
                        "children": [
                            {
                                "name": "xf:select",
                                "props": {
                                    "xfName": "current_use",
                                    "xfLabel": "Current Land Use",
                                    "xfOptions": "Restaurant\nRetail\nOffice\nWarehouse\nVacant\nOther"
                                }
                            },
                            {
                                "name": "xf:boolean",
                                "props": {
                                    "xfName": "conforming_use",
                                    "xfLabel": "Conforming Use?"
                                }
                            },
                            {
                                "name": "xf:number",
                                "props": {
                                    "xfName": "lot_size",
                                    "xfLabel": "Lot Size (sq ft)"
                                }
                            },
                            {
                                "name": "xf:number",
                                "props": {
                                    "xfName": "building_size",
                                    "xfLabel": "Building Size (sq ft)"
                                }
                            },
                            {
                                "name": "xf:text",
                                "props": {
                                    "xfName": "compliance_notes",
                                    "xfLabel": "Compliance Notes"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    return schemas


def main():
    """Main function to set up training pairs"""

    print("=== Setting up PDF-to-XF Schema Training Pairs ===\n")

    # Get list of PDFs
    pdf_dir = Path("example-forms")
    pdfs = list(pdf_dir.glob("*.pdf"))

    print(f"Found {len(pdfs)} PDFs in example-forms/\n")

    # Create training_pairs directory structure
    training_dir = Path("training_pairs")
    training_dir.mkdir(exist_ok=True)
    (training_dir / "pdfs").mkdir(exist_ok=True)
    (training_dir / "schemas").mkdir(exist_ok=True)

    # Generate sample schemas
    print("Generating XF schemas for your PDFs...")
    schemas = create_sample_xf_schemas()

    # Create mapping file
    mappings = []

    for pdf_path in pdfs:
        pdf_name = pdf_path.stem

        # Copy PDF to training_pairs/pdfs/
        shutil.copy(pdf_path, training_dir / "pdfs" / pdf_path.name)

        # Find or create schema
        if pdf_name in schemas:
            schema = schemas[pdf_name]
            schema_filename = f"{pdf_name}.json"

            # Save schema to training_pairs/schemas/
            schema_path = training_dir / "schemas" / schema_filename
            with open(schema_path, 'w') as f:
                json.dump(schema, f, indent=2)

            # Add to mappings
            mappings.append({
                "pdf": pdf_path.name,
                "schema": schema_filename,
                "name": pdf_name,
                "created": datetime.now().isoformat()
            })

            print(f"✓ Created pair: {pdf_path.name} -> {schema_filename}")
        else:
            print(f"⚠️ No schema found for: {pdf_path.name}")

    # Save mappings
    mappings_file = training_dir / "mappings.json"
    with open(mappings_file, 'w') as f:
        json.dump({
            "pairs": mappings,
            "created": datetime.now().isoformat(),
            "total": len(mappings)
        }, f, indent=2)

    print(f"\n✓ Created {len(mappings)} PDF-XF schema pairs")
    print(f"✓ Saved to: training_pairs/\n")

    print("Directory structure:")
    print("  training_pairs/")
    print("    ├── pdfs/          # Your PDF files")
    print("    ├── schemas/       # Corresponding XF schemas")
    print("    └── mappings.json  # Maps PDFs to schemas")

    print("\n" + "="*50)
    print("IMPORTANT: Manual Review Required!")
    print("="*50)
    print("\nThe generated XF schemas are EXAMPLES based on common patterns.")
    print("You should:")
    print("1. Review each schema in training_pairs/schemas/")
    print("2. Modify them to match EXACTLY what you want for each PDF")
    print("3. Add/remove fields as needed")
    print("4. Ensure field names, types, and validations are correct")
    print("\nOnce you've reviewed and corrected the schemas, run:")
    print("  python train_from_pairs.py")
    print("\nThis will train OpenAI to learn YOUR specific PDF-to-XF mappings.")


if __name__ == "__main__":
    main()