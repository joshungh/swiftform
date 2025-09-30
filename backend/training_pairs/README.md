# PDF-to-XF Schema Training Pairs

This directory contains the training data for teaching OpenAI to convert your specific PDFs into XF schemas.

## 📁 Directory Structure

```
training_pairs/
├── pdfs/              # Your PDF files
├── schemas/           # Your XF JSON schemas (one per PDF)
├── mappings.json      # Auto-generated file linking PDFs to schemas
└── README.md          # This file
```

## 🔧 How to Add Your XF Schemas

### Step 1: Naming Convention
For each PDF in the `pdfs/` folder, create a corresponding JSON schema file in `schemas/` with the EXACT SAME NAME (just change the extension):

- PDF: `pdfs/CloudCompli Test - BMP Inspection Report - Custom 9-26-25.pdf`
- Schema: `schemas/CloudCompli Test - BMP Inspection Report - Custom 9-26-25.json`

### Step 2: Schema Format
Each schema file should contain a complete XF schema JSON object. Example:

```json
{
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
                "xfName": "permit_number",
                "xfLabel": "Permit Number",
                "xfRequired": true
              }
            }
          ]
        }
      }
    ]
  }
}
```

## 📝 Current PDFs Needing Schemas

Here are your PDFs and their expected schema filenames:

1. **DOTCEM-2075SW.pdf**
   → `schemas/DOTCEM-2075SW.json`

2. **Cloud Compli - Stormwater Inspection Report 8-22-25.pdf**
   → `schemas/Cloud Compli - Stormwater Inspection Report 8-22-25.json`

3. **20B-015 - Stormwater Inspection Report 8-19-25.pdf**
   → `schemas/20B-015 - Stormwater Inspection Report 8-19-25.json`

4. **1687 PENSACOLA ST - Rose Terrace - T-Mobile - BMP Inspection Report - Custom 9-18-25.pdf**
   → `schemas/1687 PENSACOLA ST - Rose Terrace - T-Mobile - BMP Inspection Report - Custom 9-18-25.json`

5. **Quarterly Site Inspection Report 9.5.pdf**
   → `schemas/Quarterly Site Inspection Report 9.5.json`

6. **Sniktaw SEC Water Sample - [Sniktaw] GDOT EROSION CONTROL Inspection 9-04-25.pdf**
   → `schemas/Sniktaw SEC Water Sample - [Sniktaw] GDOT EROSION CONTROL Inspection 9-04-25.json`

7. **Investigation_7838.pdf**
   → `schemas/Investigation_7838.json`

8. **Jacks Crab Shack - Land Use Report 8-15-25.pdf**
   → `schemas/Jacks Crab Shack - Land Use Report 8-15-25.json`

9. **Crawford Canyon Park Sidewalk Extension - BMP Inspection Report - Custom 9-19-25.pdf**
   → `schemas/Crawford Canyon Park Sidewalk Extension - BMP Inspection Report - Custom 9-19-25.json`

10. **CloudCompli Test - BMP Inspection Report - Custom 9-26-25.pdf**
    → `schemas/CloudCompli Test - BMP Inspection Report - Custom 9-26-25.json`

## ✅ How to Add Your Schemas

### Option 1: Direct Edit (Recommended)
1. Open each `.json` file in `schemas/`
2. Replace the content with your actual XF schema
3. Save the file

### Option 2: Copy Your Existing Schemas
If you have schemas elsewhere:
```bash
cp /path/to/your/schema.json "schemas/CloudCompli Test - BMP Inspection Report - Custom 9-26-25.json"
```

### Option 3: Create New Schema Files
```bash
# Create a new schema file
echo '{"name": "xf:form", "props": {...}}' > "schemas/YOUR_PDF_NAME.json"
```

## 🚀 Training the Model

Once all schemas are in place:

1. **Validate your pairs:**
   ```bash
   python validate_training_pairs.py
   ```

2. **Train the model:**
   ```bash
   python train_from_pairs.py
   ```

## 📋 Schema Checklist

Use this to track which schemas you've completed:

- [ ] DOTCEM-2075SW.json
- [ ] Cloud Compli - Stormwater Inspection Report 8-22-25.json
- [ ] 20B-015 - Stormwater Inspection Report 8-19-25.json
- [ ] 1687 PENSACOLA ST - Rose Terrace - T-Mobile - BMP Inspection Report - Custom 9-18-25.json
- [ ] Quarterly Site Inspection Report 9.5.json
- [ ] Sniktaw SEC Water Sample - [Sniktaw] GDOT EROSION CONTROL Inspection 9-04-25.json
- [ ] Investigation_7838.json
- [ ] Jacks Crab Shack - Land Use Report 8-15-25.json
- [ ] Crawford Canyon Park Sidewalk Extension - BMP Inspection Report - Custom 9-19-25.json
- [ ] CloudCompli Test - BMP Inspection Report - Custom 9-26-25.json

## 💡 Tips for Creating Good Schemas

1. **Be Consistent**: Use the same field naming patterns across similar forms
2. **Include All Fields**: Don't skip fields that appear in the PDF
3. **Use Correct Types**:
   - `xf:string` for short text
   - `xf:text` for long text/comments
   - `xf:date` for dates
   - `xf:boolean` for yes/no
   - `xf:ternary` for yes/no/NA
   - `xf:select` for dropdowns
4. **Add Validation**: Include `xfRequired`, `xfFormat`, etc. where needed
5. **Group Related Fields**: Use `xf:group` to organize related fields
6. **Use Deficiencies**: Add `composite:deficiencies` for inspection forms

## ❓ Need Help?

- Sample schemas are already in the `schemas/` folder as starting points
- Each schema can be edited to match your exact requirements
- The model will learn to produce exactly what you put in these schemas