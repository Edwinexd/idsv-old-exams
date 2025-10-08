import logging
import random
import re
import xml.etree.ElementTree as ET
from html import escape
from typing import Dict
from models import LANGUAGE_CODE, Generator, Question, QuestionContent, QuestionType
from i18n import LANGUAGES

class _GeneratorRegistry:
    _generators: Dict[QuestionType, Generator] = {}

    @classmethod
    def register_generator(cls, generator: Generator):
        cls._generators[generator.supported_type] = generator

    @classmethod
    def get_generator(cls, question_type: QuestionType) -> Generator:
        return cls._generators[question_type]


registry = _GeneratorRegistry()

def process_appendix_placeholders(text: str) -> str:
    """Replace %appendix:filename.tex% placeholders with proper LaTeX references."""
    if not text:
        return text

    def replace_placeholder(match):
        filename = match.group(1)
        # Generate label from filename automatically
        # Remove .tex extension and convert to a valid LaTeX label
        label = "appendix:" + filename.replace('.tex', '').replace('-', '').replace('_', '').replace(' ', '')
        return f"\\autoref{{{label}}}"

    # Replace all appendix placeholders
    processed = re.sub(r'%appendix:([^%]+)%', replace_placeholder, text)
    return processed

# Short Answer
# TODO: Abstract and add essay variant which is basically the same but longer space for answer
class ShortAnswerGenerator(Generator):
    supported_type = QuestionType.sa

    def to_latex(self, question: Question, lang: LANGUAGE_CODE, with_answer: bool = False) -> str:
        language = LANGUAGES[lang]
        content = question.content.get(lang)
        if not content:
            logging.warning(f"Question {question.id} does not have content in language {lang}")
            # return f"\\textit{{{language.content_not_available_language}}}\n\n"
            return ""

        # Process appendix placeholders in the question
        processed_question = process_appendix_placeholders(content.question)
        processed_answer = process_appendix_placeholders(content.answer) if content.answer else None

        latex = f"\\subsection*{{{processed_question} ({question.id})}}\n\n"
        latex += f"\\label{{q:{question.id}:sa:{lang}:{with_answer}}}\n\n"
        if with_answer and processed_answer:
            latex += f"\\textbf{{{language.answer}}}: {processed_answer}\n\n"
        elif with_answer and not content.answer:
            latex += f"\\textbf{{{language.answer}}}: {language.content_not_available_language}\n\n"
        else:
            # TODO Typable pdf text box?
            latex += "\\vspace{2cm}\n\n"  # Space for answer
            latex += "\\noindent\\makebox[\\textwidth]{\\hrulefill}\n\n"  # Horizontal line
            # jump to answer
            latex += "\\vspace{1cm}\n\n"
            latex += f"\\textit{{{language.answer}}}: \\autoref{{q:{question.id}:sa:{lang}:{True}}}\n\n"

        return latex

# Essay
class EssayGenerator(ShortAnswerGenerator):
    supported_type = QuestionType.essay

class MultipleChoiceGenerator(Generator):
    _symbol_selection = "$\\square$"  # empty square
    supported_type = QuestionType.mc

    def to_latex(self, question: Question, lang: LANGUAGE_CODE, with_answer: bool = False) -> str:
        language = LANGUAGES[lang]
        content = question.content.get(lang)
        if not content:
            logging.warning(f"Question {question.id} does not have content in language {lang}")
            return ""

        latex = f"\\subsection*{{{content.question} ({question.id})}}\n\n"
        latex += f"\\label{{q:{question.id}:mc:{lang}:{with_answer}}}\n\n"

        if not content.ans_alternatives:
            logging.warning(f"Question {question.id} does not have answer alternatives for multiple choice")
            return ""

        latex += "\\begin{itemize}\n"
        answer_highlighted = False
        shuffled = list(content.ans_alternatives)
        if content.answer:
            shuffled.append(content.answer)
        random.seed(question.id)  # seed with question id for consistency between compilations
        random.shuffle(shuffled)
        for alternative in shuffled:
            if with_answer and content.answer and alternative.lower().strip() in content.answer.lower().strip():
                latex += f"  \\item[{self._symbol_selection}] \\textbf{{{alternative}}}\n"
                answer_highlighted = True
            else:
                latex += f"  \\item[{self._symbol_selection}] {alternative}\n"
        latex += "\\end{itemize}\n\n"

        if with_answer and not content.answer:
            latex += f"\\textbf{{{language.answer}}}: {language.content_not_available_language}\n\n"

        if with_answer and not answer_highlighted:
            latex += f"\\textbf{{{language.answer}}}: {content.answer}\n\n"


        if not with_answer:
            latex += "\\vspace{1cm}\n\n"
            latex += f"\\textit{{{language.answer}}}: \\autoref{{q:{question.id}:mc:{lang}:{True}}}\n\n"

        return latex

