import re

def data_preprocessing(text):
    sentences = []
    buffer = ""
    state = "READING"  

    #--------Sentence Segmentation----------
    for ch in text:
        buffer += ch

        if state == "READING":
            if ch in ".!?":
                state = "END"

        elif state == "END":
            if ch == " ":
               
                sentences.append(buffer.strip())
                buffer = ""
                state = "READING"


    if buffer.strip():
        sentences.append(buffer.strip())

    # -- TOKENIZATION PROCESS --
    tokenized_sentences = []
    for sentence in sentences:
        # Remove numbers and punctuation
        clean_sentence = re.sub(r"[^a-zA-ZñÑ\s]", "", sentence)
        # Tokenize by spaces and lowercase
        tokens = clean_sentence.lower().split()
        if tokens:
            tokenized_sentences.append(tokens)

    return tokenized_sentences