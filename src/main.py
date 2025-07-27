# Entry point for processing PDF files and extracting outlines
import os
import json

# Local imports
from pdf_analyzer import extract_outline_from_pdf
from config import INPUT_DIR, OUTPUT_DIR

def process_all_pdfs():
    # Process all PDFs in input directory
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)  # Create output dir if missing

    try:
        pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    except FileNotFoundError:
        print(f"Error: Input directory '{INPUT_DIR}' not found.")
        return

    if not pdf_files:
        print(f"No PDF files found in '{INPUT_DIR}'.")
        return

    print(f"Found {len(pdf_files)} PDF file(s) in '{INPUT_DIR}'")
    for filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, filename)
        output_filename = os.path.splitext(filename)[0] + ".json"
        output_filepath = os.path.join(OUTPUT_DIR, output_filename)

        print(f"--- Processing file: {filename} ---")
        try:
            result = extract_outline_from_pdf(pdf_path)
            with open(output_filepath, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Output written to: {output_filepath}")
        except Exception as e:
            print(f"Error processing file '{filename}': {e}")
        print("-" * (len(filename) + 25))

    print("\nAll PDF files processed.")

if __name__ == "__main__":
    process_all_pdfs()
