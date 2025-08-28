import logging
from typing import Dict
from models import LANGUAGE_CODE, Generator, Question, QuestionType
from i18n import LANGUAGES

class _GeneratorRegistry:
    _generators: Dict[QuestionType, Generator] = {}

    @classmethod
    def register_generator(cls, generator: Generator):
        cls._generators[generator.supported_type] = generator

    @classmethod
    def get_generator(cls, question_type: QuestionType) -> Generator | None:
        return cls._generators.get(question_type)


registry = _GeneratorRegistry()

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

        latex = f"\\subsection{{{content.question}}}\n\n"
        latex += f"\\label{{q:{question.id}:sa:{lang}:{with_answer}}}\n\n"
        if with_answer and content.answer:
            latex += f"\\textbf{{{language.answer}}}: {content.answer}\n\n"
        else:
            # TODO Typable pdf text box?
            latex += "\\vspace{2cm}\n\n"  # Space for answer
            latex += "\\noindent\\makebox[\\textwidth]{\\hrulefill}\n\n"  # Horizontal line
            # jump to answer
            latex += "\\vspace{1cm}\n\n"
            latex += f"\\textit{{{language.answer}}}: \\autoref{{q:{question.id}:sa:{lang}:{True}}}\n\n"

        return latex

# sc = "Single Choice" # generates a question with multiple alternatives, only one is correct

class MultipleChoiceGenerator(Generator):
    supported_type = QuestionType.mc

    def to_latex(self, question: Question, lang: LANGUAGE_CODE, with_answer: bool = False) -> str:
        language = LANGUAGES[lang]
        content = question.content.get(lang)
        if not content:
            logging.warning(f"Question {question.id} does not have content in language {lang}")
            return ""

        latex = f"\\subsection{{{content.question}}}\n\n"
        latex += f"\\label{{q:{question.id}:mc:{lang}:{with_answer}}}\n\n"

        if not content.ans_alternatives:
            logging.warning(f"Question {question.id} does not have answer alternatives for multiple choice")
            return ""

        latex += "\\begin{itemize}\n"
        for alternative in content.ans_alternatives:
            if with_answer and content.answer and alternative == content.answer:
                latex += f"  \\item[$\\square$] \\textbf{{{alternative}}} \\hfill \\textbf{{{language.answer}}}\n"
            else:
                latex += f"  \\item[$\\square$] {alternative}\n"
        latex += "\\end{itemize}\n\n"

        if not with_answer:
            latex += "\\vspace{1cm}\n\n"
            latex += f"\\textit{{{language.answer}}}: \\autoref{{q:{question.id}:mc:{lang}:{True}}}\n\n"

        return latex

# mq = "Multi Question" # generates a questions
# half of the mq questions isn't actually questions either but rather statements which cant be answered to the expected answer
class MultiQuestionGenerator(Generator):
    supported_type = QuestionType.mq

    def to_latex(self, question: Question, lang: LANGUAGE_CODE, with_answer: bool = False) -> str:
        logging.warning("MultiQuestionGenerator is not implemented yet.") # it contains two questions really, both will be generated
        return ""


# dq = "Drop Down"
# dq is fucked in the provided CSV as no answer alternatives are given, ???

# nq = "Number"




registry.register_generator(ShortAnswerGenerator())
