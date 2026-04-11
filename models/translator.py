from transformers import MarianMTModel, MarianTokenizer

loaded_models = {}

def get_model(source_lang, target_lang):
    model_name = f"Helsinki-NLP/opus-mt-{source_lang}-{target_lang}"

    if model_name not in loaded_models:
        tokenizer = MarianTokenizer.from_pretrained(model_name)
        model = MarianMTModel.from_pretrained(model_name)
        loaded_models[model_name] = (tokenizer, model)

    return loaded_models[model_name]


def translate_text(text, source_lang='en', target_lang='hi'):
    tokenizer, model = get_model(source_lang, target_lang)

    tokens = tokenizer(text, return_tensors="pt", padding=True)
    translated = model.generate(**tokens)
    result = tokenizer.decode(translated[0], skip_special_tokens=True)

    return result