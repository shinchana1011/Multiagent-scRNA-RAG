# src/rag/llm_extractor.py — local LLM extraction via Ollama (Member 2)
from __future__ import annotations

import json
from openai import OpenAI
from loguru import logger

# Ollama runs a local OpenAI-compatible server — no API key, no billing
_client = OpenAI(base_url="http://localhost:11434/v1", api_key="ollama")

_PROMPT = """You are extracting scRNA-seq analysis parameters from methods text.

From the text below, extract these three parameters IF explicitly stated:
- mito_pct: the mitochondrial percentage cutoff for QC (a number)
- n_pcs: the number of principal components used (an integer)
- resolution: the Leiden/Louvain clustering resolution (a number)

Return ONLY a JSON object, no other text. For any parameter not explicitly
stated, use null. Example: {"mito_pct": 10, "n_pcs": 30, "resolution": 0.5}

TEXT:
{chunks}
"""


def extract_parameters_llm(chunks: list[str], model: str = "llama3.1") -> dict:
    """Extract parameters using a local Ollama model. Returns {} on failure,
    so the recommender's regex fallback takes over."""
    joined = "\n\n---\n\n".join(chunks[:5])
    try:
        resp = _client.chat.completions.create(
            model=model,
            messages=[{"role": "user", "content": _PROMPT.replace("{chunks}", joined)}],
            temperature=0,
        )
        text = resp.choices[0].message.content.strip()
        text = text.replace("```json", "").replace("```", "").strip()
        parsed = json.loads(text)
        logger.info("LLM extracted: {}", parsed)
        return parsed
    except Exception as e:
        logger.warning("LLM extraction failed ({}); falling back to regex", e)
        return {}