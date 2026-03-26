import os
import json
import uuid

notebooks_to_convert = [
    ("bronze_to_silver.py", "Bronze_to_Silver"),
    ("silver_to_gold.py", "Silver_to_Gold"),
    ("build_semantic_model.py", "Build_Semantic_Model")
]

base_dir = "notebooks"

lakehouse_id = "21708f39-20b9-4dda-9ab9-bd346e45ca0c"
workspace_id = "19f5ade2-5ab6-4e67-9c26-157935db64e3"

def convert_notebooks():
    for file_name, display_name in notebooks_to_convert:
        notebook_dir = os.path.join(base_dir, f"{display_name}.Notebook")
        os.makedirs(notebook_dir, exist_ok=True)
        
        # 1. Create .platform JSON
        platform_content = {
          "$schema": "https://developer.microsoft.com/json-schemas/fabric/gitIntegration/platformProperties/2.0.0/schema.json",
          "metadata": {
            "type": "Notebook",
            "displayName": display_name
          },
          "config": {
            "version": "2.0",
            "logicalId": str(uuid.uuid4())
          }
        }
        with open(os.path.join(notebook_dir, ".platform"), "w") as f:
            json.dump(platform_content, f, indent=2)
            
        # 2. Wrap and save notebook-content.py
        with open(os.path.join(base_dir, file_name), "r") as f:
            code_content = f.read()
            
        fabric_py_content = f"""# Fabric notebook source

# METADATA ********************

# META {{
# META   "kernel_info": {{
# META     "name": "synapse_pyspark"
# META   }},
# META   "dependencies": {{
# META     "lakehouse": {{
# META       "default_lakehouse": "{lakehouse_id}",
# META       "default_lakehouse_name": "MRPLakehouse",
# META       "default_lakehouse_workspace_id": "{workspace_id}"
# META     }}
# META   }}
# META }}

# CELL ********************

{code_content}

# METADATA ********************

# META {{
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }}
"""
        with open(os.path.join(notebook_dir, "notebook-content.py"), "w") as f:
            f.write(fabric_py_content)
            
        # 3. Clean up the original file
        os.remove(os.path.join(base_dir, file_name))
        print(f"Converted {file_name} to Fabric Git format in {notebook_dir}")

if __name__ == "__main__":
    convert_notebooks()
    print("Notebook restructuring completely successful!")
