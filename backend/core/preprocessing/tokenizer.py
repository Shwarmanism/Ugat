def tokenizer(sentence):
   
    punctuation = "?.,:;!"  # Punctuation to keep as separate tokens
    tokens = []
    buffer = ""

    for ch in sentence:
        if ch.isalpha():
            # Alphabetic character - add to buffer
            buffer += ch.lower()
        elif ch == '-':
            # Hyphen - keep with word if buffer has content (e.g., "nag-text")
            if buffer:
                buffer += ch
        else:
            # Non-alphabetic, non-hyphen character
            # Save any accumulated word (strip trailing hyphen if any)
            if buffer:
                tokens.append(buffer.rstrip('-'))
                buffer = ""
            
            # Keep only specific punctuation as separate tokens
            if ch in punctuation:
                tokens.append(ch)

    # Handle leftover buffer (strip trailing hyphen if any)
    if buffer:
        tokens.append(buffer.rstrip('-'))

    return tokens