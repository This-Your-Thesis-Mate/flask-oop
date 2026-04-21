"""
Quiz parsing utilities
"""
import re


class QuizParser:
    """Parser for quiz responses"""
    
    @staticmethod
    def is_choice_line(s):
        """Check if line is a choice option"""
        return len(s) >= 3 and s[0].isalpha() and s[1] == '.' and s[2] == ' '
    
    @staticmethod
    def normalize_answer_text(s):
        """Normalize answer text to label"""
        s = s.strip()
        if not s:
            return s
        if len(s) >= 2 and s[1] in '.)':
            return s[0].upper()
        return s[0].upper()
    
    @staticmethod
    def extract_answers(line, prefix):
        """Extract answers from line"""
        ans_text = line[len(prefix):].strip()
        if ans_text.startswith(':'):
            ans_text = ans_text[1:].strip()
        if ans_text.startswith('**') and ans_text.endswith('**'):
            ans_text = ans_text[2:-2].strip()
        return [a.strip() for a in ans_text.split('|') if a.strip()]
    
    @staticmethod
    def parse_quiz(quiz_string):
        """Parse quiz string into structured format"""
        lines = quiz_string.split('\n')
        quizzes = []
        
        current_question = None
        is_essay = False
        is_multiple_choice_single = False
        is_multiple_choice_multiple = False
        
        def finalize_current():
            nonlocal current_question
            if current_question and ("title" in current_question):
                if "type" not in current_question:
                    if is_essay:
                        current_question["type"] = "Essay"
                    else:
                        current_mode_type = "Multiple" if is_multiple_choice_multiple else "Choice"
                        current_question["type"] = current_mode_type
                quizzes.append(current_question)
            current_question = None
        
        for raw in lines:
            line = raw.strip()
            if not line:
                continue
            
            # Section headers
            if line.startswith("Multiple Choice with One Answer:"):
                finalize_current()
                is_essay = False
                is_multiple_choice_single = True
                is_multiple_choice_multiple = False
                continue
            
            if (line.startswith("Multiple Choice with Multiple Answers:") or 
                line.startswith("Multiple Choice with Multiple Answer:")):
                finalize_current()
                is_essay = False
                is_multiple_choice_single = False
                is_multiple_choice_multiple = True
                continue
            
            if line.startswith("Essay:"):
                finalize_current()
                is_essay = True
                is_multiple_choice_single = False
                is_multiple_choice_multiple = False
                continue
            
            # ESSAY parsing
            if is_essay:
                if line.startswith("Answer:") or line.startswith("Jawaban:") or line.startswith("**Answer:**"):
                    if current_question is None:
                        current_question = {"title": "", "answer": ""}
                    
                    if line.startswith("Answer:"):
                        ans = line[len("Answer:"):].strip()
                    elif line.startswith("Jawaban:"):
                        ans = line[len("Jawaban:"):].strip()
                    else:
                        ans = line[len("**Answer:**"):].strip()
                    
                    current_question["answer"] = ans
                    current_question["type"] = "Essay"
                    finalize_current()
                else:
                    qtext = line
                    if qtext[0].isdigit() and '.' in qtext:
                        qtext = qtext.split('.', 1)[1].strip()
                    if current_question is None:
                        current_question = {}
                    current_question["title"] = qtext
                continue
            
            # MULTIPLE CHOICE parsing
            if is_multiple_choice_single or is_multiple_choice_multiple:
                # New question starting with number
                if line[0].isdigit() and '.' in line:
                    finalize_current()
                    _, qtext = line.split('.', 1)
                    current_question = {"title": qtext.strip(), "choices": []}
                    continue
                
                # Choice line
                if QuizParser.is_choice_line(line):
                    if current_question is None:
                        current_question = {"title": "", "choices": []}
                    current_question["choices"].append(line)
                    continue
                
                # Answer line
                lowered = line.lower()
                prefixes = []
                if lowered.startswith("answer:"):
                    prefixes.append("Answer:")
                if lowered.startswith("jawaban:"):
                    prefixes.append("Jawaban:")
                if line.startswith("**Answer:**"):
                    prefixes.append("**Answer:**")
                
                if prefixes:
                    if current_question is None:
                        current_question = {"title": "", "choices": []}
                    
                    answers_raw = None
                    for p in prefixes:
                        if line.startswith(p):
                            answers_raw = QuizParser.extract_answers(line, p)
                            break
                    answers_raw = answers_raw or []
                    
                    # Map labels to full choice text
                    mapped_answers = []
                    choices = current_question.get("choices", [])
                    if choices:
                        label_map = {}
                        for c in choices:
                            label = c[0].upper() if c and c[0].isalpha() else None
                            if label:
                                label_map[label] = c
                        for a in answers_raw:
                            label = QuizParser.normalize_answer_text(a)
                            mapped_answers.append(label_map.get(label, a))
                    else:
                        mapped_answers = answers_raw
                    
                    current_question["answer"] = mapped_answers
                    current_question["type"] = "Multiple" if is_multiple_choice_multiple else "Choice"
                    finalize_current()
                    continue
                
                # Other text in MC mode
                if current_question is None:
                    current_question = {"title": line, "choices": []}
                else:
                    if "title" in current_question and current_question["title"]:
                        current_question["title"] += " " + line
                    else:
                        current_question["title"] = line
                continue
            
            # Default: treat as essay title
            if current_question is None:
                current_question = {"title": line}
        
        finalize_current()
        return quizzes


# Singleton instance
quiz_parser = QuizParser()
