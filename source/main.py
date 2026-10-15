import os
import json
import csv
import time
from pathlib import Path
from dotenv import load_dotenv
from google import genai
from google.genai import types

load_dotenv(Path(__file__).with_name(".env"))
client = genai.Client()

def extract_level1(image_bytes, model_name):
    prompt = """
    Extract the billing details from this electricity bill.
    Follow these strict rules:
    - Amounts are numbers in PKR. Remove currency labels and commas.
    - Credits and subsidies are negative.
    - Use null for unavailable values. Do not guess.
    - Exclude personal identifiers.
    - For payable_after_due_date, if several late-payment amounts are shown, use the highest.

    Return ONLY a raw JSON object following this exact structure:
    {
      "provider": "KE | LESCO | IESCO",
      "tariff": "string",
      "sanctioned_load_kw": "number",
      "bill_month": "YYYY-MM",
      "reading_date": "YYYY-MM-DD",
      "issue_date": "YYYY-MM-DD",
      "due_date": "YYYY-MM-DD",
      "previous_reading": "number",
      "current_reading": "number",
      "units_consumed": "number",
      "charges": [
        {
          "type": "energy | fixed | fpa | quarterly_adjustment | surcharge | meter_rent | subsidy | other",
          "amount": "number"
        }
      ],
      "total_charges": "number",
      "taxes": [
        {
          "type": "gst | electricity_duty | income_tax | municipal_tax | other_tax",
          "amount": "number"
        }
      ],
      "total_taxes": "number",
      "current_bill": "number",
      "arrears": "number",
      "payable_within_due_date": "number",
      "payable_after_due_date": "number"
    }
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png" if image_bytes.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg"),
                    prompt
                ],
                config=types.GenerateContentConfig(
                    response_mime_type="application/json",
                    temperature=0.1
                )
            )
            bill_json_obj = json.loads(response.text)
            return json.dumps(bill_json_obj, separators=(',', ':'))
        except Exception as e:
            print(f"    [Attempt {attempt+1}/{max_retries}] Server Error: {e}")
            if attempt < max_retries - 1:
                print("    Waiting 10 seconds before retrying...")
                time.sleep(10)
            else:
                return "{}"

def answer_level2(image_bytes, question, model_name):
    prompt = f"""
    You are a helpful customer support assistant explaining an electricity bill.
    Answer the following customer question based ONLY on the provided bill image.
    
    Rules:
    - Ground your answer in the bill. If the bill does not show a needed value, say so instead of guessing.
    - Calculate accurately (averages, differences, counts, percentages).
    - Label any estimates and explain how you calculated them.
    - Explain ambiguous interpretations.
    - Exclude personal identifiers.
    - Write your answer in plain English.

    CRITICAL CHART READING RULES:
    When analyzing the "13 Month Usage History" bar chart, you must strictly align the data:
    1. Read the exact number written vertically inside each bar.
    2. Match it ONLY to the specific month abbreviation located directly below that exact bar.
    3. Read the chart sequentially from left to right (from 2025 to 2026) to ensure you do not skip or misalign months before determining the highest or lowest values. 
    
    Customer Question: {question}
    """
    
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = client.models.generate_content(
                model=model_name,
                contents=[
                    types.Part.from_bytes(data=image_bytes, mime_type="image/png" if image_bytes.startswith(b"\x89PNG\r\n\x1a\n") else "image/jpeg"),
                    prompt
                ],
                config=types.GenerateContentConfig(temperature=0.1)
            )
            return response.text.strip()
        except Exception as e:
            print(f"    [Attempt {attempt+1}/{max_retries}] Server Error: {e}")
            if attempt < max_retries - 1:
                print("    Waiting 10 seconds before retrying...")
                time.sleep(10)
            else:
                return "Error: Could not generate answer."

def process_all():
    model_name = os.getenv("MODEL_NAME", "gemini-3.5-flash-lite")
    test_bills_folder = "test/bills"
    level1_template = "test/csv/level1.csv"
    level2_template = "test/csv/level2.csv"
    
    output_level1_path = "output/level1.csv"
    output_level2_path = "output/level2.csv"
    
    os.makedirs("output", exist_ok=True)
    image_cache = {}
    
    print("=== STARTING LEVEL 1 EXTRACTION ===")
    level1_results = []
    with open(level1_template, 'r', encoding='utf-8') as f:
        rows = list(csv.DictReader(f))
        
    for row in rows:
        bill_id = row['bill_id']
        print(f"Extracting Level 1 JSON for {bill_id}...")
        
        image_file = None
        for ext in ['.png', '.jpg', '.jpeg']:
            possible_path = os.path.join(test_bills_folder, f"{bill_id}{ext}")
            if os.path.exists(possible_path):
                image_file = possible_path
                break
                
        if not image_file:
            print(f"Warning: Image file for {bill_id} not found!")
            continue
            
        with open(image_file, "rb") as img_f:
            img_bytes = img_f.read()
            image_cache[bill_id] = img_bytes
            
        extracted_json = extract_level1(img_bytes, model_name)
        level1_results.append({"bill_id": bill_id, "json": extracted_json})
        time.sleep(4.5) 

    with open(output_level1_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['bill_id', 'json'], quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(level1_results)
    print(f"Saved Level 1 results to {output_level1_path}\n")

    print("=== STARTING LEVEL 2 QUESTION ANSWERING ===")
    level2_results = []
    with open(level2_template, 'r', encoding='utf-8') as f:
        l2_rows = list(csv.DictReader(f))

    total_q = len(l2_rows)
    for index, row in enumerate(l2_rows, start=1):
        bill_id = row['bill_id']
        q_id = row['question_id']
        question = row['question']
        
        print(f"[{index}/{total_q}] Answering {q_id} for {bill_id}...")
        
        img_bytes = image_cache.get(bill_id)
        if img_bytes:
            ans = answer_level2(img_bytes, question, model_name)
        else:
            ans = "Bill image not found."

        level2_results.append({
            "bill_id": bill_id,
            "question_id": q_id,
            "question": question,
            "answer": ans
        })
        time.sleep(4.5)

    with open(output_level2_path, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=['bill_id', 'question_id', 'question', 'answer'], quoting=csv.QUOTE_MINIMAL)
        writer.writeheader()
        writer.writerows(level2_results)
    print(f"Saved Level 2 results to {output_level2_path}\n")
    print("ALL DONE!")

if __name__ == "__main__":
    process_all()