# sc = "Single Choice" # generates a question with multiple alternatives, only one is correct
class SingleChoiceGenerator(MultipleChoiceGenerator):
    supported_type = QuestionType.sc
    _symbol_selection = "$\\bigcirc$"  # empty circle


# dq = "Drop Down"
# dq is fucked in the provided CSV as no answer alternatives are given, ???
# due to this being broken we call it as a short answer for now
class DropDownGenerator(ShortAnswerGenerator):
    supported_type = QuestionType.dq


# nq = "Number"
# TODO: I mean it's kinda fine as-is...
class NumberGenerator(ShortAnswerGenerator):
    supported_type = QuestionType.nq


# code = "Code Assignment"
# Shows only the assignment description, no answer available
class CodeGenerator(Generator):
    supported_type = QuestionType.code

    def to_latex(self, question: Question, lang: LANGUAGE_CODE, with_answer: bool = False) -> str:
        language = LANGUAGES[lang]
        content = question.content.get(lang)
        if not content:
            logging.warning(f"Question {question.id} does not have content in language {lang}")
            return ""

        # Process appendix placeholders in the question
        processed_question = process_appendix_placeholders(content.question)

        latex = f"\\subsection*{{{language.programming} ({question.id})}}\n\n"
        latex += f"\\label{{q:{question.id}:code:{lang}}}\n\n"
        latex += f"{processed_question}\n\n"

        # No answer is shown for code assignments
        # Just provide space for the solution
        latex += "\\vspace{1cm}\n\n"

        latex += f"\\textbf{{{language.answer}}}: {language.content_not_available_language}\n\n"

        return latex


registry.register_generator(ShortAnswerGenerator())
registry.register_generator(EssayGenerator())
registry.register_generator(MultipleChoiceGenerator())
registry.register_generator(SingleChoiceGenerator())
registry.register_generator(DropDownGenerator())
registry.register_generator(NumberGenerator())
registry.register_generator(CodeGenerator())


# mq = "Multi Question" # generates a questions
# defined last as it uses other generators
class MultiQuestionGenerator(Generator):
    supported_type = QuestionType.mq

    def to_latex(self, question: Question, lang: LANGUAGE_CODE, with_answer: bool = False) -> str:
        language = LANGUAGES[lang]
        content = question.content.get(lang)
        if not content:
            logging.warning(f"Question {question.id} does not have content in language {lang}")
            return ""     

        base_content = content.question
        # believe it or not this is also a comma separated list of answers, one for each sub-question...
        answers = content.answer.split(",") if content.answer else []
        variants: list[str] = content.q_alternatives or []
        variants_ans: list[str] = content.ans_alternatives or [] # each is either "essay" or a comma separated list of alternatives...

        if len(variants) != len(variants_ans):
            logging.warning(f"Question {question.id} has mismatched number of question and answer alternatives")
            return ""

        output = ""
        for i, (var, var_ans) in enumerate(zip(variants, variants_ans)):
            if var_ans.strip() == "essay":
                question = Question(
                    id=question.id * 100 + i,  # Generate a new ID based on parent question ID
                    chapter=question.chapter,
                    type=QuestionType.essay,
                    subject=question.subject,
                    content={lang: QuestionContent(question=f"{base_content} - {var}", answer=answers[i] if i < len(answers) else None)}
                )
                output += registry.get_generator(QuestionType.essay).to_latex(question, lang, with_answer)
                continue

            # comma separated list of alternatives, sc is inferred from the broken CSV
            question = Question(
                id=question.id * 100 + i,  # Generate a new ID based on parent question ID
                chapter=question.chapter,
                type=QuestionType.sc,
                subject=question.subject,
                content={lang: QuestionContent(question=f"{base_content} - {var}", answer=answers[i] if i < len(answers) else None, ans_alternatives=[a.strip() for a in var_ans.split(",")] if var_ans.count(",") > 0 else None)}
            )
            output += registry.get_generator(QuestionType.sc).to_latex(question, lang, with_answer)

        return output


