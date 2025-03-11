from html import unescape
import re
from collections import Counter
from nltk.corpus import stopwords

import nltk
nltk.download('stopwords')

def remove_repeated_text(text: str, threshold: int = 3) -> str:
    sentences = re.split(r'(?<=[.!?]) +', text)
    sentence_counts = Counter(sentences)
    filtered_sentences = [sentence for sentence in sentences if sentence_counts[sentence] <= threshold]
    filtered_text = ' '.join(filtered_sentences)
    return filtered_text

def clean_text(text: str) -> str:
    text = unescape(text)
    text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    text = re.sub(r'[^A-Za-z0-9æøåÆØÅ\s.,!?\'"-]', '', text)
    text = re.sub(r'\s+', ' ', text).strip()

    stop_words = set(stopwords.words('english'))
    text = ' '.join([word for word in text.split() if word.lower() not in stop_words])

    stop_words = set(stopwords.words('norwegian'))
    text = ' '.join([word for word in text.split() if word.lower() not in stop_words])

    return text

# from transformers import pipeline, BartTokenizer
# summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
# tokenizer = BartTokenizer.from_pretrained('facebook/bart-large-cnn')

# def summarize_text(text):    
#     if not text: return ""
#     inputs = tokenizer(text, return_tensors='pt', truncation=True, max_length=1024)
#     if len(inputs['input_ids'][0]) < 512:
#         return text
#     text = tokenizer.decode(inputs['input_ids'][0], skip_special_tokens=True)
#     summary = summarizer(text, max_length=256, min_length=50, do_sample=False)
#     return summary[0]['summary_text']