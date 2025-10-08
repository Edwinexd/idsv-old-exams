#!/usr/bin/env python3
"""Script to extract all unique tags from the question CSV."""

import json
import sys
import os

# Add project root to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import csv_parser

def get_unique_tags():
    """Extract all unique tags from the CSV file."""
    questions = csv_parser.read_csv_file('question_bank/2025-08-31.csv')
    all_tags = set()

    for q in questions:
        if q.tags:
            all_tags.update(q.tags)

    return sorted(all_tags)

if __name__ == "__main__":
    tags = get_unique_tags()

    if tags:
        # Output as JSON array for GitHub Actions matrix
        print(json.dumps(tags))
    else:
        # Output empty array if no tags
        print(json.dumps([]))