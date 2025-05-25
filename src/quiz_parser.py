"""
Moduł parsowania plików z quizami
Obsługuje formaty .json i .md
"""

import json
import re
import os
from typing import List, Dict, Any
from dataclasses import dataclass


@dataclass
class Question:
    """Klasa reprezentująca pojedyncze pytanie"""
    id: str
    question: str
    answer: str
    options: List[str] = None
    category: str = ""
    difficulty: int = 1
    question_type: str = "text"  # "text", "single_choice", "multiple_choice"
    correct_answers: List[str] = None  # Dla pytań wielokrotnego wyboru


class QuizParser:
    """Parser plików z quizami"""
    
    @staticmethod
    def parse_file(file_path: str) -> List[Question]:
        """Parsuje plik z quizem i zwraca listę pytań"""
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Plik {file_path} nie istnieje")
        
        file_extension = os.path.splitext(file_path)[1].lower()
        
        if file_extension == '.json':
            return QuizParser._parse_json(file_path)
        elif file_extension == '.md':
            return QuizParser._parse_markdown(file_path)
        else:
            raise ValueError(f"Nieobsługiwany format pliku: {file_extension}")
    
    @staticmethod
    def _parse_json(file_path: str) -> List[Question]:
        """Parsuje plik JSON z quizem"""
        with open(file_path, 'r', encoding='utf-8') as file:
            data = json.load(file)
        
        questions = []
        
        # Obsługa różnych formatów JSON
        if isinstance(data, list):
            # Format: lista pytań
            for i, item in enumerate(data):
                if isinstance(item, dict):
                    questions.append(QuizParser._create_question_from_dict(item, str(i)))
        
        elif isinstance(data, dict):
            if 'questions' in data:
                # Format: {"questions": [...]}
                for i, item in enumerate(data['questions']):
                    questions.append(QuizParser._create_question_from_dict(item, str(i)))
            else:
                # Format: {"pytanie1": "odpowiedź1", ...}
                for key, value in data.items():
                    questions.append(Question(
                        id=key,
                        question=key,
                        answer=str(value)
                    ))
        
        return questions
    
    @staticmethod
    def _create_question_from_dict(item: Dict[str, Any], default_id: str) -> Question:
        """Tworzy obiekt Question z dictionary"""
        question_id = item.get('id', default_id)
        question_text = item.get('question', item.get('q', ''))
        answer = item.get('answer', item.get('a', ''))
        options = item.get('options', item.get('choices', []))
        category = item.get('category', item.get('topic', ''))
        difficulty = item.get('difficulty', 1)
        question_type = item.get('type', 'text')
        correct_answers = item.get('correct_answers', None)
        
        # Jeśli są opcje i nie ma typu, ustaw odpowiedni typ
        if options and question_type == 'text':
            if correct_answers and len(correct_answers) > 1:
                question_type = 'multiple_choice'
            elif correct_answers or answer:
                question_type = 'single_choice'
        
        # Jeśli answer jest listą, traktuj jako pytanie wielokrotnego wyboru
        if isinstance(answer, list):
            correct_answers = answer
            answer = ", ".join(answer)
            question_type = 'multiple_choice'
        
        return Question(
            id=question_id,
            question=question_text,
            answer=answer,
            options=options,
            category=category,
            difficulty=difficulty,
            question_type=question_type,
            correct_answers=correct_answers
        )
    
    @staticmethod
    def _parse_markdown(file_path: str) -> List[Question]:
        """Parsuje plik Markdown z quizem"""
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        questions = []
        question_id = 0
        
        # Najpierw sprawdź pytania wielokrotnego wyboru (ABCD)
        # Wzorzec dla pytań ABCD
        abcd_pattern = r'Q:\s*(.+?)\n(?:A[).\]]\s*(.+?)\n)(?:B[).\]]\s*(.+?)\n)(?:C[).\]]\s*(.+?)\n)(?:D[).\]]\s*(.+?)\n)(?:Answer:|Odpowiedź:|Poprawna:|Correct:)\s*([A-D,\s]+)(?:\n\n|\n$|$)'
        
        abcd_matches = re.findall(abcd_pattern, content, re.MULTILINE | re.DOTALL)
        
        for match in abcd_matches:
            question_text, opt_a, opt_b, opt_c, opt_d, answer_letters = match
            
            # Zbierz dostępne opcje
            options = []
            option_map = {}
            
            if opt_a and opt_a.strip():
                options.append(opt_a.strip())
                option_map['A'] = opt_a.strip()
            if opt_b and opt_b.strip():
                options.append(opt_b.strip())
                option_map['B'] = opt_b.strip()
            if opt_c and opt_c.strip():
                options.append(opt_c.strip())
                option_map['C'] = opt_c.strip()
            if opt_d and opt_d.strip():
                options.append(opt_d.strip())
                option_map['D'] = opt_d.strip()
            
            if not options:
                continue
            
            # Parsuj poprawne odpowiedzi
            answer_letters = answer_letters.strip().upper()
            correct_letters = [letter.strip() for letter in re.split(r'[,\s]+', answer_letters) if letter.strip() in option_map]
            
            if not correct_letters:
                continue
            
            # Określ typ pytania i odpowiedzi
            correct_answers = [option_map[letter] for letter in correct_letters]
            
            if len(correct_answers) == 1:
                question_type = 'single_choice'
                answer = correct_answers[0]
            else:
                question_type = 'multiple_choice'
                answer = ", ".join(correct_answers)
            
            questions.append(Question(
                id=str(question_id),
                question=question_text.strip(),
                answer=answer,
                options=options,
                question_type=question_type,
                correct_answers=correct_answers
            ))
            question_id += 1
        
        # Jeśli znaleziono pytania ABCD, zwróć je
        if questions:
            return questions
        
        # Wzorce dla pytań tekstowych
        patterns = [
            # Format: Q: pytanie\nA: odpowiedź
            r'Q:\s*(.+?)\nA:\s*(.+?)(?=\nQ:|\n\n|\Z)',
            # Format: ## pytanie\nanswer
            r'##\s*(.+?)\n(.+?)(?=\n##|\n\n|\Z)',
            # Format: **pytanie**\nodpowiedź
            r'\*\*(.+?)\*\*\n(.+?)(?=\n\*\*|\n\n|\Z)',
            # Format: pytanie?\nodpowiedź
            r'(.+\?)\n(.+?)(?=\n.+\?|\n\n|\Z)'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            if matches:
                for question_text, answer in matches:
                    questions.append(Question(
                        id=str(question_id),
                        question=question_text.strip(),
                        answer=answer.strip(),
                        question_type='text'
                    ))
                    question_id += 1
                break  # Użyj pierwszego pasującego wzorca
        
        # Jeśli żaden wzorzec nie pasuje, spróbuj prostego podziału linii
        if not questions:
            lines = content.strip().split('\n')
            for i in range(0, len(lines) - 1, 2):
                if i + 1 < len(lines):
                    questions.append(Question(
                        id=str(i // 2),
                        question=lines[i].strip(),
                        answer=lines[i + 1].strip(),
                        question_type='text'
                    ))
        
        return questions
    
    @staticmethod
    def get_quiz_files(directory: str = "quizy") -> List[str]:
        """Zwraca listę plików z quizami w katalogu"""
        if not os.path.exists(directory):
            return []
        
        quiz_files = []
        for file in os.listdir(directory):
            if file.endswith(('.json', '.md')):
                quiz_files.append(os.path.join(directory, file))
        
        return sorted(quiz_files)
    
    @staticmethod
    def create_sample_files():
        """Tworzy przykładowe pliki z quizami"""
        os.makedirs("quizy", exist_ok=True)
        
        # Przykładowy plik JSON
        sample_json = {
            "title": "Podstawy Pythona",
            "description": "Quiz sprawdzający podstawowe zagadnienia Python",
            "questions": [
                {
                    "id": "py_1",
                    "question": "Jak zdefiniować funkcję w Pythonie?",
                    "answer": "def nazwa_funkcji():",
                    "category": "syntax",
                    "type": "text"
                },
                {
                    "id": "py_2", 
                    "question": "Jakie słowo kluczowe używa się do importowania modułów?",
                    "answer": "import",
                    "category": "modules",
                    "type": "text"
                },
                {
                    "id": "py_3",
                    "question": "Jak stworzyć listę w Pythonie?",
                    "answer": "[]",
                    "options": ["[]", "{}", "()", "||"],
                    "category": "data_types",
                    "type": "single_choice"
                },
                {
                    "id": "py_4",
                    "question": "Które z poniższych są typami danych w Pythonie?",
                    "options": ["int", "string", "boolean", "array"],
                    "correct_answers": ["int", "string", "boolean"],
                    "answer": "int, string, boolean",
                    "category": "data_types",
                    "type": "multiple_choice"
                },
                {
                    "id": "py_5",
                    "question": "Który operator służy do sprawdzania równości w Pythonie?",
                    "options": ["=", "==", "===", "eq"],
                    "answer": "==",
                    "category": "operators",
                    "type": "single_choice"
                }
            ]
        }
        
        with open("quizy/python_podstawy.json", "w", encoding="utf-8") as f:
            json.dump(sample_json, f, ensure_ascii=False, indent=2)
        
        # Przykładowy plik Markdown
        sample_md = """# Quiz: Historia Polski

## Kto był pierwszym królem Polski?
Bolesław Chrobry

## W którym roku Polska przyjęła chrześcijaństwo?
966

**Kto napisał "Pan Tadeusz"?**
Adam Mickiewicz

**W którym roku odzyskaliśmy niepodległość?**
1918

Q: Która bitwa miała miejsce w 1410 roku?
A) Bitwa pod Grunwaldem
B) Bitwa pod Wiedniem
C) Bitwa pod Komarowem
D) Bitwa pod Kircholmem
Answer: A

Q: Które miasta były stolicami Polski?
A) Kraków
B) Warszawa
C) Gniezno
D) Poznań
Answer: A, B, C
"""
        
        with open("quizy/historia_polski.md", "w", encoding="utf-8") as f:
            f.write(sample_md)
        
        # Prosty quiz słownictwa
        simple_vocab = {
            "hello": "cześć",
            "goodbye": "żegnaj",
            "please": "proszę",
            "thank you": "dziękuję",
            "yes": "tak",
            "no": "nie"
        }
        
        with open("quizy/angielski_podstawy.json", "w", encoding="utf-8") as f:
            json.dump(simple_vocab, f, ensure_ascii=False, indent=2)
