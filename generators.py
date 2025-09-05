import logging
import random
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

        latex = f"\\subsection*{{{content.question} ({question.id})}}\n\n"
        latex += f"\\label{{q:{question.id}:sa:{lang}:{with_answer}}}\n\n"
        if with_answer and content.answer:
            latex += f"\\textbf{{{language.answer}}}: {content.answer}\n\n"
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


registry.register_generator(ShortAnswerGenerator())
registry.register_generator(EssayGenerator())
registry.register_generator(MultipleChoiceGenerator())
registry.register_generator(SingleChoiceGenerator())
registry.register_generator(DropDownGenerator())
registry.register_generator(NumberGenerator())


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
