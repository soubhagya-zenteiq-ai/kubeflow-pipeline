import os
import pypdf
import pandas as pd
import argparse
from pathlib import Path
import re

def clean_text(text):
    """
    Cleans raw PDF text for better embedding quality.
    Removes redundant whitespaces, newlines, and non-ASCII artifacts.
    """
    # Replace multiple newlines/spaces with a single space
    text = re.sub(r'\s+', ' ', text)
    # Remove basic non-printable characters
    text = re.sub(r'[^\x00-\x7F]+', ' ', text)
    return text.strip()

def ingest_pdfs(input_dir, output_file):
    processed_records = []
    input_path = Path(input_dir)
    
    # List all PDFs in the input directory
    pdf_files = list(input_path.glob("*.pdf"))
    print(f"🚀 Ingestion started. Found {len(pdf_files)} PDFs in {input_dir}")

    for pdf_file in pdf_files:
        try:
            print(f"📄 Processing: {pdf_file.name}")
            reader = pypdf.PdfReader(pdf_file)
            
            # Extract text page by page to maintain order
            full_text = ""
            for i, page in enumerate(reader.pages):
                page_text = page.extract_text()
                if page_text:
                    full_text += page_text + " "

            cleaned_content = clean_text(full_text)
            
            # Store with metadata (crucial for RAG source attribution)
            processed_records.append({
                "source_file": pdf_file.name,
                "content": cleaned_content,
                "char_count": len(cleaned_content)
            })
            
        except Exception as e:
            print(f"❌ Error processing {pdf_file.name}: {str(e)}")

    # Create a DataFrame and save as CSV for the Embedding component
    df = pd.DataFrame(processed_records)
    
    # Ensure the output directory exists
    os.makedirs(os.path.dirname(output_file), exist_ok=True)
    
    df.to_csv(output_file, index=False)
    print(f"✅ Ingestion complete. Data saved to {output_file}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="PDF Ingestion Worker")
    parser.add_argument("--input_dir", type=str, required=True, help="Folder containing PDFs")
    parser.add_argument("--output_file", type=str, required=True, help="Path to save the cleaned CSV")
    
    args = parser.parse_args()
    ingest_pdfs(args.input_dir, args.output_file)