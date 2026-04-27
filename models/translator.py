"""
models/translator.py
Translation pipeline — memory-optimised for ≤512 MB environments.

Priority per request:
  1. Groq LLaMA API        (zero local RAM — preferred)
  2. Marian MT (local)     (≈300 MB per model, loaded + unloaded per request)
  3. NLLB-distilled-600M   (≈1.2 GB — last resort, unloaded immediately after use)

Key memory rules:
  - No model is kept in a global cache between requests.
  - Every local model is deleted and gc.collect() called after use.
  - torch.set_num_threads(1) to avoid spawning extra threads.
  - Translation result cache is capped at 512 entries (strings only, no tensors).
"""
import re
import gc
import os
import logging
from collections import OrderedDict

logger = logging.getLogger(__name__)

# ── Result cache (strings only — no tensors) ─────────────────────────────────
_MAX_CACHE = 512

class _LRUCache:
    def __init__(self, maxsize: int):
        self._store: OrderedDict = OrderedDict()
        self._maxsize = maxsize

    def get(self, key: str):
        if key not in self._store:
            return None
        self._store.move_to_end(key)
        return self._store[key]

    def set(self, key: str, value: str):
        if key in self._store:
            self._store.move_to_end(key)
        self._store[key] = value
        if len(self._store) > self._maxsize:
            self._store.popitem(last=False)

_cache = _LRUCache(_MAX_CACHE)

# ── Non-Latin script set (name preservation unsafe) ──────────────────────────
_NON_LATIN = {
    "hi","bn","ur","ta","te","mr","gu","pa","ml","kn","ne","si",
    "as","or","sd","ks","kok","mai","bho","sat","doi","mni",
    "ar","fa","he","zh","ja","ko","th","my","km","lo","am","ru","uk","el",
}

# ── NLLB language code map ────────────────────────────────────────────────────
_NLLB_CODES = {
    "en":"eng_Latn","hi":"hin_Deva","fr":"fra_Latn","de":"deu_Latn",
    "es":"spa_Latn","ru":"rus_Cyrl","zh":"zho_Hans","ar":"arb_Arab",
    "bn":"ben_Beng","ur":"urd_Arab","ta":"tam_Taml","te":"tel_Telu",
    "mr":"mar_Deva","gu":"guj_Gujr","pa":"pan_Guru","as":"asm_Beng",
    "or":"ory_Orya","ml":"mal_Mlym","kn":"kan_Knda","sd":"snd_Arab",
    "ne":"npi_Deva","si":"sin_Sinh","ks":"kas_Arab","kok":"gom_Deva",
    "mai":"mai_Deva","bho":"bho_Deva","sat":"sat_Olck","doi":"doi_Deva",
    "mni":"mni_Beng","it":"ita_Latn","nl":"nld_Latn","pl":"pol_Latn",
    "sv":"swe_Latn","fi":"fin_Latn","da":"dan_Latn","no":"nob_Latn",
    "cs":"ces_Latn","el":"ell_Grek","uk":"ukr_Cyrl","hu":"hun_Latn",
    "ro":"ron_Latn","pt":"por_Latn","ja":"jpn_Jpan","ko":"kor_Hang",
    "th":"tha_Thai","vi":"vie_Latn","id":"ind_Latn","ms":"msa_Latn",
    "km":"khm_Khmr","lo":"lao_Laoo","my":"mya_Mymr","fa":"pes_Arab",
    "he":"heb_Hebr","sw":"swh_Latn","yo":"yor_Latn","ig":"ibo_Latn",
    "ha":"hau_Latn","am":"amh_Ethi","zu":"zul_Latn","xh":"xho_Latn",
    "tr":"tur_Latn",
}