registry.register_generator(MultiQuestionGenerator())


def _create_xml_with_cdata(question_elem, question_text, answer_feedback=None):
    """Create properly formatted XML string with CDATA sections."""
    # Convert the ElementTree to string first
    base_xml = ET.tostring(question_elem, encoding="unicode")
    
    # Replace the questiontext placeholder with CDATA
    if question_text:
        base_xml = base_xml.replace("PLACEHOLDER_QUESTIONTEXT", f"<![CDATA[{question_text}]]>")
    
    # Replace the generalfeedback placeholder with CDATA if present
    if answer_feedback:
        base_xml = base_xml.replace("PLACEHOLDER_GENERALFEEDBACK", f"<![CDATA[{answer_feedback}]]>")
    
    return base_xml


def _create_question_manually(question_id, subject_value, question_type, question_text, answer_feedback=None, moodle_name_override=None, **kwargs):
    """Manually create XML string to avoid ElementTree escaping issues."""

    xml_parts = [f'<question type="{question_type}">']
    xml_parts.append(f'  <name>')
    name_text = moodle_name_override or f"Question {question_id} - {subject_value}"
    xml_parts.append(f'    <text>{name_text}</text>')
    xml_parts.append(f'  </name>')
    
    # Question text with CDATA
    xml_parts.append('  <questiontext format="html">')
    xml_parts.append(f'    <text><![CDATA[{question_text}]]></text>')
    xml_parts.append('  </questiontext>')
    
    # Default grade
    xml_parts.append('  <defaultgrade>1</defaultgrade>')
    
    # General feedback
    xml_parts.append('  <generalfeedback format="html">')
    if answer_feedback:
        xml_parts.append(f'    <text><![CDATA[{answer_feedback}]]></text>')
    else:
        xml_parts.append('    <text></text>')
    xml_parts.append('  </generalfeedback>')
    
    # Question type specific elements
    if question_type == "essay":
        xml_parts.extend([
            '  <responseformat>editor</responseformat>',
            '  <responserequired>1</responserequired>',
            '  <responsefieldlines>15</responsefieldlines>'
        ])
    elif question_type == "shortanswer":
        if "answer_text" in kwargs:
            xml_parts.extend([
                f'  <answer fraction="100">',
                f'    <text>{escape(kwargs["answer_text"])}</text>',
                f'    <feedback format="html">',
                f'      <text></text>',
                f'    </feedback>',
                f'  </answer>'
            ])
        xml_parts.append('  <usecase>0</usecase>')
    elif question_type == "multichoice":
        single = kwargs.get("single", "false")
        alternatives = kwargs.get("alternatives", [])
        correct_answers = kwargs.get("correct_answers", [])
        
        xml_parts.extend([
            f'  <single>{single}</single>',
            '  <shuffleanswers>true</shuffleanswers>'
        ])
        
        for alternative in alternatives:
            is_correct = any(correct.strip().lower() in alternative.lower().strip() for correct in correct_answers)
            fraction = "100" if is_correct else "0"
            xml_parts.extend([
                f'  <answer fraction="{fraction}">',
                f'    <text>{escape(alternative)}</text>',
                f'    <feedback format="html">',
                f'      <text></text>',
                f'    </feedback>',
                f'  </answer>'
            ])
    elif question_type == "numerical":
        if "answer_text" in kwargs:
            try:
                numeric_answer = float(kwargs["answer_text"])
                tolerance = str(abs(numeric_answer) * 0.1)
            except ValueError:
                tolerance = "0"
            
            xml_parts.extend([
                f'  <answer fraction="100">',
                f'    <text>{escape(kwargs["answer_text"])}</text>',
                f'    <tolerance>{tolerance}</tolerance>',
                f'    <feedback format="html">',
                f'      <text></text>',
                f'    </feedback>',
                f'  </answer>'
            ])
    
    xml_parts.append('</question>')
    return '\n'.join(xml_parts)


