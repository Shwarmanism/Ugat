from ugat import tokenizer, segmenter


def text_preprocess(raw_text, lang):
    processed_text = []

    sentences = segmenter(raw_text)

    for sentence in sentences:
        tokens = tokenizer(sentence)
        processed_text.append(tokens)

    return {
        "lang" : lang,
        "sentences": processed_text
    }

def pos_tagging():
    print("")

def morph_rules(tokens):
    print("")
    
if __name__ == "__main__":

    text = "Hello! Kumusta ka? Kain tayo."
    lang = "Hiligaynon"

    result = text_preprocess(text, lang)

    print(result)