#!/usr/bin/env python3
"""Script to build the complete build matrix for GitHub Actions."""

import json
import sys
import os

# Add project root to path to import modules
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

import csv_parser

def build_complete_matrix():
    """Build complete matrix including subjects, tags, chapters, and all."""
    questions = csv_parser.read_csv_file('question_bank/2025-08-31.csv')

    matrix_items = []

    # Add subjects
    all_subjects = set()
    for q in questions:
        all_subjects.add(q.subject.name)
    for subject in sorted(all_subjects):
        matrix_items.append({"type": "subject", "value": subject})

    # Add tags
    all_tags = set()
    for q in questions:
        if q.tags:
            all_tags.update(q.tags)
    for tag in sorted(all_tags):
        matrix_items.append({"type": "tag", "value": tag})

    # Add chapters (0-12)
    for chapter in range(13):
        matrix_items.append({"type": "chapter", "value": str(chapter)})

    # Add complete compilation
    matrix_items.append({"type": "all", "value": "ALL"})

    return matrix_items

if __name__ == "__main__":
    matrix = build_complete_matrix()
    print(json.dumps(matrix))
