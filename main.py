import argparse
import logging
import re
from typing import Dict, List, Optional
from models import Question, QuestionSubject
import csv_parser
from generators import registry, moodle_xml_registry
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

def generate_latex_document(csv_file: str, subject_filter: Optional[str] = None, chapter_filter: Optional[int] = None, tag_filter: Optional[str] = None, custom_title: Optional[str] = None):
    """Generate the complete LaTeX document with all sections."""
    
    # Read questions from CSV with proper encoding
    questions = csv_parser.read_csv_file(csv_file)
    
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

    # Filter questions by chapter if specified
    if chapter_filter is not None:
        questions = [q for q in questions if q.chapter == chapter_filter]
        print(f"Filtering questions for chapter: {chapter_filter} ({len(questions)} questions)")

    # Filter questions by tag if specified
    if tag_filter:
        questions = [q for q in questions if q.tags and tag_filter in q.tags]
        print(f"Filtering questions for tag: {tag_filter} ({len(questions)} questions)")

    # Check if any questions reference machineForProblemStatements
    has_machine_references = any(
        'machineForProblemStatements' in str(q.content.get('sv', '')) or 
        'machineForProblemStatements' in str(q.content.get('en', ''))
        for q in questions
    )
    
    # Determine the title
    if custom_title:
        document_title = custom_title
    elif subject_filter:
        subject_enum = QuestionSubject[subject_filter.upper()]
        document_title = f"{subject_enum.value} Questions"
    elif chapter_filter is not None:
        document_title = f"Chapter {chapter_filter} Questions"
    elif tag_filter:
        document_title = f"Tag: {tag_filter}"
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
    
    # Conditionally include machine appendix based on whether questions reference it
    if not has_machine_references:
        # Remove the machine appendix chapters
        # Find and remove the appendix section
        appendix_pattern = r'\\appendix.*?\\printbibliography'
        replacement = r'\\printbibliography'
        output = re.sub(appendix_pattern, replacement, output, flags=re.DOTALL)
    
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
    elif chapter_filter is not None:
        output_filename = f"output_chapter_{chapter_filter}.tex"
    elif tag_filter:
        # Make filename safe by replacing spaces and special chars
        safe_tag = tag_filter.replace(' ', '_').replace('/', '_').replace('\\', '_')
        output_filename = f"output_tag_{safe_tag}.tex"
    
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(output)
    
    print(f"Generated LaTeX document with {len(questions)} questions")
    if has_machine_references:
        print("Machine appendix included (questions reference machineForProblemStatements)")
    else:
        print("Machine appendix excluded (no questions reference machineForProblemStatements)")
    print(f"Output written to: {output_filename}")
    print("Unicode characters have been converted to LaTeX commands")


