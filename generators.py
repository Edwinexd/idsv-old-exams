from typing import Dict
from models import LANGUAGE_CODE, Generator, Question, QuestionType

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
class ShortAnswerGenerator(Generator):
    supported_type = QuestionType.sa

    def to_latex(self, question: Question, lang: LANGUAGE_CODE, with_answer: bool = False) -> str:
        content = question.content.get(lang)
        if not content:
            return "\\textit{Content not available in the requested language.}\n\n"

        latex = f"\\subsection{{{content.question}}}\n\n"
        latex += f"\\label{{q:{question.id}:sa:{lang}:{with_answer}}}\n\n"
        if with_answer and content.answer:
            latex += f"\\textbf{{Answer}}: {content.answer}\n\n"
        else:
            # TODO Typable pdf text box?
            latex += "\\vspace{2cm}\n\n"  # Space for answer

        return latex

registry.register_generator(ShortAnswerGenerator())
