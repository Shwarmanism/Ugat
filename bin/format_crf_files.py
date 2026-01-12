#!/usr/bin/env python3
"""
Script to format CRF training files to match ilocano_dataset_cleaned.txt format.
Converts tab-delimited files to pipe-delimited format for CRF training.
"""

import os
import sys
import re


def format_crf_file(input_file, output_file):
    """
    Convert tab or space-delimited CRF file to pipe-delimited format.
    
    Args:
        input_file: Path to input CRF file (tab or space-delimited)
        output_file: Path to output formatted file (pipe-delimited)
    """
    if not os.path.exists(input_file):
        print(f"Error: File '{input_file}' not found.")
        return False
    
    try:
        with open(input_file, 'r', encoding='utf-8') as f_in:
            lines = f_in.readlines()
        
        formatted_lines = []
        prev_was_empty = False
        skipped_lines = 0
        
        for line_num, line in enumerate(lines, 1):
            line = line.rstrip('\n\r')
            
            # Skip empty lines but add one between sentences
            if not line.strip():
                if not prev_was_empty:
                    formatted_lines.append('')
                    prev_was_empty = True
                continue
            
            prev_was_empty = False
            
            # Try splitting by tab first
            if '\t' in line:
                parts = line.split('\t')
            else:
                # Split by multiple spaces (2 or more)
                parts = re.split(r'\s{2,}', line.strip())
            
            # Clean up parts
            parts = [p.strip() for p in parts if p.strip()]
            
            # Ensure we have exactly 7 fields
            if len(parts) != 7:
                # Try splitting by any whitespace as fallback
                parts = line.split()
                if len(parts) >= 7:
                    parts = parts[:7]
                else:
                    skipped_lines += 1
                    if skipped_lines <= 5:  # Only show first 5 warnings
                        print(f"Warning: Line {line_num} has {len(parts)} fields instead of 7, skipping: {line[:60]}...")
                    continue
            
            # Join with tab delimiter (matching ilocano_dataset_cleaned.txt format)
            formatted_line = '\t'.join(parts)
            formatted_lines.append(formatted_line)
        
        if skipped_lines > 5:
            print(f"  (Skipped {skipped_lines} malformed lines total)")
        
        # Remove trailing empty lines
        while formatted_lines and not formatted_lines[-1]:
            formatted_lines.pop()
        
        # Write formatted output
        with open(output_file, 'w', encoding='utf-8') as f_out:
            f_out.write('\n'.join(formatted_lines))
            if formatted_lines:  # Add newline at end if file is not empty
                f_out.write('\n')
        
        data_lines = len([l for l in formatted_lines if l])
        print(f"[OK] Formatted '{input_file}' -> '{output_file}'")
        print(f"     Processed {data_lines} data lines")
        return True
        
    except Exception as e:
        print(f"Error processing '{input_file}': {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Main function to format all CRF files."""
    # List of files to format
    files_to_format = [
        'Hiligaynon_crf.txt',
        'ilocano_crf.txt',
        'Cebuano_crf.txt'
    ]
    
    # Output file names (you can modify these if needed)
    output_files = [
        'Hiligaynon_crf_formatted.txt',
        'ilocano_crf_formatted.txt',
        'Cebuano_crf_formatted.txt'
    ]
    
    print("=" * 60)
    print("CRF File Formatter")
    print("Formatting CRF files to match ilocano_dataset_cleaned.txt format")
    print("=" * 60)
    print()
    
    success_count = 0
    
    for input_file, output_file in zip(files_to_format, output_files):
        if format_crf_file(input_file, output_file):
            success_count += 1
        print()
    
    print("=" * 60)
    print(f"Formatting complete: {success_count}/{len(files_to_format)} files processed successfully")
    print("=" * 60)
    print()
    print("Formatted files:")
    for input_file, output_file in zip(files_to_format, output_files):
        if os.path.exists(output_file):
            print(f"  - {output_file}")
    
    # Optionally, you can overwrite original files
    # Uncomment the following lines if you want to replace original files
    # print("\nWould you like to overwrite original files? (y/n): ", end='')
    # response = input().strip().lower()
    # if response == 'y':
    #     for input_file, output_file in zip(files_to_format, output_files):
    #         if os.path.exists(output_file):
    #             os.replace(output_file, input_file)
    #             print(f"Replaced '{input_file}' with formatted version")


if __name__ == '__main__':
    main()