# Moodle XML Generator Classes
def _get_bilingual_text(question: Question, field: str, lang_order: list | None = None, escape_html: bool = False) -> str:
    """Get text in both languages if available, combining them with proper HTML formatting.

    Args:
        question: The question object
        field: The field to extract (e.g., 'question', 'answer')
        lang_order: List of language codes in order of preference (default: ['en', 'sv'])
        escape_html: Whether to escape HTML entities (False when using CDATA)
    """
    if lang_order is None:
        lang_order = ['en', 'sv']

    texts = []

    for i, lang in enumerate(lang_order):
        if lang in question.content:
            content = question.content[lang]
            text = getattr(content, field, None)
            if text:
                # Optionally escape HTML
                display_text = escape(text) if escape_html else text
                # First language is normal, subsequent languages are italicized
                if i == 0:
                    texts.append(f"<p>{display_text}</p>")
                else:
                    texts.append(f"<p><em>{display_text}</em></p>")

    # Join the paragraphs
    if texts:
        return "\n        ".join(texts)
    else:
        return ""


def _get_bilingual_alternatives(question: Question, lang_order: list | None = None) -> list:
    """Get answer alternatives in both languages, combining them.
    
    Args:
        question: The question object
        lang_order: List of language codes in order of preference (default: ['sv', 'en'])
    """
    if lang_order is None:
        lang_order = ['sv', 'en']
    
    alternatives = []
    
    # Collect alternatives from languages in specified order
    for lang in lang_order:
        if lang in question.content:
            content = question.content[lang]
            if content.ans_alternatives:
                alternatives.extend(content.ans_alternatives)
    
    # Also add correct answers to alternatives if not already included
    for lang in lang_order:
        if lang in question.content:
            content = question.content[lang]
            if content.answer:
                # Handle comma-separated answers
                correct_answers = [ans.strip() for ans in content.answer.split(",")]
                for correct_answer in correct_answers:
                    if correct_answer not in alternatives:
                        alternatives.append(correct_answer)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_alternatives = []
    for alt in alternatives:
        if alt.lower().strip() not in seen:
            seen.add(alt.lower().strip())
            unique_alternatives.append(alt)
    
    return unique_alternatives


def _get_bilingual_answers(question: Question, lang_order: list | None = None) -> list:
    """Get correct answers from both languages.
    
    Args:
        question: The question object
        lang_order: List of language codes in order of preference (default: ['sv', 'en'])
    """
    if lang_order is None:
        lang_order = ['sv', 'en']
    
    answers = []
    
    for lang in lang_order:
        if lang in question.content:
            content = question.content[lang]
            if content.answer:
                # Handle comma-separated answers
                lang_answers = [ans.strip() for ans in content.answer.split(",")]
                answers.extend(lang_answers)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_answers = []
    for ans in answers:
        if ans.lower().strip() not in seen:
            seen.add(ans.lower().strip())
            unique_answers.append(ans)
    
    return unique_answers


def _get_bilingual_answer_feedback(question: Question, lang_order: list | None = None, escape_html: bool = False) -> str:
    """Get answer text formatted as feedback with labels for both languages.

    Args:
        question: The question object
        lang_order: List of language codes in order of preference (default: ['en', 'sv'])
        escape_html: Whether to escape HTML entities (False when using CDATA)
    """
    if lang_order is None:
        lang_order = ['en', 'sv']

    feedback_parts = []

    # Language-specific labels
    labels = {
        'en': 'Expected answer:',
        'sv': 'Förväntat svar:'
    }

    for lang in lang_order:
        if lang in question.content:
            content = question.content[lang]
            if content.answer:
                label = labels.get(lang, 'Answer:')
                answer_text = escape(content.answer) if escape_html else content.answer
                feedback_parts.append(f"<p><strong>{label}</strong> {answer_text}</p>")

    # Join the paragraphs
    if feedback_parts:
        return "\n        ".join(feedback_parts)
    else:
        return ""


