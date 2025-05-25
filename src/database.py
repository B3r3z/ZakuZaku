"""
Moduł zarządzający bazą danych SQLite
Przechowuje statystyki użytkownika i historię odpowiedzi
"""

import sqlite3
import json
from datetime import datetime, timedelta
from typing import Dict, List, Tuple, Optional


class Database:
    def __init__(self, db_path: str = "data/zakuzaku.db"):
        self.db_path = db_path
        self._ensure_data_dir()
        self._init_database()
    
    def _ensure_data_dir(self):
        """Tworzy katalog data jeśli nie istnieje"""
        import os
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
    
    def _init_database(self):
        """Inicjalizuje bazę danych i tworzy tabele"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Tabela pytań
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS questions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    quiz_file TEXT NOT NULL,
                    question_id TEXT NOT NULL,
                    question_text TEXT NOT NULL,
                    correct_answer TEXT NOT NULL,
                    question_type TEXT DEFAULT 'text',
                    options TEXT,
                    correct_answers TEXT,
                    UNIQUE(quiz_file, question_id)
                )
            ''')
            
            # Tabela odpowiedzi użytkownika
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS user_answers (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    question_id INTEGER NOT NULL,
                    user_answer TEXT NOT NULL,
                    is_correct BOOLEAN NOT NULL,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    response_time REAL,
                    FOREIGN KEY (question_id) REFERENCES questions (id)
                )
            ''')
            
            # Tabela statystyk SRS
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS srs_stats (
                    question_id INTEGER PRIMARY KEY,
                    difficulty REAL DEFAULT 2.5,
                    interval_days INTEGER DEFAULT 1,
                    repetitions INTEGER DEFAULT 0,
                    next_review DATETIME,
                    ease_factor REAL DEFAULT 2.5,
                    last_review DATETIME,
                    FOREIGN KEY (question_id) REFERENCES questions (id)
                )
            ''')
            
            conn.commit()
    
    def add_question(self, quiz_file: str, question_id: str, question_text: str, correct_answer: str, 
                    question_type: str = 'text', options: List[str] = None, correct_answers: List[str] = None) -> int:
        """Dodaje pytanie do bazy danych"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Konwertuj listy na JSON
            options_json = json.dumps(options, ensure_ascii=False) if options else None
            correct_answers_json = json.dumps(correct_answers, ensure_ascii=False) if correct_answers else None
            
            cursor.execute('''
                INSERT OR REPLACE INTO questions 
                (quiz_file, question_id, question_text, correct_answer, question_type, options, correct_answers)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            ''', (quiz_file, question_id, question_text, correct_answer, question_type, options_json, correct_answers_json))
            
            question_db_id = cursor.lastrowid or self.get_question_db_id(quiz_file, question_id)
            
            # Inicjalizuj statystyki SRS jeśli nie istnieją
            cursor.execute('''
                INSERT OR IGNORE INTO srs_stats (question_id, next_review)
                VALUES (?, ?)
            ''', (question_db_id, datetime.now().isoformat()))
            
            conn.commit()
            return question_db_id
    
    def get_question_db_id(self, quiz_file: str, question_id: str) -> Optional[int]:
        """Pobiera ID pytania z bazy danych"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT id FROM questions 
                WHERE quiz_file = ? AND question_id = ?
            ''', (quiz_file, question_id))
            result = cursor.fetchone()
            return result[0] if result else None
    
    def record_answer(self, question_db_id: int, user_answer: str, is_correct: bool, response_time: float = None):
        """Zapisuje odpowiedź użytkownika"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                INSERT INTO user_answers 
                (question_id, user_answer, is_correct, response_time)
                VALUES (?, ?, ?, ?)
            ''', (question_db_id, user_answer, is_correct, response_time))
            conn.commit()
        
        # Aktualizuj statystyki SRS
        self._update_srs_stats(question_db_id, is_correct)
    
    def _update_srs_stats(self, question_id: int, is_correct: bool):
        """Aktualizuje statystyki SRS na podstawie odpowiedzi"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute('''
                SELECT difficulty, interval_days, repetitions, ease_factor
                FROM srs_stats WHERE question_id = ?
            ''', (question_id,))
            
            result = cursor.fetchone()
            if not result:
                return
            
            difficulty, interval_days, repetitions, ease_factor = result
            
            if is_correct:
                # Odpowiedź poprawna
                if repetitions == 0:
                    interval_days = 1
                elif repetitions == 1:
                    interval_days = 6
                else:
                    interval_days = int(interval_days * ease_factor)
                
                repetitions += 1
                ease_factor = max(1.3, ease_factor + (0.1 - (3 - difficulty) * (0.08 + (3 - difficulty) * 0.02)))
            else:
                # Odpowiedź błędna
                repetitions = 0
                interval_days = 1
                ease_factor = max(1.3, ease_factor - 0.2)
            
            next_review = datetime.now() + timedelta(days=interval_days)
            
            cursor.execute('''
                UPDATE srs_stats 
                SET difficulty = ?, interval_days = ?, repetitions = ?, 
                    ease_factor = ?, next_review = ?, last_review = ?
                WHERE question_id = ?
            ''', (difficulty, interval_days, repetitions, ease_factor, 
                  next_review.isoformat(), datetime.now().isoformat(), question_id))
            
            conn.commit()
    
    def get_questions_for_review(self, quiz_file: str = None, limit: int = 20) -> List[Tuple]:
        """Pobiera pytania gotowe do powtórki"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT q.id, q.quiz_file, q.question_id, q.question_text, q.correct_answer,
                       s.next_review, s.difficulty, s.repetitions, q.question_type, q.options, q.correct_answers
                FROM questions q
                LEFT JOIN srs_stats s ON q.id = s.question_id
                WHERE (s.next_review IS NULL OR s.next_review <= ?)
            '''
            params = [datetime.now().isoformat()]
            
            if quiz_file:
                query += ' AND q.quiz_file = ?'
                params.append(quiz_file)
            
            query += ' ORDER BY s.next_review ASC, s.difficulty DESC LIMIT ?'
            params.append(limit)
            
            cursor.execute(query, params)
            return cursor.fetchall()
    
    def get_statistics(self, quiz_file: str = None) -> Dict:
        """Pobiera statystyki użytkownika"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Podstawowe statystyki
            base_query = '''
                SELECT 
                    COUNT(*) as total_answers,
                    SUM(CASE WHEN is_correct THEN 1 ELSE 0 END) as correct_answers,
                    AVG(response_time) as avg_response_time
                FROM user_answers ua
                JOIN questions q ON ua.question_id = q.id
            '''
            
            if quiz_file:
                base_query += ' WHERE q.quiz_file = ?'
                cursor.execute(base_query, (quiz_file,))
            else:
                cursor.execute(base_query)
            
            result = cursor.fetchone()
            total_answers, correct_answers, avg_response_time = result
            
            # Statystyki SRS
            srs_query = '''
                SELECT 
                    COUNT(*) as total_questions,
                    SUM(CASE WHEN repetitions > 0 THEN 1 ELSE 0 END) as learned_questions,
                    AVG(difficulty) as avg_difficulty
                FROM srs_stats s
                JOIN questions q ON s.question_id = q.id
            '''
            
            if quiz_file:
                srs_query += ' WHERE q.quiz_file = ?'
                cursor.execute(srs_query, (quiz_file,))
            else:
                cursor.execute(srs_query)
            
            srs_result = cursor.fetchone()
            total_questions, learned_questions, avg_difficulty = srs_result
            
            return {
                'total_questions': total_questions or 0,
                'total_answers': total_answers or 0,
                'correct_answers': correct_answers or 0,
                'accuracy': (correct_answers / total_answers * 100) if total_answers > 0 else 0,
                'avg_response_time': avg_response_time or 0,
                'learned_questions': learned_questions or 0,
                'avg_difficulty': avg_difficulty or 2.5
            }
    
    def get_problem_questions(self, quiz_file: str = None, limit: int = 10) -> List[Tuple]:
        """Pobiera pytania z najgorszymi wynikami"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            query = '''
                SELECT q.id, q.question_text, q.correct_answer,
                       COUNT(ua.id) as total_attempts,
                       SUM(CASE WHEN ua.is_correct THEN 1 ELSE 0 END) as correct_attempts,
                       (SUM(CASE WHEN ua.is_correct THEN 1 ELSE 0 END) * 1.0 / COUNT(ua.id)) as accuracy
                FROM questions q
                JOIN user_answers ua ON q.id = ua.question_id
            '''
            
            if quiz_file:
                query += ' WHERE q.quiz_file = ?'
                params = [quiz_file]
            else:
                params = []
            
            query += '''
                GROUP BY q.id
                HAVING total_attempts >= 3
                ORDER BY accuracy ASC, total_attempts DESC
                LIMIT ?
            '''
            params.append(limit)
            
            cursor.execute(query, params)
            return cursor.fetchall()
