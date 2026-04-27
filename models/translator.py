import torch
import re
import logging
from functools import lru_cache
from transformers import (
    MarianMTModel,
    MarianTokenizer,
    AutoTokenizer,
    AutoModelForSeq2SeqLM
)

logger = logging.getLogger(__name__)

# ------------------ DEVICE ------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_num_threads(4)
#--- name----
# Languages that use non-Latin scripts — name extraction via ASCII regex
# is meaningless for these, and placeholder injection corrupts the output
# because the translation model either translates the placeholder literally
# or drops it, leaving raw __NAME0__ tokens in the final string.
_NON_LATIN_LANGS = {
    "hi", "bn", "ur", "ta", "te", "mr", "gu", "pa", "ml", "kn",
    "ne", "si", "as", "or", "sd", "ks", "kok", "mai", "bho", "sat",
    "doi", "mni",                          # Indian scripts
    "ar", "fa", "he",                      # Arabic / Hebrew
    "zh", "ja", "ko",                      # CJK
    "th", "my", "km", "lo",               # SE Asian scripts
    "am",                                  # Ethiopic
    "ru", "uk",                            # Cyrillic (capitals differ from Latin)
    "el",                                  # Greek
}


def _should_preserve_names(src: str, tgt: str) -> bool:
    """
    Return True only when both languages use Latin script and name
    preservation is safe.  For any non-Latin pair we skip substitution
    entirely to avoid __NAMEn__ token corruption in the output.
    """
    return src not in _NON_LATIN_LANGS and tgt not in _NON_LATIN_LANGS


def extract_names(text):
    # Detect words starting with capital letter (simple approach)
    return re.findall(r'\b[A-Z][a-z]+\b', text)


def replace_names(text, names):
    for i, name in enumerate(names):
        text = text.replace(name, f"__NAME{i}__")
    return text


def restore_names(text, names):
    for i, name in enumerate(names):
        text = text.replace(f"__NAME{i}__", name)
    # Safety net: strip any leftover placeholder tokens that the model
    # failed to preserve, so they never appear in the final output.
    text = re.sub(r'__NAME\d+__', '', text)
    text = re.sub(r'\s{2,}', ' ', text).strip()
    return text

# ------------------ CACHE ------------------
# Bounded LRU cache — evicts oldest entries beyond MAX_CACHE_SIZE to prevent
# unbounded memory growth in long-running server sessions.
_MAX_CACHE_SIZE = 2048

class _LRUCache:
    """Simple thread-unsafe LRU cache backed by an OrderedDict."""
    def __init__(self, maxsize: int):
        from collections import OrderedDict
        self._store: "OrderedDict[str, str]" = OrderedDict()
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
            self._store.popitem(last=False)   # evict oldest

cache = _LRUCache(_MAX_CACHE_SIZE)

# ------------------ QUANTIZATION ------------------
def quantize_model(model):
    """
    Apply dynamic quantization only on supported platforms.
    macOS often lacks the required quantization backend, so we skip it there.
    """
    if DEVICE.type == "cpu":
        try:
            # Check if quantization backend is available
            import platform
            system = platform.system()
            
            # Skip quantization on macOS to avoid NoQEngine error
            if system == "Darwin":
                print(f"Skipping quantization on macOS (not supported)")
                return model
            
            model = torch.quantization.quantize_dynamic(
                model,
                {torch.nn.Linear},
                dtype=torch.qint8
            )
            print("Model quantized successfully")
        except Exception as e:
            print(f"Quantization failed, using original model: {e}")
            # Return original model if quantization fails
            pass
    return model


# ------------------ TEXT CLEANING ------------------
def clean_text(text):
    text = re.sub(r"\s+([?.!,])", r"\1", text)
    text = re.sub(r"\s+", " ", text)
    return text.strip()


# ------------------ SENTENCE SPLIT ------------------
def split_sentences(text):
    return re.split(r'(?<=[.!?]) +', text)


