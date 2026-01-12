def tokenizer(sentence):
    punctuation = "?.,:;!"  # Define which punctuation to keep
    tokens = []
    buffer = ""

    for ch in sentence:
        if ch.isalpha():
            buffer += ch.lower()
        else:
            # Save any accumulated word
            if buffer:
                tokens.append(buffer)
                buffer = ""
            
            # Keep only specific punctuation as separate tokens
            if ch in punctuation:
                tokens.append(ch)

    # leftover
    if buffer:
        tokens.append(buffer)

    return tokens