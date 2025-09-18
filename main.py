import argparse
import logging
import re
from typing import Dict, List, Optional
from models import Question, QuestionSubject
import csv_parser
from generators import registry
from pylatexenc.latexencode import UnicodeToLatexEncoder


# Initialize Unicode to LaTeX encoder
latex_encoder = UnicodeToLatexEncoder(
    non_ascii_only=True,
    replacement_latex_protection='braces'
)

def encode_for_latex(text):
    """Convert Unicode characters to LaTeX-safe encoding using pylatexenc."""
    if not text:
        return text
    
    return latex_encoder.unicode_to_latex(text)

def generate_latex_document(subject_filter: Optional[str] = None, custom_title: Optional[str] = None):
    """Generate the complete LaTeX document with all sections."""
    
    # Read questions from CSV with proper encoding
    questions = csv_parser.read_csv_file("question_bank/2025-08-31.csv")
    
    # Filter questions by subject if specified
    if subject_filter:
        try:
            subject_enum = QuestionSubject[subject_filter.upper()]
            questions = [q for q in questions if q.subject == subject_enum]
            print(f"Filtering questions for subject: {subject_enum.value} ({len(questions)} questions)")
        except KeyError:
            print(f"Error: Unknown subject '{subject_filter}'. Available subjects:")
            for subject in QuestionSubject:
                print(f"  {subject.name}: {subject.value}")
            return
    
    # Determine the title
    if custom_title:
        document_title = custom_title
    elif subject_filter:
        subject_enum = QuestionSubject[subject_filter.upper()]
        document_title = f"{subject_enum.value} Questions"
    else:
        document_title = "IDSV - Old Exam Questions, 2021-present"
    
    # Read the template with UTF-8 encoding
    with open("templates/body.tex", "r", encoding="utf-8") as f:
        template = f.read()
    
    # Generate content for each section
    swedish_questions_only = ""
    swedish_questions_and_answers = ""
    english_questions_only = ""
    english_questions_and_answers = ""

    # map by subject, order by id
    questions_mapping: Dict[str, List[Question]] = {}
    for question in questions:
        questions_mapping.setdefault(question.subject.name, [])
        questions_mapping[question.subject.name].append(question)

    for values in questions_mapping.values():
        values.sort(key=lambda q: q.id)

    # \section{Subject} is inserted after each subject type
    for subject in QuestionSubject:
        if subject.name not in questions_mapping:
            logging.warning("The subject %s:%s is not used by any questions.", subject.name, subject.value)
            continue

        title = f"\\section{{{subject.value}}}\n\n"
        swedish_questions_only += title
        swedish_questions_and_answers += title
        english_questions_only += title
        english_questions_and_answers += title
    
        for question in questions_mapping[subject.name]:
            # Swedish questions only (no answers)
            if 'sv' in question.content:
                latex_output = registry.get_generator(question.type).to_latex(question, "sv", with_answer=False)
                swedish_questions_only += encode_for_latex(latex_output)
                swedish_questions_only += "\n\n"
            
            # Swedish questions with answers
            if 'sv' in question.content:
                latex_output = registry.get_generator(question.type).to_latex(question, "sv", with_answer=True)
                swedish_questions_and_answers += encode_for_latex(latex_output)
                swedish_questions_and_answers += "\n\n"
            
            # English questions only (no answers)
            if 'en' in question.content:
                latex_output = registry.get_generator(question.type).to_latex(question, "en", with_answer=False)
                english_questions_only += encode_for_latex(latex_output)
                english_questions_only += "\n\n"
            
            # English questions with answers
            if 'en' in question.content:
                latex_output = registry.get_generator(question.type).to_latex(question, "en", with_answer=True)
                english_questions_and_answers += encode_for_latex(latex_output)
                english_questions_and_answers += "\n\n"


    
    
    # Replace template variables
    output = template.replace("% <<<TEMPLATEVAR_SWEDISH_QUESTIONS_ONLY>>>", swedish_questions_only.strip())
    output = output.replace("% <<<TEMPLATEVAR_SWEDISH_QUESTIONS_AND_ANSWERS>>>", swedish_questions_and_answers.strip())
    output = output.replace("% <<<TEMPLATEVAR_ENGLISH_QUESTIONS_ONLY>>>", english_questions_only.strip())
    output = output.replace("% <<<TEMPLATEVAR_ENGLISH_QUESTIONS_AND_ANSWERS>>>", english_questions_and_answers.strip())
    
    # Replace the title
    output = output.replace("\\title{IDSV - Old Exam Questions, 2021-present}", f"\\title{{{encode_for_latex(document_title)}}}")
    
    output = re.sub(r"(n\^\d+)", lambda m: f"${m.group(1)}$", output, flags=re.MULTILINE)
    output = re.sub(r"(\d+\^n)", lambda m: f"${m.group(1)}$", output, flags=re.MULTILINE)
    output = re.sub(r"(2\^\d+)", lambda m: f"${m.group(1)}$", output, flags=re.MULTILINE)

    output = re.sub(r"\\ensuremath\{\\Theta\}", "O", output, flags=re.MULTILINE)

    

    # Write output file with UTF-8 encoding, but content is LaTeX-safe
    output_filename = "output.tex"
    if subject_filter:
        output_filename = f"output_{subject_filter.lower()}.tex"
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"Generated LaTeX document with {len(questions)} questions")
    print(f"Output written to: {output_filename}")
    print("Unicode characters have been converted to LaTeX commands")


def main():
    """Main function to handle command line arguments and generate document."""
    parser = argparse.ArgumentParser(description='Generate LaTeX document from question bank')
    parser.add_argument('--subject', '-s', 
                       help='Generate questions for a specific subject only. Use subject name from QuestionSubject enum (e.g., HIS, BIN, etc.)')
    parser.add_argument('--title', '-t',
                       help='Custom title for the document. If not provided, defaults to subject-specific title when filtering by subject.')
    parser.add_argument('--list-subjects', action='store_true',
                       help='List all available subjects and exit')
    
    args = parser.parse_args()
    
    if args.list_subjects:
        print("Available subjects:")
        for subject in QuestionSubject:
            print(f"  {subject.name}: {subject.value}")
        return
    
    generate_latex_document(args.subject, args.title)


if __name__ == "__main__":
    main()
