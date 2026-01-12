import os
from sklearn_crfsuite import CRF
from sklearn_crfsuite.metrics import flat_classification_report
from sklearn.model_selection import train_test_split

# ----------------------------
# Config
# ----------------------------
INPUT_FILE = "Cebuano_crf_formatted.txt"
EXPECTED_COLUMNS = 7  # token + 5 features + label
SENTENCE_END_PUNCT = {".", "!", "?"}  # punctuation indicating sentence boundary

# ----------------------------
# Loader
# ----------------------------
def load_crf_data(file_path):
    sentences = []
    labels = []
    sentence = []
    sentence_labels = []

    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File not found: {file_path}")

    with open(file_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue

            cols = line.split('\t')  # tab-delimited
            if len(cols) != EXPECTED_COLUMNS:
                print(f"Skipped misaligned row: {line}")
                continue

            token = cols[0]
            features = cols[1:-1]
            label = cols[-1]

            # Create feature dictionary for CRF
            token_features = {'token': token, 'lower': token.lower()}
            for i, feat in enumerate(features):
                token_features[f'feat{i}'] = feat

            sentence.append(token_features)
            sentence_labels.append(label)

            # Detect sentence boundary (punctuation)
            if token in SENTENCE_END_PUNCT:
                sentences.append(sentence)
                labels.append(sentence_labels)
                sentence = []
                sentence_labels = []

    # Append any remaining tokens as a sentence
    if sentence:
        sentences.append(sentence)
        labels.append(sentence_labels)

    print(f"Loaded {len(sentences)} sentences")
    return sentences, labels

# ----------------------------
# Load Dataset
# ----------------------------
X, y = load_crf_data(INPUT_FILE)

if not X:
    raise ValueError("No sentences loaded. Check dataset formatting.")

# ----------------------------
# Train/Test Split
# ----------------------------
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# ----------------------------
# Train CRF
# ----------------------------
crf = CRF(
    algorithm='lbfgs',
    max_iterations=100,
    all_possible_transitions=True
)
crf.fit(X_train, y_train)

# ----------------------------
# Evaluate
# ----------------------------
y_pred = crf.predict(X_test)
print(flat_classification_report(y_test, y_pred))


