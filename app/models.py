"""
Data models and schemas for the application
"""

class Module:
    """Module model"""
    def __init__(self, id, module_name, course_id, ref_module_id=None):
        self.id = id
        self.module_name = module_name
        self.course_id = course_id
        self.ref_module_id = ref_module_id


class Chunk:
    """Chunk model"""
    def __init__(self, id, module_id, chunk_text):
        self.id = id
        self.module_id = module_id
        self.chunk_text = chunk_text


class Annotation:
    """Annotation model"""
    def __init__(self, page_number, text):
        self.page_number = page_number
        self.text = text
    
    def to_dict(self):
        return {
            "page": f"Page {self.page_number}",
            "page_number": self.page_number,
            "text": self.text
        }


class QuizQuestion:
    """Quiz question model"""
    def __init__(self, title, question_type, choices=None, answer=None):
        self.title = title
        self.type = question_type
        self.choices = choices or []
        self.answer = answer or []
    
    def to_dict(self):
        return {
            "title": self.title,
            "type": self.type,
            "choices": self.choices,
            "answer": self.answer
        }
