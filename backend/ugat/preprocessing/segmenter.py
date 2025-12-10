def segmenter(text):
    sentences = []
    buffer = ""
    state = "READING"

    for ch in text:

        if state == "READING":
            if ch in ".!?":   # end of sentence
                buffer += ch
                state = "END"
            else:
                buffer += ch

        elif state == "END":
            if ch in " \n\t":   # whitespace after punctuation
                sentences.append(buffer.strip())
                buffer = ""
                state = "READING"
            else:
                # no whitespace → close sentence, but DO NOT add the ch into the previous sentence
                sentences.append(buffer.strip())
                buffer = ch     # start new sentence cleanly
                state = "READING"

    if buffer.strip():
        sentences.append(buffer.strip())

    return sentences