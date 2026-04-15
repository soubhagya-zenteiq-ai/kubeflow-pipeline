import pandas as pd
import requests
import argparse
import os
import json

def evaluate_chunks(input_csv, output_report, llm_endpoint):
    df = pd.read_csv(input_csv)
    
    # We sample the data to save time/compute during evaluation
    sample_df = df.sample(min(len(df), 5)) 
    results = []

    print(f"🧐 Starting Quality Evaluation on {len(sample_df)} samples...")

    for _, row in sample_df.iterrows():
        context = row['content'][:500] # Send first 500 chars for context
        
        prompt = f"""
        System: You are a Data Quality Auditor.
        Task: Grade the following extracted text from a PDF. 
        Criteria: Is it readable? Is it actual information or just noise/headers?
        Text: {context}
        
        Respond ONLY in JSON format: {{"score": 1-10, "reason": "short explanation"}}
        """

        try:
            # Calling a local LLM API (like Ollama running on your Ubuntu)
            response = requests.post(
                llm_endpoint,
                json={
                    "model": "llama3", # or qwen
                    "prompt": prompt,
                    "stream": False
                }
            )
            grade = response.json().get('response', '{}')
            results.append(grade)
        except Exception as e:
            print(f"⚠️ Eval failed for a row: {e}")
            results.append("Error")

    # Save the evaluation report
    with open(output_report, 'w') as f:
        json.dump(results, f)
    
    print(f"✅ Evaluation Report saved to {output_report}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", type=str, required=True)
    parser.add_argument("--output_report", type=str, required=True)
    parser.add_argument("--llm_endpoint", type=str, default="http://localhost:11434/api/generate")
    
    args = parser.parse_args()
    evaluate_chunks(args.input_csv, args.output_report, args.llm_endpoint)