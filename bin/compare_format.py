#!/usr/bin/env python3
"""Compare the format of reference and formatted files."""

with open('ilocano_dataset_cleaned.txt', 'r', encoding='utf-8') as f:
    ref_line = f.readline().rstrip('\r\n')
    
with open('ilocano_crf_formatted.txt', 'r', encoding='utf-8') as f:
    formatted_line = f.readline().rstrip('\r\n')

print("Reference file (first line):")
print(repr(ref_line))
print("\nFormatted file (first line):")
print(repr(formatted_line))
print("\nAre they the same?", ref_line == formatted_line)
print("\nReference parts:", ref_line.split('\t'))
print("Formatted parts:", formatted_line.split('\t'))
print("\nNumber of fields in reference:", len(ref_line.split('\t')))
print("Number of fields in formatted:", len(formatted_line.split('\t')))

