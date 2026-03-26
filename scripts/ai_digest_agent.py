import os
import sempy.fabric as fabric
from openai import AzureOpenAI

# ==========================================
# MRP AI Digest Agent (F-06)
# ==========================================
# This script is designed to run in a Microsoft Fabric Notebook.
# It queries the 'vw_part_criticality' table for high risk parts,
# formats the data, and calls an Azure OpenAI language model to 
# generate a natural language summary for the management team.

def generate_daily_digest():
    print("Fetching critical parts from MRPLakehouse...")
    
    # 1. Query the semantic model or lakehouse directly for parts that need reordering
    try:
        df_critical = fabric.evaluate_measure(
            dataset="MRPLakehouse",
            measure="COUNTROWS('vw_part_criticality')",
            groupby_columns=["vw_part_criticality[part_id]", "vw_part_criticality[months_of_supply]", "vw_part_criticality[total_on_hand]"]
        )
        # Filter to only parts with negative months of supply (or whatever threshold)
        df_critical = df_critical[df_critical['vw_part_criticality[months_of_supply]'] < 0]
        # Sort by most critical
        df_critical = df_critical.sort_values(by='vw_part_criticality[months_of_supply]')
        top_risks = df_critical.head(5)
    except Exception as e:
        print(f"Error querying Fabric data: {e}")
        return

    if top_risks.empty:
        print("No critical parts found today. System healthy.")
        return

    # 2. Format the data context for the LLM
    data_context = "Top critical parts needing reorder:\n"
    for index, row in top_risks.iterrows():
        part_id = row['vw_part_criticality[part_id]']
        mos = row['vw_part_criticality[months_of_supply]']
        on_hand = row['vw_part_criticality[total_on_hand]']
        data_context += f"- Part: {part_id} | On Hand: {on_hand} | Months of Supply: {mos:.2f}\n"

    print("\nData collected. Generating AI summary...")

    # 3. Call Azure OpenAI
    # (Requires these environment variables or workspace secrets to be set)
    api_key = os.getenv("AZURE_OPENAI_API_KEY", "your-azure-openai-key")
    endpoint = os.getenv("AZURE_OPENAI_ENDPOINT", "https://your-endpoint.openai.azure.com/")
    deployment_name = os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME", "gpt-4")

    if api_key == "your-azure-openai-key":
        print("Azure OpenAI credentials not configured. Here is the context that would be sent:")
        print(data_context)
        return

    client = AzureOpenAI(
        api_key=api_key,
        api_version="2023-12-01-preview",
        azure_endpoint=endpoint
    )

    prompt = f"""
    You are an AI Supply Chain Assistant for Mountain Racing Products (MRP).
    Your task is to review the following critical inventory shortages and write a concise, professional, 5-8 sentence daily digest email to the management team (Rich and Tim). 

    {data_context}

    Highlight the most urgent shortages, specify that they need PO placement or air expedites, and maintain a calm, helpful tone.
    """

    try:
        response = client.chat.completions.create(
            model=deployment_name,
            messages=[
                {"role": "system", "content": "You are a helpful supply chain assistant."},
                {"role": "user", "content": prompt}
            ],
            max_tokens=300,
            temperature=0.3
        )
        
        digest = response.choices[0].message.content
        print("\n================ DAILY AI DIGEST ================\n")
        print(digest)
        print("\n=================================================")
        
        # 4. Step to send email via Power Automate HTTP trigger or Office365 API goes here.
        # requests.post(POWER_AUTOMATE_WEBHOOK_URL, json={"body": digest})
        
    except Exception as e:
        print(f"AI Generation failed: {e}")

if __name__ == "__main__":
    generate_daily_digest()
