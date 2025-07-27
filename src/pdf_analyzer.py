# Extract title and outline from PDF using heuristics
import os
import re
import pdfplumber
from collections import Counter, defaultdict
from langdetect import detect, DetectorFactory

# Local imports
import config
from utils import get_word_count

DetectorFactory.seed = 0  # Fix language detection randomness

def _detect_repeating_lines(pages):
    # Find repeated lines (headers/footers)
    line_positions = defaultdict(list)
    page_count = len(pages)
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

def _analyze_text_style(words):
    # Find common font size and style
    if not words:
        return 12, "default", False
    font_counts = Counter((round(w['size']), w['fontname']) for w in words if w['text'].strip())
    if not font_counts:
        return 12, "default", False
    most_common_style = font_counts.most_common(1)[0][0]
    body_size, body_font = most_common_style
    is_bold = 'bold' in body_font.lower()
    return body_size, body_font, is_bold

def _calculate_heading_score(line, body_size, body_is_bold, lang_props):
    # Compute score to check if line is heading
    score = 0.0
    text = re.sub(r'\s+', ' ', line['text']).strip()
    word_count = get_word_count(text, lang_props['tokenizer'])
    if not text or word_count > config.MAX_HEADING_WORDS * 1.5:
        return 0.0
    first_char = line['chars'][0]
    line_size = round(first_char['size'])
    is_bold = 'bold' in first_char['fontname'].lower()
    if line_size > body_size * config.FONT_SIZE_MULTIPLIER:
        score += config.FONT_SCORE
    if is_bold and not body_is_bold:
        score += config.BOLD_SCORE
    if word_count < config.MAX_HEADING_WORDS:
        score += config.WORD_COUNT_SCORE
    if lang_props['has_case']:
        if text.isupper() and word_count > 1:
            score += config.ALL_CAPS_SCORE
        elif text.istitle() and word_count > 1:
            score += config.TITLE_CASE_SCORE
    if re.match(r'^((\b[IVXLCDM]+\b\.)|\d+(\.\d+)*\.?)', text):
        score += config.NUMBERING_SCORE
    if text.endswith(('.', ':', ',')):
        score += config.PERIOD_PENALTY
    return score

def extract_outline_from_pdf(pdf_path):
    # Extract title and outline from PDF
    with pdfplumber.open(pdf_path) as pdf:
        all_words = [w for p in pdf.pages for w in p.extract_words(extra_attrs=['size', 'fontname'])]
        text_sample = " ".join([w['text'] for w in all_words[:500]])
        try:
            lang = detect(text_sample)
        except Exception:
            lang = 'en'
        print(f"Detected language: {lang.upper()}")
        lang_props = config.LANGUAGE_PROPERTIES.get(lang, config.LANGUAGE_PROPERTIES['default'])
        body_size, _, body_is_bold = _analyze_text_style(all_words)
        headers_footers = _detect_repeating_lines(pdf.pages)
        potential_headings = []
        for i, page in enumerate(pdf.pages):
            lines = page.extract_text_lines(layout=True, strip=False, x_tolerance=3, y_tolerance=3)
            for line in lines:
                clean_text = re.sub(r'\s+', ' ', line['text']).strip()
                if not clean_text or clean_text.lower() in headers_footers:
                    continue
                score = _calculate_heading_score(line, body_size, body_is_bold, lang_props)
                if score >= config.SCORE_THRESHOLD:
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
