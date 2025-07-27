# --- Directories ---
INPUT_DIR = "/app/input"
OUTPUT_DIR = "/app/output"

# --- Scoring Thresholds ---
SCORE_THRESHOLD = 5.0        # Min score to accept heading
MAX_HEADING_WORDS = 12       # Max words in heading

# --- Font/Style Scoring ---
FONT_SIZE_MULTIPLIER = 1.15  # Heading font size multiplier
FONT_SCORE = 4.0             # Score for large font
BOLD_SCORE = 3.5             # Score for bold font
ALL_CAPS_SCORE = 2.5         # Score for all caps
TITLE_CASE_SCORE = 1.5       # Score for title case

# --- Structure Scoring ---
NUMBERING_SCORE = 6.0        # Score for numbered lines
WORD_COUNT_SCORE = 2.0       # Score for word count
PERIOD_PENALTY = -5.0        # Penalty for trailing period

# --- Language Settings ---
LANGUAGE_PROPERTIES = {
    'en': {'has_case': True, 'tokenizer': 'default'},
    'ja': {'has_case': False, 'tokenizer': 'janome'},
    'zh-cn': {'has_case': False, 'tokenizer': 'jieba'},
    'zh-tw': {'has_case': False, 'tokenizer': 'jieba'},
    'default': {'has_case': True, 'tokenizer': 'default'}
}
