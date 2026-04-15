import pandas as pd
import numpy as np
import argparse
import os
from llama_cpp import Llama

def generate_embeddings(input_csv, output_csv, model_path):
    # 1. Load the data from the Ingestion step
    df = pd.read_csv(input_csv)
    if 'content' not in df.columns:
        raise ValueError("Input CSV must have a 'content' column")

    print(f"Loading GGUF Model from: {model_path}")
    # 2. Initialize Llama-CPP (n_ctx is the context window)
    # We set n_gpu_layers=0 because you are on CPU only
    model = Llama(model_path=model_path, embedding=True, n_gpu_layers=0, n_ctx=2048)

    print(f"Processing {len(df)} rows...")
    vectors = []

    for text in df['content']:
        # 3. Generate the embedding vector
        # Qwen-VL-Embedding usually outputs a high-dimensional vector
        output = model.create_embedding(text)
        embedding_vector = output['data'][0]['embedding']
        vectors.append(embedding_vector)

    # 4. Attach vectors to dataframe
    # We store them as strings or objects so they fit in CSV easily
    df['vectors'] = vectors
    
    # 5. Save the 'Sink'
    df.to_csv(output_csv, index=False)
    print(f"Successfully saved embeddings to {output_csv}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--input_csv", type=str, required=True, help="Path to cleaned CSV from Ingestion")
    parser.add_argument("--output_csv", type=str, required=True, help="Path to save vectors")
    parser.add_argument("--model_path", type=str, required=True, help="Path to your .gguf file")
    args = parser.parse_args()

    os.makedirs(os.path.dirname(args.output_csv), exist_ok=True)
    generate_embeddings(args.input_csv, args.output_csv, args.model_path)