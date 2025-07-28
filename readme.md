# Adobe India Hackathon 2025 - Round 1A: Understand Your Document

Welcome to the **Connecting the Dots Challenge**. This project was developed as part of the **Adobe India Hackathon 2025 (Round 1A)**, where we rethink how we interact with PDFs—transforming them into intelligent, structured, and meaningful digital experiences.

---

## Installation & Setup

### Docker Setup

To ensure compatibility with the judging environment, Docker usage is **required**.

#### Build Image (AMD64 platform)

```bash
docker build --platform linux/amd64 -t round1a:mitochondria .
```

#### Run Container (Offline, no internet access)

```bash
docker run --rm \
  -v $(pwd)/input:/app/input \
  -v $(pwd)/output:/app/output \
  --network none \
  round1a:mitochondria
```

---

## Project Objective

Extract a **structural outline** from a PDF document:

* Identify the **document title**
* Extract hierarchical headings: **H1**, **H2**, **H3**, including their **page numbers**
* Output a valid JSON in the required format

---

## Project Structure

```
adobe_round_1A/
│
├── src/
│   └── main.py             # Main script for PDF structure extraction
│
├── input/
│   ├── file01.pdf          # Sample input PDFs
│   └── ...
│
├── output/
│   ├── file01.json         # Output JSONs matching input PDFs
│   └── ...
│
├── requirements.txt        # Python dependencies
└── Dockerfile              # Docker setup for offline processing
```

---

## Execution Flow

Upon execution, the container will:

1. **Read** all `.pdf` files from the `/app/input` directory.
2. **Process** each file to extract:

   * Title
   * Headings (H1, H2, H3) with page numbers
3. **Save** structured output JSON in `/app/output`, maintaining filename consistency.

---

## Sample Output Format

```json
{
  "title": "South of France - Cities",
  "outline": [
    { "level": "H1", "text": "Introduction", "page": 1 },
    { "level": "H2", "text": "Geography", "page": 2 },
    { "level": "H3", "text": "Climate", "page": 3 }
  ]
}
```

---

## Dependencies

Listed in `requirements.txt`:

* `pdfplumber` – PDF text and layout extraction
* `spacy` – Natural language processing
* `langdetect` – Language identification (**for multilingual support**)
* `jieba`, `janome` – Tokenizers for **Chinese and Japanese text handling**

> **Note:** Multilingual handling is a key bonus criterion. Our solution robustly processes non-Latin scripts, enabling extraction from documents in **Japanese**, **Chinese**, and other languages.

---

## Constraints

| Constraint           | Requirement                            |
| -------------------- | -------------------------------------- |
| Execution Time       | ≤ 10 seconds per 50-page PDF           |
| Model Size (if used) | ≤ 200MB                                |
| Network              | Offline only (no internet access)      |
| Architecture         | CPU only, `amd64`, no GPU dependencies |
| Memory               | Runs on 16GB RAM, 8 CPU system         |

---

## Approach Summary

* **Hybrid strategy** combining font size analysis, layout heuristics, and linguistic cues.
* **Multilingual support** using `langdetect`, `jieba`, and `janome` for non-Latin scripts.
* **Heading validation** via text classification (to filter out non-heading text).
* **Offline processing** with optimized runtime and memory footprint.
* **Hierarchical JSON** built by tracking heading levels and their relationships.

**Multilingual:** Our extractor is optimized to **handle multilingual documents**, ensuring accurate heading extraction across **English**, **Chinese**, **Japanese**, and more. This boosts document intelligence for global content.

---

## Authors

* Team: *Mitochondria*
* Event: Adobe India Hackathon 2025 - Round 1A
