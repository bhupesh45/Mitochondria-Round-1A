# Language-specific word count utility
from janome.tokenizer import Tokenizer
import jieba

# Init tokenizers
JANOME_TOKENIZER = Tokenizer()

def get_word_count(text, tokenizer_type):
    # Return word count using language-specific tokenizer
    if tokenizer_type == 'janome':
        return len(list(JANOME_TOKENIZER.tokenize(text)))
    if tokenizer_type == 'jieba':
        return len(list(jieba.cut(text)))
    return len(text.split())