# ------------------ MARIAN ------------------
MARIAN_MODELS = {
    # English ↔ Indian
    ("en", "hi"): "Helsinki-NLP/opus-mt-en-hi",
    ("hi", "en"): "Helsinki-NLP/opus-mt-hi-en",
    ("en", "bn"): "Helsinki-NLP/opus-mt-en-bn",
    ("bn", "en"): "Helsinki-NLP/opus-mt-bn-en",
    ("en", "ur"): "Helsinki-NLP/opus-mt-en-ur",
    ("ur", "en"): "Helsinki-NLP/opus-mt-ur-en",
    ("en", "ta"): "Helsinki-NLP/opus-mt-en-ta",
    ("ta", "en"): "Helsinki-NLP/opus-mt-ta-en",
    ("en", "te"): "Helsinki-NLP/opus-mt-en-te",
    ("te", "en"): "Helsinki-NLP/opus-mt-te-en",
    ("en", "mr"): "Helsinki-NLP/opus-mt-en-mr",
    ("mr", "en"): "Helsinki-NLP/opus-mt-mr-en",
    ("en", "gu"): "Helsinki-NLP/opus-mt-en-gu",
    ("gu", "en"): "Helsinki-NLP/opus-mt-gu-en",

    # English ↔ European
    ("en", "fr"): "Helsinki-NLP/opus-mt-en-fr",
    ("fr", "en"): "Helsinki-NLP/opus-mt-fr-en",
    ("en", "de"): "Helsinki-NLP/opus-mt-en-de",
    ("de", "en"): "Helsinki-NLP/opus-mt-de-en",
    ("en", "es"): "Helsinki-NLP/opus-mt-en-es",
    ("es", "en"): "Helsinki-NLP/opus-mt-es-en",
    ("en", "it"): "Helsinki-NLP/opus-mt-en-it",
    ("it", "en"): "Helsinki-NLP/opus-mt-it-en",
    ("en", "nl"): "Helsinki-NLP/opus-mt-en-nl",
    ("nl", "en"): "Helsinki-NLP/opus-mt-nl-en",
    ("en", "pt"): "Helsinki-NLP/opus-mt-en-pt",
    ("pt", "en"): "Helsinki-NLP/opus-mt-pt-en",
    ("en", "ru"): "Helsinki-NLP/opus-mt-en-ru",
    ("ru", "en"): "Helsinki-NLP/opus-mt-ru-en",
    ("en", "pl"): "Helsinki-NLP/opus-mt-en-pl",
    ("pl", "en"): "Helsinki-NLP/opus-mt-pl-en",

    # English ↔ Asian
    ("en", "zh"): "Helsinki-NLP/opus-mt-en-zh",
    ("zh", "en"): "Helsinki-NLP/opus-mt-zh-en",
    ("en", "ja"): "Helsinki-NLP/opus-mt-en-ja",
    ("ja", "en"): "Helsinki-NLP/opus-mt-ja-en",
    ("en", "ko"): "Helsinki-NLP/opus-mt-en-ko",
    ("ko", "en"): "Helsinki-NLP/opus-mt-ko-en",
    ("en", "vi"): "Helsinki-NLP/opus-mt-en-vi",
    ("vi", "en"): "Helsinki-NLP/opus-mt-vi-en",
    ("en", "id"): "Helsinki-NLP/opus-mt-en-id",
    ("id", "en"): "Helsinki-NLP/opus-mt-id-en",

    # English ↔ Middle East
    ("en", "ar"): "Helsinki-NLP/opus-mt-en-ar",
    ("ar", "en"): "Helsinki-NLP/opus-mt-ar-en",
    ("en", "fa"): "Helsinki-NLP/opus-mt-en-fa",
    ("fa", "en"): "Helsinki-NLP/opus-mt-fa-en",
    ("en", "he"): "Helsinki-NLP/opus-mt-en-he",
    ("he", "en"): "Helsinki-NLP/opus-mt-he-en",
}

marian_cache = {}

def load_marian(src, tgt):
    key = (src, tgt)

    if key not in marian_cache:
        model_name = MARIAN_MODELS[key]

        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)

        model = quantize_model(model)

        model.to(DEVICE)
        model.eval()

        marian_cache[key] = (tokenizer, model)

    return marian_cache[key]


def translate_marian(text, src, tgt):
    tokenizer, model = load_marian(src, tgt)

    inputs = tokenizer(
        text,
        return_tensors="pt",
        truncation=True,
        padding=True
    ).to(DEVICE)

    with torch.inference_mode():
        outputs = model.generate(
            **inputs,
            max_length=128,
            num_beams=2
        )

    return tokenizer.decode(outputs[0], skip_special_tokens=True)


# ------------------ NLLB ------------------
NLLB_MODEL = "facebook/nllb-200-distilled-600M"

# Lazy loading cache for NLLB
nllb_cache = {}

def load_nllb():
    """Load NLLB model lazily (only when first needed)"""
    if "model" not in nllb_cache:
        print("Loading NLLB (quantized)...")
        
        tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL)
        model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)
        
        model = quantize_model(model)
        model.to(DEVICE)
        model.eval()
        
        nllb_cache["tokenizer"] = tokenizer
        nllb_cache["model"] = model
        
        print("NLLB model loaded successfully!")
    
    return nllb_cache["tokenizer"], nllb_cache["model"]

