#!/usr/bin/env python3
"""
Script to get the proper title for a chapter in the CI/CD workflow.
Usage: python get_chapter_title.py <CHAPTER_NUMBER>
"""

import sys

def get_chapter_title(chapter_num):
    """Get the proper title for a chapter number."""
    try:
        chapter = int(chapter_num)
        return f'Chapter {chapter} Questions'
    except ValueError:
        return f'Chapter {chapter_num} Questions'

if __name__ == '__main__':
    if len(sys.argv) != 2:
        print(f"Usage: {sys.argv[0]} <CHAPTER_NUMBER>", file=sys.stderr)
        sys.exit(1)
    
    chapter_number = sys.argv[1]
    title = get_chapter_title(chapter_number)
    print(title)
