import os
import json
import re
from collections import Counter, defaultdict
import pdfplumber
import statistics

# -----------------------------
# Configuration
# -----------------------------
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

def detect_repeating_lines(pages):
    """
    Identify lines (typically headers or footers) that appear in the same position 
    across multiple pages using positional stability and frequency.
    """
    line_positions = defaultdict(list)

    for idx, page in enumerate(pages):
        lines = page.extract_text_lines(layout=True, strip=False)
        for line in lines:
            text = re.sub(r'\s+', ' ', line['text']).strip()
            if text:
                top_pos = round(line['top'], 1)
                line_positions[text].append(top_pos)

    repeated_lines = set()
    for text, positions in line_positions.items():
        if len(positions) >= 3 and statistics.stdev(positions) < 5:
            repeated_lines.add(text)

    return repeated_lines

def extract_outline_from_pdf(pdf_path):
    with pdfplumber.open(pdf_path) as pdf:
        words = []
        for page in pdf.pages:
            words.extend(page.extract_words(extra_attrs=['size', 'fontname']))

        if not words:
            return {
                "title": os.path.basename(pdf_path).replace('.pdf', ''),
                "outline": []
            }

        # Determine the most common body text size and font
        font_stats = Counter((round(w['size']), w['fontname']) for w in words)
        body_size, body_font = font_stats.most_common(1)[0][0]
        body_is_bold = 'bold' in body_font.lower()

        # Identify headers and footers to exclude them later
        repeated_lines = detect_repeating_lines(pdf.pages)

        potential_headings = []

        for page_num, page in enumerate(pdf.pages):
            lines = page.extract_text_lines(layout=True, strip=False)

            for line in lines:
                text = re.sub(r'\s+', ' ', line['text']).strip()

                if not text:
                    continue
                if len(text.split()) > 15 or text.endswith(('.', '!', '?')):
                    continue
                if text in repeated_lines:
                    continue

                first_char = line['chars'][0]
                font_size = round(first_char['size'])
                font_name = first_char['fontname']
                is_bold = 'bold' in font_name.lower()
                is_larger = font_size > (body_size * 1.1)
                is_all_caps = text.isupper() and len(text.split()) > 1
                numbered = re.match(
                    r'^((\b[IVXLCDM]+\b\.)|\d+(\.\d+)*\.?|(Appendix|Chapter|Section)\s+[A-Z0-9])',
                    text,
                    re.IGNORECASE
                )

                if numbered or (is_all_caps and is_larger) or (is_larger and is_bold and not body_is_bold):
                    potential_headings.append({
                        "text": text,
                        "size": font_size,
                        "page": page_num
                    })

        if not potential_headings:
            return {
                "title": os.path.basename(pdf_path).replace('.pdf', ''),
                "outline": []
            }

        # Analyze font sizes and assign heading levels (Title, H1, H2)
        sizes_sorted = sorted(set(h['size'] for h in potential_headings), reverse=True)

        if len(sizes_sorted) < 3:
            usable_sizes = sizes_sorted[1:]
        else:
            usable_sizes = sizes_sorted[1:3]

        size_to_level = {}
        if len(usable_sizes) > 0:
            size_to_level[usable_sizes[0]] = "H1"
        if len(usable_sizes) > 1:
            size_to_level[usable_sizes[1]] = "H2"

        # Extract title from the top-most heading(s) on the first page
        title_candidates = [
            h['text'] for h in potential_headings
            if h['size'] == sizes_sorted[0] and h['page'] == 0
        ]
        title_text = ' '.join(title_candidates) if title_candidates else potential_headings[0]['text']

        # Build outline, excluding title entries
        outline = []
        for heading in potential_headings:
            if heading['size'] in size_to_level:
                outline.append({
                    "level": size_to_level[heading['size']],
                    "text": heading['text'],
                    "page": heading['page']
                })

        title_set = set(title_candidates)
        final_outline = [h for h in outline if h['text'] not in title_set]

        # Sort headings by page number and heading level
        final_outline.sort(key=lambda h: (h['page'], int(h['level'][1:])))

        return {
            "title": title_text,
            "outline": final_outline
        }

def process_all_pdfs():
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    try:
        pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
        if not pdf_files:
            print(f"No PDF files found in '{INPUT_DIR}'.")
            return
    except FileNotFoundError:
        print(f"Error: Input directory '{INPUT_DIR}' not found.")
        return

    print(f"Processing {len(pdf_files)} PDF(s)...")
    for filename in pdf_files:
        input_path = os.path.join(INPUT_DIR, filename)
        output_filename = os.path.splitext(filename)[0] + ".json"
        output_path = os.path.join(OUTPUT_DIR, output_filename)

        print(f"Processing: {filename}")
        try:
            outline_data = extract_outline_from_pdf(input_path)
            with open(output_path, "w", encoding="utf-8") as outfile:
                json.dump(outline_data, outfile, indent=4, ensure_ascii=False)
            print(f"✅ Output written to: {output_path}")
        except Exception as e:
            print(f"❌ Error processing {filename}: {e}")

    print("✅ All PDFs processed successfully.")

if __name__ == "__main__":
    process_all_pdfs()