class MoodleXMLShortAnswerGenerator(ShortAnswerGenerator):
    """Generator for short answer questions in Moodle XML format"""

    def to_moodle_xml(self, question: Question, lang_order: list[str] | None = None) -> str:
        # Use bilingual text instead of single language
        question_text = _get_bilingual_text(question, 'question', lang_order)
        answer_text = _get_bilingual_text(question, 'answer', lang_order)
        
        if not question_text:
            return f"<!-- Question {question.id} has no content -->"
        
        # Create question element
        question_elem = ET.Element("question", type="shortanswer")
        
        # Question name
        name_elem = ET.SubElement(question_elem, "name")
        name_text_elem = ET.SubElement(name_elem, "text")
        name_text_elem.text = question.moodle_name_override or f"Question {question.id} - {question.subject.value}"
        
        # Question text with CDATA
        questiontext_elem = ET.SubElement(question_elem, "questiontext", format="html")
        questiontext_text_elem = ET.SubElement(questiontext_elem, "text")
        questiontext_text_elem.text = "PLACEHOLDER_QUESTIONTEXT"
        
        # Default grade
        defaultgrade_elem = ET.SubElement(question_elem, "defaultgrade")
        defaultgrade_elem.text = "1"
        
        # General feedback
        generalfeedback_elem = ET.SubElement(question_elem, "generalfeedback", format="html")
        generalfeedback_text_elem = ET.SubElement(generalfeedback_elem, "text")
        generalfeedback_text_elem.text = ""
        
        # Answer
        if answer_text:
            answer_elem = ET.SubElement(question_elem, "answer", fraction="100")
            answer_text_elem = ET.SubElement(answer_elem, "text")
            answer_text_elem.text = escape(answer_text)
            
            # Answer feedback
            feedback_elem = ET.SubElement(answer_elem, "feedback", format="html")
            feedback_text_elem = ET.SubElement(feedback_elem, "text")
            feedback_text_elem.text = ""
        
        # Use case sensitivity
        usecase_elem = ET.SubElement(question_elem, "usecase")
        usecase_elem.text = "0"
        
        return _create_xml_with_cdata(question_elem, question_text)


class MoodleXMLEssayGenerator(EssayGenerator):
    """Generator for essay questions in Moodle XML format"""

    def to_moodle_xml(self, question: Question, lang_order: list[str] | None = None) -> str:
        question_text = _get_bilingual_text(question, 'question', lang_order)
        answer_feedback = _get_bilingual_answer_feedback(question, lang_order)
        
        if not question_text:
            return f"<!-- Question {question.id} has no content -->"
        
        return _create_question_manually(
            question.id,
            question.subject.value,
            "essay",
            question_text,
            answer_feedback,
            moodle_name_override=question.moodle_name_override
        )


class MoodleXMLMultipleChoiceGenerator(MultipleChoiceGenerator):
    """Generator for multiple choice questions in Moodle XML format"""

    def to_moodle_xml(self, question: Question, lang_order: list[str] | None = None) -> str:
        if lang_order is None:
            lang_order = ['sv', 'en']

        question_text = _get_bilingual_text(question, 'question', lang_order, escape_html=False)
        alternatives = _get_bilingual_alternatives(question, lang_order)
        correct_answers = _get_bilingual_answers(question, lang_order)

        if not question_text:
            return f"<!-- Question {question.id} has no content -->"

        if not alternatives:
            return f"<!-- Question {question.id} has no answer alternatives -->"

        return _create_question_manually(
            question.id,
            question.subject.value,
            "multichoice",
            question_text,
            None,  # No general feedback for now
            moodle_name_override=question.moodle_name_override,
            single="false",  # Allow multiple correct answers
            alternatives=alternatives,
            correct_answers=correct_answers
        )


