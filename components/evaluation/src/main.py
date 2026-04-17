import pandas as pd
import argparse
import os
import json
from llama_cpp import Llama

def evaluate_chunks(input_csv, output_report, model_path):
    print(f"🧠 Loading Evaluation Judge model from {model_path}...")
    llm = Llama(model_path=model_path, verbose=False)
    
    df = pd.read_csv(input_csv)
    
    # We sample the data to save time/compute during evaluation
    sample_df = df.sample(min(len(df), 5)) 
    results = []

    print(f"🧐 Starting Quality Evaluation on {len(sample_df)} samples...")

    for _, row in sample_df.iterrows():
        context = str(row['content'])[:500] # Send first 500 chars for context
        
        prompt = f"""<|im_start|>system
You are a Data Quality Auditor. Grade the following text from a PDF. Is it actual information or just noise?
Respond ONLY in JSON: {{"score": 1-10, "reason": "why"}}<|im_end|>
<|im_start|>user
Text: {context}<|im_end|>
<|im_start|>assistant
"""

        try:
            output = llm(prompt, max_tokens=100, stop=["<|im_end|>"])
            text_response = output['choices'][0]['text']
            results.append({
                "source": row['source_file'],
                "eval": text_response
            })
            print(f"✅ Evaluated: {row['source_file']}")
        except Exception as e:
            print(f"⚠️ Eval failed for a row: {e}")
            results.append({"error": str(e)})

    # Save the evaluation report
    with open(output_report, 'w') as f:
        json.dump(results, f, indent=2)
    
    print(f"✅ Evaluation Report saved to {output_report}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", type=str, required=True)
    parser.add_argument("--output_report", type=str, required=True)
    parser.add_argument("--model_path", type=str, required=True)
    
    args = parser.parse_args()
    evaluate_chunks(args.input_csv, args.output_report, args.model_path)