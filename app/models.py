class Module:
    """Module model"""
    def __init__(self, id, module_name, course_id, course_name=None, ref_module_id=None, tenant_id=None):
        self.id = id
        self.module_name = module_name
        self.course_id = course_id
        self.course_name = course_name
        self.ref_module_id = ref_module_id
        self.tenant_id = tenant_id


class Chunk:
    """Chunk model"""
    def __init__(self, id, module_id, chunk_text, tenant_id=None):
        self.id = id
        self.module_id = module_id
        self.chunk_text = chunk_text
        self.tenant_id = tenant_id


class Annotation:
    """Annotation model"""
    def __init__(self, page_number, text, tenant_id=None):
        self.page_number = page_number
        self.text = text
        self.tenant_id = tenant_id
    
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
