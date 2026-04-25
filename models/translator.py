import torch
import re
from transformers import (
    MarianMTModel,
    MarianTokenizer,
    AutoTokenizer,
    AutoModelForSeq2SeqLM
)

# ------------------ DEVICE ------------------
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
torch.set_num_threads(4)
#--- name----
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
    return text

# ------------------ CACHE ------------------
cache = {}

# ------------------ QUANTIZATION ------------------
def quantize_model(model):
    if DEVICE.type == "cpu":
        model = torch.quantization.quantize_dynamic(
            model,
            {torch.nn.Linear},
            dtype=torch.qint8
        )
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

print("Loading NLLB (quantized)...")

nllb_tokenizer = AutoTokenizer.from_pretrained(NLLB_MODEL)
nllb_model = AutoModelForSeq2SeqLM.from_pretrained(NLLB_MODEL)

nllb_model = quantize_model(nllb_model)

nllb_model.to(DEVICE)
nllb_model.eval()

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

    inputs = nllb_tokenizer(text, return_tensors="pt").to(DEVICE)

    with torch.inference_mode():
        outputs = nllb_model.generate(
            **inputs,
            forced_bos_token_id=nllb_tokenizer.lang_code_to_id[tgt_code],
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
    names = extract_names(text)
    text = replace_names(text, names)

    # ------------------ CLEAN + SPLIT ------------------
    text = clean_text(text)
    sentences = split_sentences(text)

    translated_sentences = []

    for sentence in sentences:
        if not sentence.strip():
            continue

        key = f"{source_lang}-{target_lang}-{sentence}"

        if key in cache:
            translated = cache[key]
        else:
            if (source_lang, target_lang) in MARIAN_MODELS:
                translated = translate_marian(sentence, source_lang, target_lang)
            else:
                translated = translate_nllb(sentence, source_lang, target_lang)

            cache[key] = translated

        translated_sentences.append(translated)

    # ------------------ JOIN RESULT ------------------
    result = " ".join(translated_sentences)

    # ------------------ RESTORE NAMES ------------------
    result = restore_names(result, names)

    return result