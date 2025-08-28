from pydantic import BaseModel

class Language(BaseModel):
    name: str

    answer: str
    content_not_available_language: str


swedish = Language(name="se", answer="Svar", content_not_available_language="Frågan finns inte på detta språk")
english = Language(name="en", answer="Answer", content_not_available_language="The question is not available in this language")

LANGUAGES = {
    "se": swedish,
    "en": english,
}
