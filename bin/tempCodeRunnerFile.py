import os
from sklearn_crfsuite import CRF
from sklearn_crfsuite.metrics import flat_classification_report
from sklearn.model_selection import train_test_split

# ----------------------------
# Config
# ----------------------------
INPUT_FILE = "ilocano_dataset_cleaned.txt"
EXPECTED_COLUMNS = 7  # token + 5 features + label

# ----------------------------
# Loader
# ----------------------------
def load_crf_data(file_path):
    sentences = []
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
            features = cols[1:-1]  # columns 1-5
            label = cols[-1]

            # Minimal features for CRF
            token_features = {
                'token': token,
                'lower': token.lower()
            }
            for i, feat in enumerate(features):
                token_features[f'feat{i}'] = feat

            sentence.append(token_features)
            sentence_labels.append(label)

            # Sentence boundary
            if label == "EOS":
                sentences.append(sentence)
                sentence_labels[-1] = 'PUNCT'  # optionally replace EOS with PUNCT
                sentences[-1][-1]['EOS'] = True
                sentences[-1][-1]['token'] = '.'  # optional
                sentence_labels = sentence_labels[:-1] + ['PUNCT']
                sentence_labels_final = sentence_labels
                sentence_labels = []

                # Append the sentence labels correctly
                sentences[-1] = sentence
                sentence_labels = sentence_labels_final
                sentence = []

    print(f"Loaded {len(sentences)} sentences")
    return sentences, sentences_labels_final  # X, y

# ----------------------------
# Feature Conversion Helper
# ----------------------------
def convert_X_y(sentences, labels):
    X = sentences
    y = labels
    return X, y

# ----------------------------
# Load Dataset
# ----------------------------
# Note: Make sure your dataset uses tabs, has EOS in last column
X, y = load_crf_data(INPUT_FILE)

if not X:
    raise ValueError("No sentences loaded. Check dataset formatting and EOS labels.")

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