# ── Marian model names ────────────────────────────────────────────────────────
_MARIAN_MODELS = {
    ("en","hi"):"Helsinki-NLP/opus-mt-en-hi", ("hi","en"):"Helsinki-NLP/opus-mt-hi-en",
    ("en","fr"):"Helsinki-NLP/opus-mt-en-fr", ("fr","en"):"Helsinki-NLP/opus-mt-fr-en",
    ("en","de"):"Helsinki-NLP/opus-mt-en-de", ("de","en"):"Helsinki-NLP/opus-mt-de-en",
    ("en","es"):"Helsinki-NLP/opus-mt-en-es", ("es","en"):"Helsinki-NLP/opus-mt-es-en",
    ("en","it"):"Helsinki-NLP/opus-mt-en-it", ("it","en"):"Helsinki-NLP/opus-mt-it-en",
    ("en","nl"):"Helsinki-NLP/opus-mt-en-nl", ("nl","en"):"Helsinki-NLP/opus-mt-nl-en",
    ("en","pt"):"Helsinki-NLP/opus-mt-en-pt", ("pt","en"):"Helsinki-NLP/opus-mt-pt-en",
    ("en","ru"):"Helsinki-NLP/opus-mt-en-ru", ("ru","en"):"Helsinki-NLP/opus-mt-ru-en",
    ("en","pl"):"Helsinki-NLP/opus-mt-en-pl", ("pl","en"):"Helsinki-NLP/opus-mt-pl-en",
    ("en","zh"):"Helsinki-NLP/opus-mt-en-zh", ("zh","en"):"Helsinki-NLP/opus-mt-zh-en",
    ("en","ja"):"Helsinki-NLP/opus-mt-en-ja", ("ja","en"):"Helsinki-NLP/opus-mt-ja-en",
    ("en","ko"):"Helsinki-NLP/opus-mt-en-ko", ("ko","en"):"Helsinki-NLP/opus-mt-ko-en",
    ("en","vi"):"Helsinki-NLP/opus-mt-en-vi", ("vi","en"):"Helsinki-NLP/opus-mt-vi-en",
    ("en","id"):"Helsinki-NLP/opus-mt-en-id", ("id","en"):"Helsinki-NLP/opus-mt-id-en",
    ("en","ar"):"Helsinki-NLP/opus-mt-en-ar", ("ar","en"):"Helsinki-NLP/opus-mt-ar-en",
    ("en","fa"):"Helsinki-NLP/opus-mt-en-fa", ("fa","en"):"Helsinki-NLP/opus-mt-fa-en",
    ("en","he"):"Helsinki-NLP/opus-mt-en-he", ("he","en"):"Helsinki-NLP/opus-mt-he-en",
    ("en","ur"):"Helsinki-NLP/opus-mt-en-ur", ("ur","en"):"Helsinki-NLP/opus-mt-ur-en",
    ("en","ta"):"Helsinki-NLP/opus-mt-en-ta", ("ta","en"):"Helsinki-NLP/opus-mt-ta-en",
    ("en","te"):"Helsinki-NLP/opus-mt-en-te", ("te","en"):"Helsinki-NLP/opus-mt-te-en",
    ("en","mr"):"Helsinki-NLP/opus-mt-en-mr", ("mr","en"):"Helsinki-NLP/opus-mt-mr-en",
    ("en","bn"):"Helsinki-NLP/opus-mt-en-bn", ("bn","en"):"Helsinki-NLP/opus-mt-bn-en",
    ("en","gu"):"Helsinki-NLP/opus-mt-en-gu", ("gu","en"):"Helsinki-NLP/opus-mt-gu-en",
}

# ── Text helpers ──────────────────────────────────────────────────────────────

def _clean(text: str) -> str:
    text = re.sub(r"\s+([?.!,])", r"\1", text)
    return re.sub(r"\s+", " ", text).strip()

def _split(text: str):
    return re.split(r'(?<=[.!?]) +', text)

def _extract_names(text: str):
    return re.findall(r'\b[A-Z][a-z]+\b', text)

def _replace_names(text: str, names) -> str:
    for i, n in enumerate(names):
        text = text.replace(n, f"__N{i}__")
    return text

def _restore_names(text: str, names) -> str:
    for i, n in enumerate(names):
        text = text.replace(f"__N{i}__", n)
    text = re.sub(r'__N\d+__', '', text)
    return re.sub(r'\s{2,}', ' ', text).strip()

# ── Groq translation (API — no local RAM) ────────────────────────────────────

_GROQ_LANG_MAP = {
    "en":"English","hi":"Hindi","fr":"French","de":"German","es":"Spanish",
    "zh":"Chinese","ar":"Arabic","ru":"Russian","it":"Italian","pt":"Portuguese",
    "ja":"Japanese","ko":"Korean","bn":"Bengali","ur":"Urdu","ta":"Tamil",
    "te":"Telugu","mr":"Marathi","gu":"Gujarati","pa":"Punjabi","nl":"Dutch",
    "pl":"Polish","sv":"Swedish","fi":"Finnish","da":"Danish","no":"Norwegian",
    "cs":"Czech","el":"Greek","uk":"Ukrainian","hu":"Hungarian","ro":"Romanian",
    "th":"Thai","vi":"Vietnamese","id":"Indonesian","ms":"Malay","fa":"Persian",
    "he":"Hebrew","sw":"Swahili","tr":"Turkish","ne":"Nepali","si":"Sinhala",
    "ml":"Malayalam","kn":"Kannada",
}

def _groq_translate(text: str, src: str, tgt: str) -> str:
    from groq import Groq
    client = Groq(api_key=os.getenv("GROQ_API_KEY", ""))
    source = _GROQ_LANG_MAP.get(src, src)
    target = _GROQ_LANG_MAP.get(tgt, tgt)
    resp = client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=[
            {"role": "system", "content": "You are an expert multilingual translator. Output only the translated text."},
            {"role": "user",   "content": f"Translate from {source} to {target}:\n{text}"},
        ],
        temperature=0.1,
        max_tokens=1024,
    )
    return resp.choices[0].message.content.strip()

# ── Marian local (load → use → unload) ───────────────────────────────────────

