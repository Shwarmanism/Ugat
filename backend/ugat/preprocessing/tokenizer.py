def tokenizer(sentence):
    tokens = []
    buffer = ""

    for ch in sentence:
        if ch.isalpha():
            buffer += ch.lower() 
        else:
            if buffer:
                tokens.append(buffer)
                buffer = ""

    if buffer:
        tokens.append(buffer)

    return tokens
