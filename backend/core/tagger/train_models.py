import os
import pickle

from sklearn_crfsuite import CRF
from sklearn_crfsuite.metrics import flat_classification_report
from sklearn.model_selection import train_test_split


# ----------------------------
# Config
# ----------------------------
EXPECTED_COLUMNS = 7  # token + 5 features + label
SENTENCE_END_PUNCT = {".", "!", "?"}  # punctuation indicating sentence boundary


def load_crf_data(file_path: str):
    """
    Load CRF data from a tab-delimited file.

    Each non-empty line is expected to have:
        token, feat1, feat2, feat3, feat4, feat5, label
    """
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

            cols = line.split("\t")
            if len(cols) != EXPECTED_COLUMNS:
                # Skip malformed rows quietly; data was mostly cleaned already.
                continue

            token = cols[0]
            features = cols[1:-1]
            label = cols[-1]

            # Basic token features
            token_features = {"token": token, "lower": token.lower()}
            for i, feat in enumerate(features):
                token_features[f"feat{i}"] = feat

            sentence.append(token_features)
            sentence_labels.append(label)

            # Sentence boundary
            if token in SENTENCE_END_PUNCT:
                sentences.append(sentence)
                labels.append(sentence_labels)
                sentence = []
                sentence_labels = []

    if sentence:
        sentences.append(sentence)
        labels.append(sentence_labels)

    print(f"Loaded {len(sentences)} sentences from {file_path}")
    return sentences, labels


def train_and_save_model(data_file: str, model_path: str):
    """
    Train a CRF model on the given data file and save it as a pickle.
    """
    print("=" * 60)
    print(f"Training model from {data_file}")

    X, y = load_crf_data(data_file)
    if not X:
        raise ValueError(f"No sentences loaded from {data_file}. Check formatting.")

    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    crf = CRF(
        algorithm="lbfgs",
        max_iterations=100,
        all_possible_transitions=True,
    )
    crf.fit(X_train, y_train)

    y_pred = crf.predict(X_test)
    print(flat_classification_report(y_test, y_pred))

    with open(model_path, "wb") as f:
        pickle.dump(crf, f)

    print(f"Saved model to {model_path}")


def main():
    # Map language to (data file, model file)
    configs = {
        "cebuano": ("Cebuano_crf_formatted.txt", "cebuano_model.pkl"),
        "ilocano": ("ilocano_crf_formatted.txt", "ilocano_model.pkl"),
    }

    for lang, (data_file, model_file) in configs.items():
        print("=" * 60)
        print(f"=== Training {lang.capitalize()} model ===")
        train_and_save_model(data_file, model_file)

    print("\nDone training Cebuano and Ilocano models.")


if __name__ == "__main__":
    main()


