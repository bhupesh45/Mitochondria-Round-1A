import os
import json
import re
from collections import Counter, defaultdict
import pdfplumber
import statistics

# --- Multilingual & NLP Dependencies ---
from langdetect import detect, DetectorFactory
from janome.tokenizer import Tokenizer
import jieba

# Ensure consistent language detection
DetectorFactory.seed = 0

# --- Configuration ---
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

# --- Heuristic Scoring Parameters ---
SCORE_THRESHOLD = 5.0
FONT_SIZE_MULTIPLIER = 1.15
FONT_SCORE = 4.0
BOLD_SCORE = 3.5
WORD_COUNT_SCORE = 2.0
ALL_CAPS_SCORE = 2.5
TITLE_CASE_SCORE = 1.5
NUMBERING_SCORE = 6.0
PERIOD_PENALTY = -5.0
MAX_HEADING_WORDS = 12

# --- Language Properties ---
LANGUAGE_PROPERTIES = {
    'en': {'has_case': True, 'tokenizer': 'default'},
    'ja': {'has_case': False, 'tokenizer': 'janome'},
    'zh-cn': {'has_case': False, 'tokenizer': 'jieba'},
    'zh-tw': {'has_case': False, 'tokenizer': 'jieba'},
    'default': {'has_case': True, 'tokenizer': 'default'}
}


def get_word_count(text, tokenizer_type, tokenizer_instance):
    """Return word count based on language-specific tokenizer."""
    if tokenizer_type == 'janome' and tokenizer_instance:
        return len(list(tokenizer_instance.tokenize(text)))
    if tokenizer_type == 'jieba':
        return len(list(jieba.cut(text)))
    return len(text.split())