LANG_CODE_MAP = {
    # Core
    "en": "eng_Latn",
    "hi": "hin_Deva",
    "fr": "fra_Latn",
    "de": "deu_Latn",
    "es": "spa_Latn",
    "ru": "rus_Cyrl",
    "zh": "zho_Hans",
    "ar": "arb_Arab",

    # Indian Languages (extended)
    "bn": "ben_Beng",
    "ur": "urd_Arab",
    "ta": "tam_Taml",
    "te": "tel_Telu",
    "mr": "mar_Deva",
    "gu": "guj_Gujr",
    "pa": "pan_Guru",
    "as": "asm_Beng",
    "or": "ory_Orya",
    "ml": "mal_Mlym",
    "kn": "kan_Knda",
    "sd": "snd_Arab",
    "ne": "npi_Deva",
    "si": "sin_Sinh",
    "ks": "kas_Arab",   # Kashmiri
    "kok": "gom_Deva",  # Konkani
    "mai": "mai_Deva",  # Maithili
    "bho": "bho_Deva",  # Bhojpuri
    "sat": "sat_Olck",  # Santali
    "doi": "doi_Deva",  # Dogri
    "mni": "mni_Beng",  # Manipuri (Meitei)

    # European
    "it": "ita_Latn",
    "nl": "nld_Latn",
    "pl": "pol_Latn",
    "sv": "swe_Latn",
    "fi": "fin_Latn",
    "da": "dan_Latn",
    "no": "nob_Latn",
    "cs": "ces_Latn",
    "el": "ell_Grek",
    "uk": "ukr_Cyrl",
    "hu": "hun_Latn",
    "ro": "ron_Latn",
    "pt": "por_Latn",

    # Asian
    "ja": "jpn_Jpan",
    "ko": "kor_Hang",
    "th": "tha_Thai",
    "vi": "vie_Latn",
    "id": "ind_Latn",
    "ms": "msa_Latn",
    "km": "khm_Khmr",
    "lo": "lao_Laoo",
    "my": "mya_Mymr",

    # Middle East
    "fa": "pes_Arab",
    "he": "heb_Hebr",

    # African
    "sw": "swh_Latn",
    "yo": "yor_Latn",
    "ig": "ibo_Latn",
    "ha": "hau_Latn",
    "am": "amh_Ethi",
    "zu": "zul_Latn",
    "xh": "xho_Latn",

    # Others
    "tr": "tur_Latn",
}


def translate_nllb(text, src, tgt):
    src_code = LANG_CODE_MAP.get(src)
    tgt_code = LANG_CODE_MAP.get(tgt)

    if not src_code or not tgt_code:
        return "Language not supported"

    # Load NLLB model lazily
    nllb_tokenizer, nllb_model = load_nllb()

    # Set the source language on the tokenizer so the encoder gets the right
    # language token.  AutoTokenizer returns an NllbTokenizer whose src_lang
    # attribute controls the BOS token injected during encoding.
    nllb_tokenizer.src_lang = src_code

    inputs = nllb_tokenizer(text, return_tensors="pt").to(DEVICE)

    # Resolve the target-language token id via convert_tokens_to_ids —
    # the correct API across all transformers versions.
    # lang_code_to_id is a legacy dict that does NOT exist on every build
    # and raises KeyError / AttributeError silently swallowed upstream.
    tgt_token_id = nllb_tokenizer.convert_tokens_to_ids(tgt_code)
    if tgt_token_id == nllb_tokenizer.unk_token_id:
        # Fallback: try the lang_code_to_id dict if it exists (older builds)
        tgt_token_id = getattr(nllb_tokenizer, "lang_code_to_id", {}).get(
            tgt_code, tgt_token_id
        )

    with torch.inference_mode():
        outputs = nllb_model.generate(
            **inputs,
            forced_bos_token_id=tgt_token_id,
            max_length=128,
            num_beams=2
        )

    return nllb_tokenizer.decode(outputs[0], skip_special_tokens=True)


# ------------------ MAIN FUNCTION ------------------
def translate_text(text, source_lang="en", target_lang="hi"):
    if not text or not text.strip():
        return ""

    source_lang = source_lang.lower()
    target_lang = target_lang.lower()

    # ------------------ NAME HANDLING ------------------
    # Only preserve names when both languages use Latin script.
    # For non-Latin pairs the placeholder approach corrupts the output.
    use_name_preservation = _should_preserve_names(source_lang, target_lang)
    names = extract_names(text) if use_name_preservation else []
    if names:
        text = replace_names(text, names)

    # ------------------ CLEAN + SPLIT ------------------
    text = clean_text(text)
    sentences = split_sentences(text)

    translated_sentences = []

    for sentence in sentences:
        if not sentence.strip():
            continue

        key = f"{source_lang}-{target_lang}-{sentence}"

        if cache.get(key) is not None:
            translated = cache.get(key)
        else:
            if (source_lang, target_lang) in MARIAN_MODELS:
                try:
                    translated = translate_marian(sentence, source_lang, target_lang)
                except Exception as marian_err:
                    # Model may not exist on HuggingFace Hub (e.g. en↔bn, en↔mr,
                    # en↔gu, en↔te, en↔ta).  Fall back to NLLB silently.
                    logger.warning(
                        "Marian failed for (%s→%s), falling back to NLLB: %s",
                        source_lang, target_lang, marian_err
                    )
                    translated = translate_nllb(sentence, source_lang, target_lang)
            else:
                translated = translate_nllb(sentence, source_lang, target_lang)

            cache.set(key, translated)

        translated_sentences.append(translated)

    # ------------------ JOIN RESULT ------------------
    result = " ".join(translated_sentences)

    # ------------------ RESTORE NAMES ------------------
    if names:
        result = restore_names(result, names)
    else:
        # Still run the safety-net strip in case any stray tokens slipped through
        result = re.sub(r'__NAME\d+__', '', result)
        result = re.sub(r'\s{2,}', ' ', result).strip()

    return result