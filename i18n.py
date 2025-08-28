from pydantic import BaseModel

class Language(BaseModel):
    name: str

    answer: str
    content_not_available_language: str

