#!/usr/bin/env python3
"""
Script to get the proper title for a subject in the CI/CD workflow.
Usage: python get_subject_title.py <SUBJECT_CODE>
"""

import sys
import os

# Add the parent directory to the path so we can import models
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from models import QuestionSubject

def get_subject_title(code):
    """Get the proper title for a subject code."""
    try:
        subject = QuestionSubject[code]
        return f'{subject.value} Questions'
    except KeyError:
        return f'{code} Questions'

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <SUBJECT_CODE>", file=sys.stderr)
        sys.exit(1)
    
    subject_code = sys.argv[1]
    title = get_subject_title(subject_code)
    print(title)