class MoodleXMLSingleChoiceGenerator(SingleChoiceGenerator):
    """Generator for single choice questions in Moodle XML format"""

    def to_moodle_xml(self, question: Question, lang_order: list[str] | None = None) -> str:
        if lang_order is None:
            lang_order = ['sv', 'en']

        question_text = _get_bilingual_text(question, 'question', lang_order, escape_html=False)
        alternatives = _get_bilingual_alternatives(question, lang_order)
        correct_answers = _get_bilingual_answers(question, lang_order)

        if not question_text:
            return f"<!-- Question {question.id} has no content -->"

        if not alternatives:
            return f"<!-- Question {question.id} has no answer alternatives -->"

        return _create_question_manually(
            question.id,
            question.subject.value,
            "multichoice",
            question_text,
            None,  # No general feedback for now
            moodle_name_override=question.moodle_name_override,
            single="true",
            alternatives=alternatives,
            correct_answers=correct_answers
        )


class MoodleXMLNumberGenerator(NumberGenerator):
    """Generator for numerical questions in Moodle XML format"""

    def to_moodle_xml(self, question: Question, lang_order: list[str] | None = None) -> str:
        question_text = _get_bilingual_text(question, 'question', lang_order)
        answer_text = _get_bilingual_text(question, 'answer', lang_order)
        
        if not question_text:
            return f"<!-- Question {question.id} has no content -->"
        
        # Create question element
        question_elem = ET.Element("question", type="numerical")
        
        # Question name
        name_elem = ET.SubElement(question_elem, "name")
        name_text_elem = ET.SubElement(name_elem, "text")
        name_text_elem.text = question.moodle_name_override or f"Question {question.id} - {question.subject.value}"
        
        # Question text with CDATA
        questiontext_elem = ET.SubElement(question_elem, "questiontext", format="html")
        questiontext_text_elem = ET.SubElement(questiontext_elem, "text")
        questiontext_text_elem.text = "PLACEHOLDER_QUESTIONTEXT"
        
        # Default grade
        defaultgrade_elem = ET.SubElement(question_elem, "defaultgrade")
        defaultgrade_elem.text = "1"
        
        # General feedback
        generalfeedback_elem = ET.SubElement(question_elem, "generalfeedback", format="html")
        generalfeedback_text_elem = ET.SubElement(generalfeedback_elem, "text")
        generalfeedback_text_elem.text = ""
        
        # Answer
        if answer_text:
            answer_elem = ET.SubElement(question_elem, "answer", fraction="100")
            answer_text_elem = ET.SubElement(answer_elem, "text")
            answer_text_elem.text = escape(answer_text)
            
            # Tolerance (10% of the answer by default)
            tolerance_elem = ET.SubElement(answer_elem, "tolerance")
            try:
                numeric_answer = float(answer_text)
                tolerance_elem.text = str(abs(numeric_answer) * 0.1)
            except ValueError:
                tolerance_elem.text = "0"
            
            # Feedback
            feedback_elem = ET.SubElement(answer_elem, "feedback", format="html")
            feedback_text_elem = ET.SubElement(feedback_elem, "text")
            feedback_text_elem.text = ""
        
        return _create_xml_with_cdata(question_elem, question_text)


class MoodleXMLCodeGenerator(CodeGenerator):
    """Generator for code assignment questions in Moodle XML format"""

    def to_moodle_xml(self, question: Question, lang_order: list[str] | None = None) -> str:
        question_text = _get_bilingual_text(question, 'question', lang_order)

        if not question_text:
            return f"<!-- Question {question.id} has no content -->"

        # Code assignments are exported as essay questions in Moodle
        # No answer feedback is provided since answers are not available
        return _create_question_manually(
            question.id,
            question.subject.value,
            "essay",
            question_text,
            None,  # No answer feedback
            moodle_name_override=question.moodle_name_override
        )


# Create Moodle XML generator registry
moodle_xml_registry = _GeneratorRegistry()
moodle_xml_registry.register_generator(MoodleXMLShortAnswerGenerator())
moodle_xml_registry.register_generator(MoodleXMLEssayGenerator())
moodle_xml_registry.register_generator(MoodleXMLMultipleChoiceGenerator())
moodle_xml_registry.register_generator(MoodleXMLSingleChoiceGenerator())
moodle_xml_registry.register_generator(MoodleXMLNumberGenerator())
moodle_xml_registry.register_generator(MoodleXMLCodeGenerator())


