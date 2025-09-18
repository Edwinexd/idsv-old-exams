import csv
import re
from typing import Dict, List, Optional
from dataclasses import dataclass
from enum import Enum
from pydantic import BaseModel

# Import the classes from your existing code
from models import Question, QuestionContent, QuestionType, QuestionSubject


class CSVQuestionParser:
    """Parser for converting CSV question data to Question objects."""
    
    def __init__(self):
        self.questions: List[Question] = []
    
    def parse_csv_content(self, csv_content: str) -> List[Question]:
        """Parse CSV content string and return a list of Question objects."""
        reader = csv.DictReader(csv_content.strip().split('\n'), escapechar='\\')
        
        for row in reader:
            question = self._parse_row(row)
            if question:
                self.questions.append(question)
        
        return self.questions
    
    def _parse_row(self, row: Dict[str, str]) -> Optional[Question]:
        """Parse a single CSV row into a Question object."""
        try:
            # Extract basic fields
            question_id = int(row['id']) if row['id'] else None
            if question_id is None:
                return None
            
            chapter = int(row['chapter']) if row['chapter'] else 1
            
            # Parse question type
            try:
                question_type = QuestionType(row['type'])
            except ValueError:
                # Handle case where type doesn't match enum exactly
                type_mapping = {
                    'essay': QuestionType.essay,
                    'sa': QuestionType.sa,
                    'sc': QuestionType.sc,
                    'mc': QuestionType.mc,
                    'mq': QuestionType.mq,
                    'dq': QuestionType.dq,
                    'nq': QuestionType.nq
                }
                question_type = type_mapping.get(row['type'].lower())
                if not question_type:
                    print(f"Warning: Unknown question type '{row['type']}' for question {question_id}")
                    return None
            
            # Parse subject
            try:
                # Parse subject by name (key) rather than value
                subject_key = row['subject'].lower()
                subject_map = {name.lower(): value for name, value in QuestionSubject.__members__.items()}
                if subject_key in subject_map:
                    subject = subject_map[subject_key]
                else:
                    raise ValueError(f"Invalid subject: {row['subject']}")
            except ValueError:
                print(f"Warning: Unknown subject '{row['subject']}' for question {question_id}")
                return None
            
            # Build content for both languages
            content = {}
            
            # Swedish content
            if row.get('q_se') or row.get('ans_se'):
                content['sv'] = QuestionContent(
                    question=row.get('q_se', '').strip(),
                    answer=row.get('ans_se', '').strip() if row.get('ans_se') else None,
                    q_alternatives=self._parse_alternatives(row.get('q_alt_se', ''), separators=["_"]),
                    ans_alternatives=self._parse_alternatives(row.get('ans_alt_se', ''))
                )
            
            # English content
            if row.get('q_en') or row.get('ans_en'):
                content['en'] = QuestionContent(
                    question=row.get('q_en', '').strip(),
                    answer=row.get('ans_en', '').strip() if row.get('ans_en') else None,
                    q_alternatives=self._parse_alternatives(row.get('q_alt_en', ''), separators=["_"]),
                    ans_alternatives=self._parse_alternatives(row.get('ans_alt_en', ''))
                )
            
            # Create Question object
            question = Question(
                id=question_id,
                chapter=chapter,
                type=question_type,
                subject=subject,
                content=content
            )
            
            return question
            
        except Exception as e:
            print(f"Error parsing row for question ID {row.get('id', 'unknown')}: {e}")
            return None
    
    def _parse_alternatives(self, alternatives_str: str, separators: Optional[List[str]] = None) -> Optional[List[str]]:
        """Parse alternatives string into a list of alternatives."""
        if not alternatives_str or not alternatives_str.strip():
            return None
        
        # Handle different separators commonly used in CSV
        # Try semicolon first (common in European CSVs), then comma, then pipe
        if separators is None:
            separators = [';', '|', ',']
        
        for sep in separators:
            if sep in alternatives_str:
                alternatives = [alt.strip() for alt in alternatives_str.split(sep)]
                # Filter out empty alternatives
                alternatives = [alt for alt in alternatives if alt]
                return alternatives if alternatives else None
        
        # If no separator found, treat as single alternative
        single_alt = alternatives_str.strip()
        return [single_alt] if single_alt else None
    
    def get_questions_by_subject(self, subject: QuestionSubject) -> List[Question]:
        """Get all questions for a specific subject."""
        return [q for q in self.questions if q.subject == subject]
    
    def get_questions_by_type(self, question_type: QuestionType) -> List[Question]:
        """Get all questions of a specific type."""
        return [q for q in self.questions if q.type == question_type]
    
    def get_questions_by_chapter(self, chapter: int) -> List[Question]:
        """Get all questions from a specific chapter."""
        return [q for q in self.questions if q.chapter == chapter]
    
    def validate_questions(self) -> Dict[str, List[int]]:
        """Validate parsed questions and return any issues found."""
        issues = {
            'missing_content': [],
            'missing_questions': [],
            'missing_answers_for_answer_types': [],
            'missing_alternatives_for_choice_types': []
        }
        
        for question in self.questions:
            # Check if question has content in at least one language
            if not question.content:
                issues['missing_content'].append(question.id)
                continue
            
            for lang, content in question.content.items():
                # Check for missing questions
                if not content.question:
                    issues['missing_questions'].append(question.id)
                
                # Check for missing answers in answer-required types
                if question.type in [QuestionType.sa, QuestionType.essay, QuestionType.nq] and not content.answer:
                    issues['missing_answers_for_answer_types'].append(question.id)
                
                # Check for missing alternatives in choice types
                if question.type in [QuestionType.sc, QuestionType.mc, QuestionType.dq, QuestionType.mq]:
                    if not content.ans_alternatives:
                        issues['missing_alternatives_for_choice_types'].append(question.id)
        
        return issues


# Alternative method for parsing from string content
def parse_csv_string(csv_content: str) -> List[Question]:
    """Convenience function to parse CSV content directly from a string."""
    parser = CSVQuestionParser()
    parser.parse_csv_content(csv_content)
    return parser.questions

def read_csv_file(file_path: str) -> List[Question]:
    """Convenience function to read and parse a CSV file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return parse_csv_string(content)

if __name__ == "__main__":
    with open("question_bank/2025-08-31.csv", "r", encoding="utf-8") as f:
        content = f.read()
    questions = parse_csv_string(content)
    print(f"Parsed {len(questions)} questions from string content")