def _marian_translate(text: str, src: str, tgt: str) -> str:
    """Load Marian model, translate one sentence, unload immediately."""
    import torch
    from transformers import MarianMTModel, MarianTokenizer

    torch.set_num_threads(1)
    model_name = _MARIAN_MODELS[(src, tgt)]
    logger.info("[Marian] Loading %s (will unload after use)", model_name)

    tokenizer = MarianTokenizer.from_pretrained(model_name)
    model     = MarianMTModel.from_pretrained(model_name)
    model.eval()

    try:
        inputs = tokenizer(text, return_tensors="pt", truncation=True, padding=True)
        with torch.inference_mode():
            out = model.generate(**inputs, max_length=256, num_beams=2)
        result = tokenizer.decode(out[0], skip_special_tokens=True)
    finally:
        del model, tokenizer, inputs
        gc.collect()
        logger.info("[Marian] Model unloaded.")

    return result

# ── NLLB local fallback (load → use → unload) ────────────────────────────────

def _nllb_translate(text: str, src: str, tgt: str) -> str:
    """Load NLLB-distilled-600M, translate, unload immediately."""
    import torch
    from transformers import AutoTokenizer, AutoModelForSeq2SeqLM

    src_code = _NLLB_CODES.get(src)
    tgt_code = _NLLB_CODES.get(tgt)
    if not src_code or not tgt_code:
        return "Language not supported"

    torch.set_num_threads(1)
    logger.info("[NLLB] Loading facebook/nllb-200-distilled-600M (will unload after use)…")

    tokenizer = AutoTokenizer.from_pretrained("facebook/nllb-200-distilled-600M")
    model     = AutoModelForSeq2SeqLM.from_pretrained("facebook/nllb-200-distilled-600M")
    model.eval()

    try:
        tokenizer.src_lang = src_code
        inputs = tokenizer(text, return_tensors="pt")
        tgt_id = tokenizer.convert_tokens_to_ids(tgt_code)
        if tgt_id == tokenizer.unk_token_id:
            tgt_id = getattr(tokenizer, "lang_code_to_id", {}).get(tgt_code, tgt_id)

        with torch.inference_mode():
            out = model.generate(**inputs, forced_bos_token_id=tgt_id, max_length=256, num_beams=2)
        result = tokenizer.decode(out[0], skip_special_tokens=True)
    finally:
        del model, tokenizer, inputs
        gc.collect()
        logger.info("[NLLB] Model unloaded.")

    return result

# ── Public entry point ────────────────────────────────────────────────────────

def translate_text(text: str, source_lang: str = "en", target_lang: str = "hi") -> str:
    """
    Translate text using a 3-tier fallback pipeline:
      1. Groq API (no local RAM)
      2. Marian MT (local, load+unload per call)
      3. NLLB-600M (local, load+unload per call — last resort)

    Results are cached by (src, tgt, sentence) to avoid redundant API calls.
    """
    if not text or not text.strip():
        return ""

    src = source_lang.lower().strip()
    tgt = target_lang.lower().strip()

    if src == tgt:
        return text

    # Name preservation (Latin-script pairs only)
    use_names = src not in _NON_LATIN and tgt not in _NON_LATIN
    names = _extract_names(text) if use_names else []
    if names:
        text = _replace_names(text, names)

    text = _clean(text)
    sentences = _split(text)
    translated_parts = []

    groq_key = os.getenv("GROQ_API_KEY", "").strip()

    for sentence in sentences:
        sentence = sentence.strip()
        if not sentence:
            continue

        cache_key = f"{src}|{tgt}|{sentence}"
        cached = _cache.get(cache_key)
        if cached is not None:
            translated_parts.append(cached)
            continue

        result = None

        # ── Tier 1: Groq API ─────────────────────────────────────────────────
        if groq_key:
            try:
                result = _groq_translate(sentence, src, tgt)
                logger.debug("[Translate] Groq succeeded for %s→%s", src, tgt)
            except Exception as e:
                logger.warning("[Translate] Groq failed (%s), trying local.", e)

        # ── Tier 2: Marian (if Groq failed or unavailable) ───────────────────
        if result is None and (src, tgt) in _MARIAN_MODELS:
            try:
                result = _marian_translate(sentence, src, tgt)
                logger.debug("[Translate] Marian succeeded for %s→%s", src, tgt)
            except Exception as e:
                logger.warning("[Translate] Marian failed (%s), trying NLLB.", e)

        # ── Tier 3: NLLB (last resort) ────────────────────────────────────────
        if result is None:
            try:
                result = _nllb_translate(sentence, src, tgt)
                logger.debug("[Translate] NLLB succeeded for %s→%s", src, tgt)
            except Exception as e:
                logger.error("[Translate] All tiers failed for %s→%s: %s", src, tgt, e)
                result = f"[Translation failed: {e}]"

        _cache.set(cache_key, result)
        translated_parts.append(result)

    joined = " ".join(translated_parts)

    if names:
        joined = _restore_names(joined, names)
    else:
        joined = re.sub(r'__N\d+__', '', joined)
        joined = re.sub(r'\s{2,}', ' ', joined).strip()

    return joined