class MoodleXMLDropDownGenerator(DropDownGenerator):
    """Generator for dropdown questions in Moodle XML format.

    Since dropdown questions in the CSV don't have proper answer alternatives,
    we convert them to short answer questions in Moodle XML format.
    """

    def to_moodle_xml(self, question: Question, lang_order: list[str] | None = None) -> str:
        # Use manual XML creation for short answer since dropdown data is incomplete
        question_text = _get_bilingual_text(question, 'question', lang_order, escape_html=False)
        answer_text = _get_bilingual_text(question, 'answer', lang_order, escape_html=True)

        if not question_text:
            return f"<!-- Question {question.id} has no content -->"

        return _create_question_manually(
            question.id,
            question.subject.value,
            "shortanswer",
            question_text,
            None,  # No general feedback
            moodle_name_override=question.moodle_name_override,
            answer_text=answer_text if answer_text else None
        )


class MoodleXMLMultiQuestionGenerator(MultiQuestionGenerator):
    """Generator for multi-question types in Moodle XML format.
    
    This generates multiple separate questions for each sub-question in the multi-question,
    since Moodle doesn't have a direct equivalent to multi-questions.
    """
    
    def to_moodle_xml(self, question: Question, lang_order: list[str] | None = None) -> str:
        if lang_order is None:
            lang_order = ['sv', 'en']
        
        # Check if question has content in any language
        if not question.content:
            return f"<!-- Question {question.id} has no content -->"
        
        # Use the first available language to get the base content structure
        # Since we're using bilingual questions, we just need one to get the structure
        primary_lang = None
        for lang in lang_order:
            if lang in question.content:
                primary_lang = lang
                break
        
        if not primary_lang:
            return f"<!-- Question {question.id} has no content in specified languages -->"
        
        content = question.content[primary_lang]
        base_content = content.question
        # believe it or not this is also a comma separated list of answers, one for each sub-question...
        answers = content.answer.split(",") if content.answer else []
        variants: list[str] = content.q_alternatives or []
        variants_ans: list[str] = content.ans_alternatives or [] # each is either "essay" or a comma separated list of alternatives...

        if len(variants) != len(variants_ans):
            return f"<!-- Question {question.id} has mismatched number of question and answer alternatives -->"

        output_parts = []
        for i, (var, var_ans) in enumerate(zip(variants, variants_ans)):
            if var_ans.strip() == "essay":
                # Create bilingual content for sub-question
                sub_content = {}
                for lang in lang_order:
                    if lang in question.content:
                        sub_content[lang] = QuestionContent(
                            question=f"{question.content[lang].question} - {var}", 
                            answer=answers[i] if i < len(answers) else None
                        )
                
                sub_question = Question(
                    id=question.id * 100 + i,  # Generate a new ID based on parent question ID
                    chapter=question.chapter,
                    type=QuestionType.essay,
                    subject=question.subject,
                    content=sub_content,
                    moodle_name_override=question.moodle_name_override  # Inherit parent's override
                )
                essay_gen = MoodleXMLEssayGenerator()
                output_parts.append(essay_gen.to_moodle_xml(sub_question, lang_order))
                continue

            # comma separated list of alternatives, sc is inferred from the broken CSV
            # Create bilingual content for sub-question
            sub_content = {}
            for lang in lang_order:
                if lang in question.content:
                    sub_content[lang] = QuestionContent(
                        question=f"{question.content[lang].question} - {var}", 
                        answer=answers[i] if i < len(answers) else None, 
                        ans_alternatives=[a.strip() for a in var_ans.split(",")] if var_ans.count(",") > 0 else None
                    )
            
            sub_question = Question(
                id=question.id * 100 + i,  # Generate a new ID based on parent question ID
                chapter=question.chapter,
                type=QuestionType.sc,
                subject=question.subject,
                content=sub_content,
                moodle_name_override=question.moodle_name_override  # Inherit parent's override
            )
            sc_gen = MoodleXMLSingleChoiceGenerator()
            output_parts.append(sc_gen.to_moodle_xml(sub_question, lang_order))

        return "\n\n".join(output_parts)


moodle_xml_registry.register_generator(MoodleXMLDropDownGenerator())
moodle_xml_registry.register_generator(MoodleXMLMultiQuestionGenerator())
# Note: Drop down and multi-question generators now have Moodle XML support
