#!/usr/bin/env python3
"""Script to extract all unique subjects from the question CSV."""

import json
import sys
import os

# Add project root to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import csv_parser

def get_unique_subjects():
    """Extract all unique subjects from the CSV file as matrix items."""
    questions = csv_parser.read_csv_file('question_bank/2025-08-31.csv')
    all_subjects = set()

    for q in questions:
        all_subjects.add(q.subject.name)

    # Return as matrix items with type and value
    return [{"type": "subject", "value": subject} for subject in sorted(all_subjects)]

if __name__ == "__main__":
    subjects = get_unique_subjects()

    if subjects:
        # Output as JSON array for GitHub Actions matrix
        print(json.dumps(subjects))
    else:
        # Output empty array if no subjects
        print(json.dumps([]))
