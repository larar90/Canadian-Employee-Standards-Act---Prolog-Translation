
## Employment‑Standards‑Act → Prolog Converter

Turn the entire Ontario **Employment Standards Act, 2000** (or any other lengthy statute) into a clean set of executable Prolog rules — complete with obligations, prohibitions, entitlements and penalties — in a single command.  
Behind the scenes the tool combines **PyMuPDF‑powered** PDF parsing, an **OCR fallback**, and the reasoning muscle of **OpenAI GPT‑4o** to ensure that even scanned pages and footnotes are captured accurately.

---

### ✨  Key Features
* **Robust PDF extraction** – PyMuPDF reads embedded text; image‑only pages are piped through Tesseract OCR so nothing is lost. :contentReference[oaicite:0]{index=0}  
* **Chunk‑aware LLM translation** – Long acts are sliced into ~1 600‑token windows so every clause fits inside GPT‑4o’s 128 k context ceiling. :contentReference[oaicite:1]{index=1}  
* **Progress bars** – Two `tqdm` bars track PDF scanning and LLM translation in real time. :contentReference[oaicite:2]{index=2}  
* **Deterministic name harmonisation** – A fast regex pass unifies predicate and variable spellings across chunks before the final LLM clean‑up, guaranteeing duplicates collapse correctly. :contentReference[oaicite:3]{index=3}  
* **Single‑file output** – The resulting rules are written to  
  `…/Canadian‑Employee‑Standards‑Act---Prolog‑Translation/<PDF‑name>_prolog.txt`.

---

### 📦  Requirements

| Package | Purpose |
|---------|---------|
| `PyMuPDF >= 1.25` | High‑fidelity PDF parsing with image export :contentReference[oaicite:4]{index=4} |
| `pytesseract >= 0.3` | OCR fallback for scanned pages :contentReference[oaicite:5]{index=5} |
| `tesseract` binary | Install via `brew install tesseract` on macOS :contentReference[oaicite:6]{index=6} |
| `openai >= 1.77` | Access to GPT‑4o Chat Completions :contentReference[oaicite:7]{index=7} |
| `python‑dotenv >= 1.0` | Load `OPENAI_API_KEY` from a `.env` file :contentReference[oaicite:8]{index=8} |
| `tqdm >= 4.66` | Pretty progress bars :contentReference[oaicite:9]{index=9} |

> **Note:** GPT‑4o’s 128 k token context is ample for provincial acts; if you migrate to GPT‑4.1 Mini/Nano you’ll still be well within limits :contentReference[oaicite:10]{index=10}.

---

### 🔧  Installation

```bash
# 1. Create and activate a virtual environment
python3 -m venv .venv
source .venv/bin/activate

# 2. Install Python dependencies
pip install -r requirements.txt

# 3. Install Tesseract OCR engine (macOS)
brew install tesseract
````

Add your OpenAI key to a `.env` file:

```bash
echo 'OPENAI_API_KEY=sk-…' >> .env
```

---

### 🚀  Usage

The script is wired for a single, hard‑coded file path, but you can edit it or wrap it in a CLI of your choice.

```bash
python main.py
```

Console output:

```
Scanning PDF: 100%|██████████| 217/217 [00:14<00:00, 15.4page/s]
LLM translate: 100%|██████████| 42/42 [04:07<00:00,  5.89s/it]
🧹  Normalising & deduplicating …
✔  Saved /…/Employment_Standards_Act_ontario.ca_prolog.txt
```

Open the text file to see rules such as:

```prolog
obligation(employer, pay_minimum_wage).
prohibition(employer, withhold_wages_without_authorization).
penalty(recruiter, fine_for_non_compliance).
```

---

### 🏗️  How It Works

1. **PDF scan** – `fitz.open(pdf_path)` streams each page; empty pages are rasterised and OCR‑ed. ([PyMuPDF][1], [PyImageSearch][2])
2. **Chunking** – Paragraphs are grouped until \~4 000 chars to respect the model’s message limits.
3. **First GPT‑4o pass** – Each chunk is translated into Prolog with a strict schema prompt.
4. **Local name normalisation** – `unify_names()` sticks to the first spelling of every identifier using `re` word‑boundary replacements ([Stack Overflow][3], [W3Schools.com][4]).
5. **Second GPT‑4o pass** – Rules are deduped and final‑polished.
6. **Write‑out** – Everything ends up in the fixed `TARGET_DIR`.

---

### ⚠️  Known Limitations & Future Work

* The simple regex pass can’t detect semantic aliases (`pay_wages` vs `remunerate_employee`). A future version could send a synonym‑merging prompt to GPT‑4o or GPT‑4.1 Mini.
* For multi‑province support, swap the source PDF and perhaps adjust the ontology (e.g., add `exception/2`).
* The script currently runs synchronously; parallel chunk translation could cut end‑to‑end time in half — pending OpenAI rate‑limit allowances.

---

### 🤝  Contributing

Pull requests are welcome!  Please lint with **Black** and keep the Prolog schema unchanged unless you also update the prompts and README.

---

### 📜  License

Distributed under the Apache 2.0 License — the same open license used by the OpenAI Python SDK and PyMuPDF. ([GitHub][5], [PyMuPDF][1])

```
