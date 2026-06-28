class Module:
    def __init__(self, id: int, module_name: str, course_id: int, course_name: str, ref_module_id: int, siteidentifier: str):
        self.id: int = id
        self.module_name: str = module_name
        self.course_id: int = course_id
        self.course_name: str = course_name
        self.ref_module_id: int = ref_module_id
        self.siteidentifier: str = siteidentifier


class Chunk:
    def __init__(self, id: int, module_id: int, chunk_text: str, siteidentifier: str):
        self.id: int = id
        self.module_id: int = module_id
        self.chunk_text: str = chunk_text
        self.siteidentifier: str = siteidentifier


class Annotation:
    def __init__(self, page_number: int, text: str, siteidentifier: str):
        self.page_number: int = page_number
        self.text: str = text
        self.siteidentifier: str = siteidentifier
    
    def to_dict(self) -> dict:
        return {
            "page": f"Page {self.page_number}",
            "page_number": self.page_number,
            "text": self.text
        }


class QuizQuestion:
    def __init__(self, title: str, question_type: str, choices: list , answer: list ):
        self.title: str = title
        self.type: str = question_type
        self.choices: list = choices or []
        self.answer: list = answer or []
    
    def to_dict(self) -> dict:
        return {
            "title": self.title,
            "type": self.type,
            "choices": self.choices,
            "answer": self.answer
        }