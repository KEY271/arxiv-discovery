import os
import re
import json5
import feedparser
from sentence_transformers import SentenceTransformer
import numpy as np
from pylatexenc.latex2text import LatexNodes2Text
import unicodedata

def load_settings() -> dict:
    if not os.path.exists("settings.json5"):
        raise FileNotFoundError("settings.json5 not found. Copy settings.example.json5 to settings.json5 and configure it.")
    with open("settings.json5", "r") as f:
        config = json5.load(f)
    return config

class Entry:
    def __init__(self, title: str, link: str, summary: str, authors: list[str]):
        self.title = title
        self.link = link
        self.summary = summary
        self.authors = authors

def normalize_text(text: str, L2T: LatexNodes2Text) -> str:
    text = L2T.latex_to_text(text)
    text = unicodedata.normalize("NFC", text)
    return json5.dumps(text, ensure_ascii=False)

def fetch_feeds(config) -> list[Entry]:
    L2T = LatexNodes2Text(math_mode="verbatim")
    entries = []
    seen_links = set()
    for url in config["feeds"]:
        feed = feedparser.parse(url, sanitize_html=False)
        for entry in feed.entries:
            announce_type = entry.get("arxiv_announce_type", "")
            link = entry["link"].strip()
            if link in seen_links:
                continue
            if announce_type == "new" or announce_type == "cross":
                desc = normalize_text(entry["description"].split("Abstract:")[-1].strip(), L2T)
                authors = [normalize_text(author.strip(), L2T) for author in entry.get("author", "").split(",")]
                entries.append(Entry(normalize_text(entry["title"].strip(), L2T), entry["link"].strip(), desc, authors))
                seen_links.add(link)
    return entries

def create_preference_vector(config, model: SentenceTransformer) -> np.ndarray:
    vecs = []
    w = config.get("weights", { "keywords": 10, "liked_texts": 10, "trusted_authors": 30 })
    if config.get("keywords"):
        kw_vecs = model.encode(config.get("keywords", []), normalize_embeddings=True)
        vecs.append((np.mean(kw_vecs, axis=0), w.get("keywords", 1.0) / len(kw_vecs)))
    if config.get("liked_texts"):
        liked_vecs = model.encode(config.get("liked_texts", []), normalize_embeddings=True)
        vecs.append((np.mean(liked_vecs, axis=0), w.get("liked_texts", 1.0) / len(liked_vecs)))
    vec = np.zeros_like(vecs[0][0])
    for v, ww in vecs:
        vec += v * ww
    return vec

def rank_papers(config, model: SentenceTransformer, entries: list[Entry], vec: np.ndarray) -> list[tuple[float, bool, Entry]]:
    texts = [entry.title + " " + entry.summary for entry in entries]
    paper_vecs = model.encode(texts, normalize_embeddings=True)
    trusted_authors = set(config.get("trusted_authors", []))

    results = []
    for entry, v in zip(entries, paper_vecs):
        score = float(np.dot(vec, v))
        is_trusted = False
        if trusted_authors.intersection(set(entry.authors)):
            score += config.get("trusted_authors_bonus", 0)
            is_trusted = True
        results.append((score, is_trusted, entry))
    results.sort(key=lambda x: x[0], reverse=True)
    return results

def write_results(results: list[tuple[float, bool, Entry]]):
    with open("results.json5", "w") as f:
        f.write("[\n")
        for score, is_trusted, entry in results:
            f.write("  {\n")
            f.write(f"    score: {score:.4f},\n")
            f.write(f"    title: {entry.title},\n")
            f.write(f"    link: \"{entry.link}\",\n")
            f.write(f"    authors: [{', '.join(f'{x}' for x in entry.authors)}],\n")
            f.write(f"    summary: {entry.summary},\n")
            f.write("  },\n")
        f.write("]\n")

def main():
    print("Loading settings...", end="", flush=True)
    config = load_settings()
    print("Done.")

    print("Loading model...", end="", flush=True)
    model = SentenceTransformer('all-MiniLM-L6-v2')
    print("Done.")

    print("Fetching new entries from feeds...", end="", flush=True)
    entries = fetch_feeds(config)
    print("Done.")
    print("Total new entries fetched:", len(entries))

    print("Preparing preference vector...", end="", flush=True)
    pref_vector = create_preference_vector(config, model)
    print("Done.")

    print("Scoring and ranking entries...", end="", flush=True)
    results = rank_papers(config, model, entries, pref_vector)
    print("Done.")

    print("Writing results to results.json5...", end="", flush=True)
    write_results(results)
    print("Done.")

if __name__ == "__main__":
    main()