def generate_moodle_xml(csv_file: str, subject_filter: Optional[str] = None, chapter_filter: Optional[int] = None, tag_filter: Optional[str] = None, lang_order: Optional[List[str]] = None):
    """Generate Moodle XML quiz format from question bank with bilingual support.
    
    Args:
        subject_filter: Filter by subject code (e.g., 'HIS')
        chapter_filter: Filter by chapter number
        lang_order: Language order for alternatives (default: ['sv', 'en'])
    """
    if lang_order is None:
        lang_order = ['sv', 'en']
    
    # Read questions from CSV with proper encoding
    questions = csv_parser.read_csv_file(csv_file)
    
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
    
    # Filter questions by chapter if specified
    if chapter_filter is not None:
        questions = [q for q in questions if q.chapter == chapter_filter]
        print(f"Filtering questions for chapter: {chapter_filter} ({len(questions)} questions)")

    # Filter questions by tag if specified
    if tag_filter:
        questions = [q for q in questions if q.tags and tag_filter in q.tags]
        print(f"Filtering questions for tag: {tag_filter} ({len(questions)} questions)")

    # Create the XML structure manually
    xml_parts = ['<?xml version="1.0" encoding="UTF-8"?>', '<quiz>']
    
    # Map questions by subject, order by id
    questions_mapping: Dict[str, List[Question]] = {}
    for question in questions:
        questions_mapping.setdefault(question.subject.name, [])
        questions_mapping[question.subject.name].append(question)

    for values in questions_mapping.values():
        values.sort(key=lambda q: q.id)
    
    # Add category elements for each subject
    for subject in QuestionSubject:
        if subject.name not in questions_mapping:
            logging.warning("The subject %s:%s is not used by any questions.", subject.name, subject.value)
            continue

        # Add category element
        xml_parts.append('  <question type="category">')
        xml_parts.append('    <category>')
        xml_parts.append(f'      <text>$course$/{subject.value}</text>')
        xml_parts.append('    </category>')
        xml_parts.append('  </question>')
        
        # Add questions for this subject
        for question in questions_mapping[subject.name]:
            # Check if question has content in at least one language
            if not question.content:
                continue
                
            try:
                # Get the appropriate Moodle XML generator
                generator = moodle_xml_registry.get_generator(question.type)
                xml_output = generator.to_moodle_xml(question, lang_order)
                
                # Add the XML directly without parsing
                if xml_output and not xml_output.startswith("<!--"):
                    # Indent each line of the question XML
                    question_lines = xml_output.split('\n')
                    indented_lines = ['  ' + line if line.strip() else line for line in question_lines]
                    xml_parts.extend(indented_lines)
                else:
                    # Add comment for unsupported question types
                    xml_parts.append(f'  <!-- Question {question.id} of type {question.type.value} not supported -->')
                    
            except KeyError:
                # Question type not supported in Moodle XML registry
                xml_parts.append(f'  <!-- Question {question.id} of type {question.type.value} not implemented for Moodle XML -->')
    
    xml_parts.append('</quiz>')
    
    # Join all parts and write to file
    final_xml = '\n'.join(xml_parts)
    
    # Determine output filename
    output_filename = "moodle_quiz.xml"
    if subject_filter:
        output_filename = f"moodle_quiz_{subject_filter.lower()}.xml"
    elif chapter_filter is not None:
        output_filename = f"moodle_quiz_chapter_{chapter_filter}.xml"
    elif tag_filter:
        # Make filename safe by replacing spaces and special chars
        safe_tag = tag_filter.replace(' ', '_').replace('/', '_').replace('\\', '_')
        output_filename = f"moodle_quiz_tag_{safe_tag}.xml"
    
    # Write XML file directly
    with open(output_filename, "w", encoding="utf-8") as f:
        f.write(final_xml)
    
    print(f"Generated Moodle XML quiz with {len(questions)} questions")
    print(f"Output written to: {output_filename}")
    print("Both English and Swedish content included when available")


def main():
    """Main function to handle command line arguments and generate document."""
    parser = argparse.ArgumentParser(description='Generate LaTeX document or Moodle XML quiz from question bank')
    parser.add_argument('--subject', '-s', 
                       help='Generate questions for a specific subject only. Use subject name from QuestionSubject enum (e.g., HIS, BIN, etc.)')
    parser.add_argument('--chapter', '-c', type=int,
                       help='Generate questions for a specific chapter only. Use chapter number (e.g., 0, 1, 2, etc.)')
    parser.add_argument('--tag',
                       help='Generate questions for a specific tag only. Use exact tag string.')
    parser.add_argument('--title', '-t',
                       help='Custom title for the document. If not provided, defaults to subject-specific title when filtering by subject.')
    parser.add_argument('--format', '-f', choices=['latex', 'moodle'], default='latex',
                       help='Output format: "latex" for LaTeX document (default) or "moodle" for Moodle XML quiz')
    parser.add_argument('--lang-order', '-l', nargs='+', default=['sv', 'en'],
                       help='Language order for answer alternatives in Moodle XML (default: sv en)')
    parser.add_argument('--list-subjects', action='store_true',
                       help='List all available subjects and exit')
    parser.add_argument('--list-tags', action='store_true',
                       help='List all available tags and exit')
    parser.add_argument('--csv-file', '-i', default='question_bank/2025-08-31.csv',
                       help='CSV file to process (default: question_bank/2025-08-31.csv)')
    
    args = parser.parse_args()
    
    if args.list_subjects:
        print("Available subjects:")
        for subject in QuestionSubject:
            print(f"  {subject.name}: {subject.value}")
        return

    if args.list_tags:
        # Read questions to extract all unique tags
        questions = csv_parser.read_csv_file(args.csv_file)
        all_tags = set()
        for q in questions:
            if q.tags:
                all_tags.update(q.tags)
        if all_tags:
            print("Available tags:")
            for tag in sorted(all_tags):
                # Count questions with this tag
                count = sum(1 for q in questions if q.tags and tag in q.tags)
                print(f"  {tag} ({count} questions)")
        else:
            print("No tags found in the question bank")
        return
    
    # Check for conflicting filter options
    filters_count = sum([args.subject is not None, args.chapter is not None, args.tag is not None])
    if filters_count > 1:
        print("Error: Cannot specify more than one filter (--subject, --chapter, or --tag) at the same time")
        return

    if args.format == 'moodle':
        generate_moodle_xml(args.csv_file, args.subject, args.chapter, args.tag, args.lang_order)
    else:
        generate_latex_document(args.csv_file, args.subject, args.chapter, args.tag, args.title)


if __name__ == "__main__":
    main()
