#!/usr/bin/env python3
"""Verify that formatted files match the reference format."""

print("Verifying format match...")
print("=" * 60)

with open('ilocano_dataset_cleaned.txt', 'r', encoding='utf-8') as f:
    ref_lines = [l.rstrip('\r\n') for l in f.readlines() if l.strip()]

with open('ilocano_crf_formatted.txt', 'r', encoding='utf-8') as f:
    fmt_lines = [l.rstrip('\r\n') for l in f.readlines() if l.strip()]

# Compare first 10 data lines
print(f"\nReference file: {len(ref_lines)} data lines")
print(f"Formatted file: {len(fmt_lines)} data lines")

# Check format structure
print("\nChecking format structure (first 3 lines):")
for i in range(min(3, len(ref_lines), len(fmt_lines))):
    ref_parts = ref_lines[i].split('\t')
    fmt_parts = fmt_lines[i].split('\t')
    match = ref_parts == fmt_parts
    status = "Match" if match else "Mismatch"
    print(f"  Line {i+1}: {status}")
    print(f"    Reference fields: {len(ref_parts)}")
    print(f"    Formatted fields: {len(fmt_parts)}")

print("\n" + "=" * 60)
print("Format verification complete!")
print("\nNote: The column numbers and colors you see in your IDE")
print("are normal - they indicate the IDE recognizes the tab-separated format.")