def detect_repeating_lines(pages, page_count):
    """Identify repeated lines that may indicate headers or footers."""
    line_positions = defaultdict(list)
    sample_pages = pages[:3] + pages[-3:] if page_count > 6 else pages

    for page in sample_pages:
        lines = page.extract_text_lines(layout=True, strip=False, x_tolerance=3, y_tolerance=3)
        for line in lines:
            text = re.sub(r'\s+', ' ', line['text']).strip().lower()
            if text and not (text.isdigit() and len(text) < 4):
                line_positions[(text, round(line['top']))].append(page.page_number)

    repeated_lines = set()
    min_occurrences = max(2, page_count // 4)

    for (text, _), pages_appeared in line_positions.items():
        if len(set(pages_appeared)) >= min_occurrences:
            repeated_lines.add(text)

    return repeated_lines


def analyze_text_style(words):
    """Determine the most common font size and font name to define body text style."""
    if not words:
        return 12, "default", False

    font_counts = Counter((round(w['size']), w['fontname']) for w in words if w['text'].strip())
    if not font_counts:
        return 12, "default", False

    most_common_style = font_counts.most_common(1)[0][0]
    body_size, body_font = most_common_style
    is_bold = 'bold' in body_font.lower()

    return body_size, body_font, is_bold


def calculate_heading_score(line, body_size, body_is_bold, lang_props, tokenizer):
    """Compute a heuristic score for a line to determine if it is a heading."""
    score = 0.0
    text = re.sub(r'\s+', ' ', line['text']).strip()
    word_count = get_word_count(text, lang_props['tokenizer'], tokenizer)

    if not text or word_count > MAX_HEADING_WORDS * 1.5:
        return 0.0

    first_char = line['chars'][0]
    line_size = round(first_char['size'])
    is_bold = 'bold' in first_char['fontname'].lower()

    if line_size > body_size * FONT_SIZE_MULTIPLIER:
        score += FONT_SCORE
    if is_bold and not body_is_bold:
        score += BOLD_SCORE
    if word_count < MAX_HEADING_WORDS:
        score += WORD_COUNT_SCORE

    if lang_props['has_case']:
        if text.isupper() and word_count > 1:
            score += ALL_CAPS_SCORE
        elif text.istitle() and word_count > 1:
            score += TITLE_CASE_SCORE

    if re.match(r'^((\b[IVXLCDM]+\b\.)|\d+(\.\d+)*\.?)', text):
        score += NUMBERING_SCORE
    if text.endswith(('.', ':', ',')):
        score += PERIOD_PENALTY

    return score


def extract_outline_from_pdf(pdf_path):
    """Extract document title and outline (headings with page numbers) from a PDF."""
    with pdfplumber.open(pdf_path) as pdf:
        all_words = [w for p in pdf.pages for w in p.extract_words(extra_attrs=['size', 'fontname'])]

        text_sample = " ".join([w['text'] for w in all_words[:500]])
        try:
            lang = detect(text_sample)
        except:
            lang = 'en'
        print(f"Detected language: {lang.upper()}")

        lang_props = LANGUAGE_PROPERTIES.get(lang, LANGUAGE_PROPERTIES['default'])
        lang_props['lang_code'] = lang

        tokenizer_instance = Tokenizer() if lang_props['tokenizer'] == 'janome' else None

        body_size, _, body_is_bold = analyze_text_style(all_words)
        headers_footers = detect_repeating_lines(pdf.pages, len(pdf.pages))

        potential_headings = []
        for i, page in enumerate(pdf.pages):
            lines = page.extract_text_lines(layout=True, strip=False, x_tolerance=3, y_tolerance=3)
            for line in lines:
                clean_text = re.sub(r'\s+', ' ', line['text']).strip()
                if not clean_text or clean_text.lower() in headers_footers:
                    continue

                score = calculate_heading_score(line, body_size, body_is_bold, lang_props, tokenizer_instance)
                if score >= SCORE_THRESHOLD:
                    potential_headings.append({
                        "text": clean_text,
                        "size": round(line['chars'][0]['size']),
                        "page": i,
                        "score": score
                    })

    if not potential_headings:
        return {"title": os.path.basename(pdf_path).replace('.pdf', ''), "outline": []}

    heading_sizes = sorted(list(set(h['size'] for h in potential_headings)), reverse=True)
    title_size = heading_sizes[0] if heading_sizes else body_size
    level_sizes = [s for s in heading_sizes if s < title_size]
    size_to_level = {size: f"H{i+1}" for i, size in enumerate(level_sizes[:3])}

    title_candidates = [h['text'] for h in potential_headings if h['size'] == title_size and h['page'] <= 1]
    document_title = ' '.join(title_candidates) if title_candidates else os.path.basename(pdf_path).replace('.pdf', '')

    outline = []
    for h in potential_headings:
        if h['size'] in size_to_level:
            outline.append({"level": size_to_level[h['size']], "text": h['text'], "page": h['page']})

    outline.sort(key=lambda x: (x['page'], int(x['level'][1:])))
    return {"title": document_title, "outline": outline}


def process_all_pdfs():
    """Process all PDF files in the input directory and write their outlines to output."""
    if not os.path.exists(OUTPUT_DIR):
        os.makedirs(OUTPUT_DIR)

    try:
        pdf_files = [f for f in os.listdir(INPUT_DIR) if f.lower().endswith(".pdf")]
    except FileNotFoundError:
        print(f"Error: Input directory '{INPUT_DIR}' not found.")
        return

    print(f"Found {len(pdf_files)} PDF file(s) in '{INPUT_DIR}'")
    for filename in pdf_files:
        pdf_path = os.path.join(INPUT_DIR, filename)
        output_filepath = os.path.join(OUTPUT_DIR, os.path.splitext(filename)[0] + ".json")
        print(f"Processing file: {filename}")
        try:
            result = extract_outline_from_pdf(pdf_path)
            with open(output_filepath, "w", encoding="utf-8") as f:
                json.dump(result, f, indent=2, ensure_ascii=False)
            print(f"Output written to: {output_filepath}")
        except Exception as e:
            print(f"Error processing file '{filename}': {e}")

    print("All PDF files have been processed.")


if __name__ == "__main__":
    process_all_pdfs()
