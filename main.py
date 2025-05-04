#!/usr/bin/env python3
"""
esa_to_prolog.py – translates the Employment Standards Act PDF into a
deduplicated set of Prolog rules.  This edition adds a fixed‐width, 
auto‑sizing tqdm bar so the progress display ALWAYS stays on one line
(no ugly line wrapping after 20–30 %).
"""

from pathlib import Path
import os
import re
import sys
import fitz                       # PyMuPDF        -> pip install pymupdf
import pytesseract                # OCR fallback   -> brew install tesseract
from tempfile import NamedTemporaryFile
from dotenv import load_dotenv
from tqdm import tqdm             # progress bars  -> pip install tqdm
import openai                     # pip install openai

# --------------------------- configuration -------------------------- #
load_dotenv()
openai.api_key = os.getenv("OPENAI_API_KEY")

MODEL          = "gpt-4o"
TEMP           = 0.0
MAX_TOKENS     = 2048
CHUNK_CHARLEN  = 4_000           # ≈1 600 tokens
OUTPUT_SUFFIX  = "_prolog.txt"

# directory for the .txt result
TARGET_DIR = Path(
    "/Users/lararusso/Canadian-Employee-Standards-Act---Prolog-Translation"
).expanduser().resolve()

# A helper that returns a tqdm bar configured never to wrap
def one_line_bar(*args, **kwargs):
    """
    Wrapper around tqdm that keeps the bar on ONE terminal line by:
    • giving tqdm explicit ncols (80) so it never exceeds width
    • enabling dynamic_ncols so it shrinks if the window resizes
    • forcing unit width to guarantee stable bar length
    """
    defaults = dict(
        ncols=80,               # hard upper bound (fits 80‑col consoles)
        dynamic_ncols=True,     # adapt if terminal is narrower
        bar_format='{l_bar}{bar}| {n_fmt}/{total_fmt} [{elapsed}<{remaining}, {rate_fmt}]',
        file=sys.stderr,        # keep stdout clean for other prints
    )
    defaults.update(kwargs)
    return tqdm(*args, **defaults)

# ------------------------ PDF extraction --------------------------- #
def extract_page_text(page):
    text = page.get_text("text", sort=True).strip()
    if text:
        return text
    # OCR fallback
    with NamedTemporaryFile(suffix=".png") as tmp:
        page.get_pixmap().save(tmp.name)
        return pytesseract.image_to_string(tmp.name).strip()

def extract_pdf_text(pdf_path: Path) -> str:
    doc = fitz.open(pdf_path)
    pages = [extract_page_text(p) for p in one_line_bar(doc, desc="Scanning PDF")]
    return "\n\n".join(pages)

# ------------------------ chunking helper -------------------------- #
def chunk_text(text: str, max_chars: int = CHUNK_CHARLEN):
    buf, size, sep = [], 0, "\n\n"
    for para in text.split(sep):
        if size + len(para) + len(sep) > max_chars and buf:
            yield sep.join(buf)
            buf, size = [], 0
        buf.append(para)
        size += len(para) + len(sep)
    if buf:
        yield sep.join(buf)

# -------------------------- OpenAI call ---------------------------- #
def chat(msgs):
    client = openai.OpenAI()
    res = client.chat.completions.create(
        model=MODEL, temperature=TEMP, max_tokens=MAX_TOKENS, messages=msgs
    )
    return res.choices[0].message.content.strip()

# ----------------------- LLM prompts ------------------------------- #
SYS_TRANSLATE = """You are a legal‑domain knowledge engineer.
Read the supplied text from the Employment Standards Act (Ontario).
Convert EVERY enforceable clause into exactly one Prolog formula.
No prose, one clause per line, snake_case identifiers. Make sure to use the same predicate and variable name for the same predicate and variables."""
SYS_NORMALISE = """Ensure identical spellings for every predicate and
variable across the supplied rules; remove duplicates; output only
newline‑separated Prolog."""

name_registry = {}

def unify_names(rules: str) -> str:
    token = re.compile(r'[A-Za-z_][A-Za-z0-9_]*')
    fixed = []
    for line in rules.splitlines():
        for tok in token.findall(line):
            canon = name_registry.setdefault(tok, tok)
            if tok != canon:
                line = re.sub(rf'\b{tok}\b', canon, line)
        fixed.append(line)
    return "\n".join(fixed)

def translate_chunk(chunk: str) -> str:
    return chat([{"role": "system", "content": SYS_TRANSLATE},
                 {"role": "user",   "content": chunk}])

def normalise_rules(rules: str) -> str:
    return chat([{"role": "system", "content": SYS_NORMALISE},
                 {"role": "user",   "content": unify_names(rules)}])

# --------------------------- pipeline ------------------------------ #
def pdf_to_prolog(pdf_path: str):
    pdf_path = Path(pdf_path).expanduser().resolve()
    raw = extract_pdf_text(pdf_path)
    pieces = list(chunk_text(raw))

    print(f"📄  {len(pieces)} chunks to translate …")
    translated = [
        translate_chunk(chunk)
        for chunk in one_line_bar(pieces, desc="LLM translate", unit="chunk")
    ]

    print("🧹  Normalising & deduplicating …")
    final = normalise_rules("\n".join(translated))

    out_path = TARGET_DIR / f"{pdf_path.stem}{OUTPUT_SUFFIX}"
    out_path.write_text(final, encoding="utf-8")
    print(f"✔  Saved {out_path}")

# --------------------------- entry --------------------------------- #
if __name__ == "__main__":
    pdf_to_prolog(
        "/Users/lararusso/Canadian-Employee-Standards-Act---Prolog-Translation/"
        "Employee_Standards_Act/Employment_Standards_Act_ontario.ca.pdf"
    )
