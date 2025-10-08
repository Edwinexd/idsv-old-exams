from pydantic import BaseModel

class Language(BaseModel):
    name: str

    answer: str
    content_not_available_language: str
    content_not_applicable: str
    programming: str


swedish = Language(name="sv", answer="Svar", content_not_available_language="Frågan finns inte på detta språk", content_not_applicable="Ej tillämpligt eller stöd för detta", programming="Programmeringsuppgift")
english = Language(name="en", answer="Answer", content_not_available_language="The question is not available in this language", content_not_applicable="Not applicable or supported", programming="Programming Assignment")

LANGUAGES = {
    "sv": swedish,
    "en": english,
}
