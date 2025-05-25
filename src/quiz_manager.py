"""
Menedżer quizów - główna logika aplikacji
"""

import time
import random
from typing import List, Dict, Optional
from src.quiz_parser import QuizParser, Question
from src.database import Database


class QuizManager:
    """Główny menedżer quizów obsługujący logikę aplikacji"""
    
    def __init__(self, database: Database):
        self.db = database
        self.current_quiz_file = None
        self.current_questions = []
        self.session_stats = {
            'questions_asked': 0,
            'correct_answers': 0,
            'start_time': time.time()
        }
    
    def load_quiz(self, file_path: str) -> bool:
        """Ładuje quiz z pliku"""
        try:
            questions = QuizParser.parse_file(file_path)
            if not questions:
                return False
            
            self.current_quiz_file = file_path
            self.current_questions = questions
            
            # Dodaj pytania do bazy danych
            for question in questions:
                self.db.add_question(
                    quiz_file=file_path,
                    question_id=question.id,
                    question_text=question.question,
                    correct_answer=question.answer,
                    question_type=question.question_type,
                    options=question.options,
                    correct_answers=question.correct_answers
                )
            
            return True
        except Exception as e:
            print(f"❌ Błąd podczas ładowania quizu: {e}")
            return False
    
    def get_available_quizzes(self) -> List[str]:
        """Zwraca listę dostępnych plików z quizami"""
        return QuizParser.get_quiz_files()
    
    def get_next_question(self, mode: str = "review") -> Optional[Dict]:
        """Pobiera następne pytanie do zadania"""
        if mode == "review":
            # Tryb powtórek - pytania na podstawie SRS
            questions_data = self.db.get_questions_for_review(
                quiz_file=self.current_quiz_file,
                limit=1
            )
        elif mode == "random":
            # Tryb losowy - wszystkie pytania z aktualnego quizu
            questions_data = self.db.get_questions_for_review(
                quiz_file=self.current_quiz_file,
                limit=100
            )
            if questions_data:
                questions_data = [random.choice(questions_data)]
        else:
            return None
        
        if not questions_data:
            return None
        
        question_data = questions_data[0]
        
        # Parsuj opcje i poprawne odpowiedzi z JSON
        import json
        options = None
        correct_answers = None
        
        if question_data[9]:  # options
            try:
                options = json.loads(question_data[9])
            except:
                options = None
                
        if question_data[10]:  # correct_answers
            try:
                correct_answers = json.loads(question_data[10])
            except:
                correct_answers = None
        
        return {
            'db_id': question_data[0],
            'quiz_file': question_data[1],
            'question_id': question_data[2],
            'question': question_data[3],
            'correct_answer': question_data[4],
            'next_review': question_data[5],
            'difficulty': question_data[6],
            'repetitions': question_data[7],
            'question_type': question_data[8] or 'text',
            'options': options,
            'correct_answers': correct_answers
        }
    
    def check_answer(self, question_db_id: int, user_answer: str, correct_answer: str, 
                    question_type: str = 'text', options: list = None, correct_answers: list = None, 
                    response_time: float = None) -> bool:
        """Sprawdza odpowiedź użytkownika"""
        
        if question_type == 'single_choice' and options:
            # Pytanie jednokrotnego wyboru (ABCD)
            is_correct = self._check_single_choice_answer(user_answer, correct_answer, options)
        elif question_type == 'multiple_choice' and correct_answers:
            # Pytanie wielokrotnego wyboru
            is_correct = self._check_multiple_choice_answer(user_answer, correct_answers, options)
        else:
            # Pytanie tekstowe (domyślne)
            is_correct = self._check_text_answer(user_answer, correct_answer)
        
        # Zapisz odpowiedź do bazy danych
        self.db.record_answer(question_db_id, user_answer, is_correct, response_time)
        
        # Aktualizuj statystyki sesji
        self.session_stats['questions_asked'] += 1
        if is_correct:
            self.session_stats['correct_answers'] += 1
        
        return is_correct
    
    def _check_single_choice_answer(self, user_answer: str, correct_answer: str, options: list) -> bool:
        """Sprawdza odpowiedź dla pytania jednokrotnego wyboru"""
        user_normalized = user_answer.strip().lower()
        
        # Sprawdź czy użytkownik podał literę (A, B, C, D)
        if len(user_normalized) == 1 and user_normalized.upper() in 'ABCD':
            letter_index = ord(user_normalized.upper()) - ord('A')
            if 0 <= letter_index < len(options):
                user_answer_text = options[letter_index]
                return user_answer_text.strip().lower() == correct_answer.strip().lower()
        
        # Sprawdź czy użytkownik podał pełną odpowiedź
        return user_normalized == correct_answer.strip().lower()
    
    def _check_multiple_choice_answer(self, user_answer: str, correct_answers: list, options: list = None) -> bool:
        """Sprawdza odpowiedź dla pytania wielokrotnego wyboru"""
        user_normalized = user_answer.strip().lower()
        
        # Obsługa liter (A, B, C, D)
        if all(c in 'abcd, ' for c in user_normalized):
            user_letters = [c.upper() for c in user_normalized if c.upper() in 'ABCD']
            user_answers = []
            
            if options:
                for letter in user_letters:
                    letter_index = ord(letter) - ord('A')
                    if 0 <= letter_index < len(options):
                        user_answers.append(options[letter_index].strip().lower())
            
            correct_normalized = [ans.strip().lower() for ans in correct_answers]
            user_answers_set = set(user_answers)
            correct_set = set(correct_normalized)
            
            return user_answers_set == correct_set
        
        # Obsługa pełnych odpowiedzi oddzielonych przecinkami
        user_parts = [part.strip().lower() for part in user_answer.split(',')]
        correct_normalized = [ans.strip().lower() for ans in correct_answers]
        
        return set(user_parts) == set(correct_normalized)
    
    def _check_text_answer(self, user_answer: str, correct_answer: str) -> bool:
        """Sprawdza odpowiedź dla pytania tekstowego"""
        # Normalizacja odpowiedzi (usunięcie białych znaków, lowercase)
        user_normalized = user_answer.strip().lower()
        correct_normalized = correct_answer.strip().lower()
        
        # Sprawdzenie dokładnego dopasowania
        is_exact_match = user_normalized == correct_normalized
        
        # Sprawdzenie częściowego dopasowania (dla dłuższych odpowiedzi)
        is_partial_match = False
        if len(correct_normalized) > 10:  # Dla dłuższych odpowiedzi
            # Sprawdź czy kluczowe słowa są obecne
            correct_words = set(correct_normalized.split())
            user_words = set(user_normalized.split())
            
            # Jeśli użytkownik podał co najmniej 70% słów kluczowych
            if len(correct_words) > 0:
                match_ratio = len(correct_words.intersection(user_words)) / len(correct_words)
                is_partial_match = match_ratio >= 0.7
        
        return is_exact_match or is_partial_match
    
    def get_session_stats(self) -> Dict:
        """Zwraca statystyki aktualnej sesji"""
        elapsed_time = time.time() - self.session_stats['start_time']
        
        return {
            **self.session_stats,
            'elapsed_time': elapsed_time,
            'accuracy': (self.session_stats['correct_answers'] / max(1, self.session_stats['questions_asked'])) * 100
        }
    
    def get_quiz_statistics(self) -> Dict:
        """Zwraca statystyki aktualnego quizu"""
        return self.db.get_statistics(self.current_quiz_file)
    
    def get_global_statistics(self) -> Dict:
        """Zwraca globalne statystyki"""
        return self.db.get_statistics()
    
    def get_problem_questions(self, limit: int = 10) -> List:
        """Zwraca problematyczne pytania"""
        return self.db.get_problem_questions(self.current_quiz_file, limit)
    
    def create_sample_quizzes(self):
        """Tworzy przykładowe pliki z quizami"""
        QuizParser.create_sample_files()
    
    def reset_session_stats(self):
        """Resetuje statystyki sesji"""
        self.session_stats = {
            'questions_asked': 0,
            'correct_answers': 0,
            'start_time': time.time()
        }
    
    def get_quiz_name(self) -> str:
        """Zwraca nazwę aktualnego quizu"""
        if not self.current_quiz_file:
            return "Brak wybranego quizu"
        
        import os
        return os.path.basename(self.current_quiz_file).replace('.json', '').replace('.md', '').replace('_', ' ').title()
    
    def has_questions_for_review(self) -> bool:
        """Sprawdza czy są pytania gotowe do powtórki"""
        questions = self.db.get_questions_for_review(self.current_quiz_file, limit=1)
        return len(questions) > 0
