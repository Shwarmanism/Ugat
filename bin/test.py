import csv

# CONFIG: adjust according to your dataset
INPUT_FILE = "ilocano_crf.txt"
OUTPUT_FILE = "ilocano_dataset_cleaned.txt"
EXPECTED_COLUMNS = 7  # Number of columns per token row

def clean_crf_dataset(input_file, output_file, expected_columns):
    cleaned_rows = []
    misaligned_rows = []

    with open(input_file, "r", encoding="utf-8") as f:
        for i, line in enumerate(f, 1):
            line = line.strip()
            
            # Skip empty lines
            if not line:
                continue
            
            cols = line.split()  # Split by whitespace
            if len(cols) != expected_columns:
                misaligned_rows.append((i, line, len(cols)))
                continue  # Skip misaligned row
            
            cleaned_rows.append(cols)

    # Write cleaned dataset
    with open(output_file, "w", encoding="utf-8") as f_out:
        for row in cleaned_rows:
            f_out.write("\t".join(row) + "\n")

    # Report
    print(f"Total rows processed: {i}")
    print(f"Total cleaned rows: {len(cleaned_rows)}")
    print(f"Total misaligned rows skipped: {len(misaligned_rows)}\n")

    if misaligned_rows:
        print("Misaligned rows:")
        for row_info in misaligned_rows:
            line_num, content, col_count = row_info
            print(f"Line {line_num} | Columns: {col_count} | Content: {content}")

    print(f"\nCleaned dataset written to: {output_file}")


if __name__ == "__main__":
    clean_crf_dataset(INPUT_FILE, OUTPUT_FILE, EXPECTED_COLUMNS)
