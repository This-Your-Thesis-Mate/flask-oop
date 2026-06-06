class Module:
    """Module model"""
    def __init__(self, id, module_name, course_id, course_name=None, ref_module_id=None, siteidentifier=None):
        self.id = id
        self.module_name = module_name
        self.course_id = course_id
        self.course_name = course_name
        self.ref_module_id = ref_module_id
        self.siteidentifier = siteidentifier


class Chunk:
    """Chunk model"""
    def __init__(self, id, module_id, chunk_text, siteidentifier=None):
        self.id = id
        self.module_id = module_id
        self.chunk_text = chunk_text
        self.siteidentifier = siteidentifier


class Annotation:
    """Annotation model"""
    def __init__(self, page_number, text, siteidentifier=None):
        self.page_number = page_number
        self.text = text
        self.siteidentifier = siteidentifier
    
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
