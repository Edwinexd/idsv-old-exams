import abc
from enum import Enum
from typing import Dict, Literal

from pydantic import BaseModel


# Question types	
# Type	Explanation
# sa	Short answer questions.
# sc	Single choice questions.
# mc	Multi-choice questions.
# mq	Multi-question questions. Questions where the program will generate a random question from several questions regarding the same subject.
# dq	Drop-down menu questions.
# nq	Number questions.
# 
class QuestionType(Enum):
    essay = "Essay"
    sa = "Short Answer"
    sc = "Single Choice"
    mc = "Multi Choice"
    mq = "Multi Question" # generates a questions
    dq = "Drop Down"
    nq = "Number"

# Subject Explanation
class QuestionSubject(Enum):
    HIS = "History"
    BIN = "Binary Numbers"
    TWO = "Two's Complement"
    DEC = "Decimal Numbers"
    HEX = "Hexadecimal Numbers"
    CHR = "Character Encoding"
    COL = "Color"
    SAM = "Audio Sampling"
    LOG = "Logical Operators"
    OPR = "Operators"
    INR = "Instruction Register"
    PRC = "Program Counter"
    MAL = "Machine Language"
    REG = "Registers"
    BIT = "Bits and Bytes"
    CAR = "Computer Architecture"
    BOL = "Boolean Values"
    MAS = "Machine Instructions"
    MIS = "Special Machine Instructions"
    PRO = "Processes and Processing"
    OPS = "Operating System"
    MEM = "Memory"
    DAT = "Data and Data Processing"
    DDL = "Deadlocks"
    NCO = "Network Connections"
    COM = "Network Communication"
    NET = "Networks in General"
    PRT = "Network Protocols"
    ADR = "IP Addresses"
    CRP = "Cryptation"
    MAW = "Malware"
    HTM = "HTML"
    SER = "Searching and Search Methods"
    RIT = "Recursion and Iteration"
    ALG = "Algorithms"
    VER = "Software Verification"
    COD = "Program Code and Coding in General"
    DTP = "Data Types"
    DTS = "Data Structures"
    SBR = "Subroutines"
    ASB = "Assemblers"
    PRD = "Programming Paradigms"
    CMP = "Compilers"
    CNP = "Concurrent Programming"
    SSI = "Sequence, Selection, and Iteration"
    TRN = "Transactions"
    PRL = "Programming Languages Types"
    AGL = "Agile Working Approach"
    PTN = "Design Patterns"
    DIG = "Diagrams"
    DLC = "Software Development Life Cycle"
    MDL = "Software Modules"
    TST = "Software Testing"
    RLT = "Relations in Software"
    CME = "Software Components and Their Usage"
    SCR = "SCRUM"
    SFD = "Software Development in General"
    CCS = "Coupling and Cohesion"
    MDN = "Modelling"
    PTR = "Data Pointers"
    DBS = "Databases and Database Management Systems"
    DMN = "Data Mining"
    DRM = "Database Relation Models"
    TDG = "3D-Graphics"
    ANM = "Computer Animations"
    LIG = "Computer Lighting"
    AI = "Artificial Intelligence"
    MCL = "Machine Learning"
    NEN = "Neural Networks"
    NLP = "Natural Language Processing"
    PRB = "Problems"
    PRM = "Problem-Solving Machines"
    CRT = "Cryptography"
    ERR = "Errors"
    VAR = "Variables"
    GAI = "Generative AI"

# question - The question text
# answer - The answer text
# q_alternatives - Question alternatives. Only for questions marked with type mq (multi-question)
# ans_alternatives - Answer alternatives. Only for questions marked with sc (single choice), mc (multi-choice), and mq (multi-question)
class QuestionContent(BaseModel):
    question: str
    answer: str | None = None
    q_alternatives: list[str] | None = None
    ans_alternatives: list[str] | None = None

# Define language code type
LANGUAGE_CODE = Literal["en", "sv"]

# Converts question to LaTeX format
# for one specific question type
class Generator(abc.ABC):
    supported_type: QuestionType

    @abc.abstractmethod
    def to_latex(self, question: "Question", lang: LANGUAGE_CODE, with_answer: bool = False) -> str:
        ...

    def to_moodle_xml(self, question: "Question", lang: LANGUAGE_CODE) -> str:
        """Convert question to Moodle XML format. Default implementation for unsupported types."""
        return f"<!-- Question {question.id} of type {question.type.value} not supported for Moodle XML -->"


class Question(BaseModel):
    id: int
    chapter: int
    type: QuestionType
    subject: QuestionSubject
    content: Dict[LANGUAGE_CODE, QuestionContent]

    def to_latex(self, lang: LANGUAGE_CODE, with_answer: bool = False) -> str:
        content = self.content.get(lang)
        if not content:
            return "Content not available in the specified language."

        return ""
