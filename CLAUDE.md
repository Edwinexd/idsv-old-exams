# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is an educational exam question generator tool for Stockholm University's Department of Computer and Systems Sciences (DSV). The system generates LaTeX documents from CSV question banks and produces PDFs for various computer science subjects. It also supports Moodle XML export for online quizzes.

## Architecture

The codebase follows a modular Python architecture:

- **models.py**: Core data models using Pydantic (Question, QuestionContent, QuestionType, QuestionSubject enums)
- **csv_parser.py**: CSV question bank parsing with Unicode handling
- **generators.py**: Question type generators (Short Answer, Multiple Choice, etc.) with both LaTeX and Moodle XML output
- **main.py**: CLI entry point with filtering and document generation orchestration
- **i18n.py**: Internationalization support for Swedish/English content

The system uses a registry pattern in `generators.py` where different question types (sa, mc, sc, etc.) have specialized generator classes that implement both LaTeX and Moodle XML output formats.

## Key Commands

### Environment Setup
Always activate the virtual environment before running any commands:
```bash
source venv/bin/activate  # or just `venv` if using venv shortcut
pip install -r requirements.txt
```

### Generate LaTeX Documents
```bash
# Generate all questions
python main.py

# Filter by subject (e.g., HIS, BIN, AI, ALG, etc.)
python main.py --subject HIS

# Filter by chapter
python main.py --chapter 2

# Custom title
python main.py --title "Custom Exam Title"

# List available subjects
python main.py --list-subjects
```

### Compile LaTeX to PDF
```bash
pdflatex output.tex
biber output
pdflatex output.tex
pdflatex output.tex
```

### Generate Moodle XML
The system can generate Moodle XML quiz banks from the same question data for online quizzes.

## Question Bank Structure

- **question_bank/2025-08-31.csv**: Main question database with multilingual content
- Questions support Swedish (sv) and English (en) languages
- Each question has: ID, subject, chapter, type, content (question/answer pairs per language)
- Special handling for machine language problems with LaTeX includes

## Templates and Output

- **templates/**: LaTeX template files and compiled artifacts
- Generated files: `output.tex`, `output_[subject].tex`, `output_chapter_[n].tex`
- The system automatically handles Unicode encoding for LaTeX using pylatexenc

## GitHub Workflows

The repository has automated PDF generation via GitHub Actions that builds documents for all subjects and chapters, creating release artifacts. Check `.github/workflows/release.yml` for the full matrix of subjects and compilation targets.

## Development Notes

- Use the existing virtual environment (`venv/`) which is already configured
- The codebase uses type hints and Pydantic models for data validation
- Question content is stored as dictionaries with language keys ('sv', 'en')
- Generator classes implement both `to_latex()` and `to_moodle_xml()` methods
- Special handling exists for machine language appendices and bibliography references
- Dont add the written by claude note