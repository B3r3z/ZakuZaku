"""
Interfejs użytkownika w terminalu
"""

import os
import time
from typing import List, Optional
from src.quiz_manager import QuizManager
from src.database import Database


class TerminalUI:
    """Interfejs użytkownika w terminalu"""
    
    def __init__(self, quiz_manager: QuizManager, database: Database):
        self.quiz_manager = quiz_manager
        self.db = database
        self.running = True
    
    def clear_screen(self):
        """Czyści ekran terminala"""
        os.system('clear' if os.name == 'posix' else 'cls')
    
    def print_header(self, title: str):
        """Wyświetla nagłówek"""
        print(f"\n{'='*60}")
        print(f"🎓 {title.center(54)} 🎓")
        print(f"{'='*60}")
    
    def print_menu(self, options: List[str], title: str = "Menu"):
        """Wyświetla menu z opcjami"""
        self.print_header(title)
        print()
        for i, option in enumerate(options, 1):
            print(f"  {i}. {option}")
        print(f"  0. Wyjście")
        print()
    
    def get_user_choice(self, max_option: int) -> int:
        """Pobiera wybór użytkownika"""
        while True:
            try:
                choice = input(f"Wybierz opcję (0-{max_option}): ").strip()
                choice_int = int(choice)
                if 0 <= choice_int <= max_option:
                    return choice_int
                else:
                    print(f"❌ Proszę podać liczbę od 0 do {max_option}")
            except ValueError:
                print("❌ Proszę podać poprawną liczbę")
            except KeyboardInterrupt:
                return 0
    
    def run(self):
        """Główna pętla aplikacji"""
        while self.running:
            self.show_main_menu()
    
    def show_main_menu(self):
        """Wyświetla główne menu"""
        options = [
            "📚 Wybierz quiz",
            "🎯 Rozpocznij naukę (tryb powtórek)",
            "🎲 Tryb losowy",
            "📊 Wyświetl statystyki",
            "🔍 Problematyczne pytania",
            "⚙️  Ustawienia i narzędzia"
        ]
        
        self.clear_screen()
        self.print_menu(options, "ZakuZaku - Menu Główne")
        
        # Wyświetl informacje o aktualnym quizie
        current_quiz = self.quiz_manager.get_quiz_name()
        print(f"📖 Aktualny quiz: {current_quiz}")
        
        if self.quiz_manager.current_quiz_file:
            stats = self.quiz_manager.get_quiz_statistics()
            print(f"📈 Pytania w bazie: {stats['total_questions']}")
            print(f"✅ Dokładność: {stats['accuracy']:.1f}%")
        
        print()
        
        choice = self.get_user_choice(len(options))
        
        if choice == 0:
            self.running = False
        elif choice == 1:
            self.select_quiz()
        elif choice == 2:
            self.start_quiz("review")
        elif choice == 3:
            self.start_quiz("random")
        elif choice == 4:
            self.show_statistics()
        elif choice == 5:
            self.show_problem_questions()
        elif choice == 6:
            self.show_settings_menu()
    
    def select_quiz(self):
        """Menu wyboru quizu"""
        quizzes = self.quiz_manager.get_available_quizzes()
        
        if not quizzes:
            self.clear_screen()
            self.print_header("Brak quizów")
            print("\n❌ Nie znaleziono żadnych plików z quizami w katalogu 'quizy'")
            print("\n💡 Czy chcesz utworzyć przykładowe quizy?")
            choice = input("Tak (t) / Nie (n): ").strip().lower()
            
            if choice in ['t', 'tak', 'y', 'yes']:
                self.quiz_manager.create_sample_quizzes()
                print("\n✅ Utworzono przykładowe quizy!")
                input("Naciśnij Enter, aby kontynuować...")
                return self.select_quiz()
            else:
                input("Naciśnij Enter, aby wrócić do menu...")
                return
        
        self.clear_screen()
        self.print_header("Wybór Quizu")
        
        print("\nDostępne quizy:")
        for i, quiz_file in enumerate(quizzes, 1):
            quiz_name = os.path.basename(quiz_file).replace('.json', '').replace('.md', '').replace('_', ' ').title()
            print(f"  {i}. {quiz_name}")
            print(f"     📁 {quiz_file}")
        
        print(f"  0. Powrót do menu głównego")
        print()
        
        choice = self.get_user_choice(len(quizzes))
        
        if choice == 0:
            return
        
        selected_quiz = quizzes[choice - 1]
        print(f"\n📥 Ładuję quiz: {selected_quiz}")
        
        if self.quiz_manager.load_quiz(selected_quiz):
            print("✅ Quiz załadowany pomyślnie!")
        else:
            print("❌ Błąd podczas ładowania quizu!")
        
        input("Naciśnij Enter, aby kontynuować...")
    
    def start_quiz(self, mode: str):
        """Rozpoczyna quiz w wybranym trybie"""
        if not self.quiz_manager.current_quiz_file:
            self.clear_screen()
            print("❌ Najpierw wybierz quiz!")
            input("Naciśnij Enter, aby kontynuować...")
            return
        
        # Sprawdź czy są pytania do zadania
        if mode == "review" and not self.quiz_manager.has_questions_for_review():
            self.clear_screen()
            print("🎉 Brawo! Wszystkie pytania zostały opanowane!")
            print("💡 Spróbuj trybu losowego lub wróć później dla powtórek.")
            input("Naciśnij Enter, aby kontynuować...")
            return
        
        self.quiz_manager.reset_session_stats()
        mode_name = "Powtórki (SRS)" if mode == "review" else "Tryb losowy"
        
        self.clear_screen()
        self.print_header(f"Quiz: {self.quiz_manager.get_quiz_name()} - {mode_name}")
        print("\n🎯 Rozpoczynamy quiz!")
        print("💡 Wskazówka: Wpisz 'quit' aby zakończyć quiz")
        print("💡 Wskazówka: Wpisz 'skip' aby pominąć pytanie")
        input("\nNaciśnij Enter, aby rozpocząć...")
        
        questions_count = 0
        max_questions = 20  # Limit pytań na sesję
        
        while questions_count < max_questions:
            question_data = self.quiz_manager.get_next_question(mode)
            
            if not question_data:
                self.clear_screen()
                print("🎉 Excellent! Nie ma więcej pytań do zadania!")
                break
            
            # Wyświetl pytanie
            self.clear_screen()
            self.print_header(f"Pytanie {questions_count + 1}/{max_questions}")
            
            print(f"\n❓ {question_data['question']}")
            
            # Wyświetl opcje dla pytań wielokrotnego wyboru
            if question_data.get('options') and question_data.get('question_type') in ['single_choice', 'multiple_choice']:
                print("\nOpcje:")
                for i, option in enumerate(question_data['options']):
                    letter = chr(ord('A') + i)
                    print(f"  {letter}) {option}")
                
                if question_data.get('question_type') == 'multiple_choice':
                    print("\n💡 Wskazówka: Dla wielokrotnego wyboru podaj litery oddzielone przecinkami (np. A, C)")
                else:
                    print("\n💡 Wskazówka: Podaj literę (A, B, C, D) lub pełną odpowiedź")
            
            print()
            
            # Zmierz czas odpowiedzi
            start_time = time.time()
            user_answer = input("💭 Twoja odpowiedź: ").strip()
            response_time = time.time() - start_time
            
            # Sprawdź czy użytkownik chce zakończyć
            if user_answer.lower() in ['quit', 'exit', 'koniec']:
                break
            
            # Sprawdź czy użytkownik chce pominąć
            if user_answer.lower() in ['skip', 'pomiń']:
                print("⏭️  Pytanie pominięte")
                time.sleep(1)
                continue
            
            # Sprawdź odpowiedź
            is_correct = self.quiz_manager.check_answer(
                question_data['db_id'],
                user_answer,
                question_data['correct_answer'],
                question_data.get('question_type', 'text'),
                question_data.get('options'),
                question_data.get('correct_answers'),
                response_time
            )
            
            # Wyświetl wynik
            if is_correct:
                print("✅ Poprawnie!")
            else:
                print(f"❌ Błędna odpowiedź!")
                print(f"💡 Poprawna odpowiedź: {question_data['correct_answer']}")
                
                # Dla pytań wielokrotnego wyboru pokaż dodatkowe informacje
                if question_data.get('question_type') == 'multiple_choice' and question_data.get('correct_answers'):
                    print("💡 Poprawne opcje:")
                    options = question_data.get('options', [])
                    for answer in question_data['correct_answers']:
                        # Znajdź literę dla odpowiedzi
                        for i, option in enumerate(options):
                            if option.strip().lower() == answer.strip().lower():
                                letter = chr(ord('A') + i)
                                print(f"   {letter}) {option}")
                                break
            
            print(f"⏱️  Czas odpowiedzi: {response_time:.2f}s")
            
            questions_count += 1
            time.sleep(2)
        
        # Pokaż statystyki sesji
        self.show_session_results()
    
    def show_session_results(self):
        """Wyświetla wyniki sesji"""
        stats = self.quiz_manager.get_session_stats()
        
        self.clear_screen()
        self.print_header("Wyniki Sesji")
        
        print(f"\n📊 Statystyki:")
        print(f"   Zadane pytania: {stats['questions_asked']}")
        print(f"   Poprawne odpowiedzi: {stats['correct_answers']}")
        print(f"   Dokładność: {stats['accuracy']:.1f}%")
        print(f"   Czas sesji: {stats['elapsed_time']:.0f}s")
        
        # Oceń wyniki
        if stats['accuracy'] >= 90:
            print("\n🏆 Fantastyczne wyniki! Jesteś mistrzem!")
        elif stats['accuracy'] >= 75:
            print("\n👍 Bardzo dobre wyniki! Tak trzymaj!")
        elif stats['accuracy'] >= 60:
            print("\n📚 Nieźle! Jeszcze trochę nauki i będzie perfekcyjnie!")
        else:
            print("\n💪 Nie poddawaj się! Praktyka czyni mistrza!")
        
        input("\nNaciśnij Enter, aby wrócić do menu...")
    
    def show_statistics(self):
        """Wyświetla statystyki"""
        self.clear_screen()
        self.print_header("Statystyki")
        
        # Statystyki aktualnego quizu
        if self.quiz_manager.current_quiz_file:
            quiz_stats = self.quiz_manager.get_quiz_statistics()
            print(f"\n📖 Quiz: {self.quiz_manager.get_quiz_name()}")
            print(f"   Pytania w bazie: {quiz_stats['total_questions']}")
            print(f"   Udzielone odpowiedzi: {quiz_stats['total_answers']}")
            print(f"   Poprawne odpowiedzi: {quiz_stats['correct_answers']}")
            print(f"   Dokładność: {quiz_stats['accuracy']:.1f}%")
            print(f"   Opanowane pytania: {quiz_stats['learned_questions']}")
            print(f"   Średnia trudność: {quiz_stats['avg_difficulty']:.2f}")
            if quiz_stats['avg_response_time']:
                print(f"   Średni czas odpowiedzi: {quiz_stats['avg_response_time']:.2f}s")
        
        # Globalne statystyki
        global_stats = self.quiz_manager.get_global_statistics()
        print(f"\n🌍 Statystyki globalne:")
        print(f"   Wszystkie pytania: {global_stats['total_questions']}")
        print(f"   Wszystkie odpowiedzi: {global_stats['total_answers']}")
        print(f"   Globalna dokładność: {global_stats['accuracy']:.1f}%")
        print(f"   Opanowane pytania: {global_stats['learned_questions']}")
        
        input("\nNaciśnij Enter, aby wrócić do menu...")
    
    def show_problem_questions(self):
        """Wyświetla problematyczne pytania"""
        if not self.quiz_manager.current_quiz_file:
            self.clear_screen()
            print("❌ Najpierw wybierz quiz!")
            input("Naciśnij Enter, aby kontynuować...")
            return
        
        problems = self.quiz_manager.get_problem_questions()
        
        self.clear_screen()
        self.print_header("Problematyczne Pytania")
        
        if not problems:
            print("\n🎉 Świetnie! Brak problematycznych pytań!")
            print("💡 Wszystkie pytania są dobrze opanowane.")
        else:
            print(f"\n🔍 Znaleziono {len(problems)} problematycznych pytań:")
            print("\n" + "="*60)
            
            for i, (q_id, question, answer, total, correct, accuracy) in enumerate(problems, 1):
                print(f"\n{i}. {question}")
                print(f"   💡 Odpowiedź: {answer}")
                print(f"   📊 Dokładność: {accuracy*100:.1f}% ({correct}/{total})")
                print("-" * 40)
        
        input("\nNaciśnij Enter, aby wrócić do menu...")
    
    def show_settings_menu(self):
        """Wyświetla menu ustawień"""
        options = [
            "📁 Utwórz przykładowe quizy",
            "🗂️  Pokaż lokalizację plików",
            "🔧 Informacje o aplikacji"
        ]
        
        self.clear_screen()
        self.print_menu(options, "Ustawienia i Narzędzia")
        
        choice = self.get_user_choice(len(options))
        
        if choice == 0:
            return
        elif choice == 1:
            self.quiz_manager.create_sample_quizzes()
            print("\n✅ Utworzono przykładowe quizy w katalogu 'quizy'!")
            input("Naciśnij Enter, aby kontynuować...")
        elif choice == 2:
            self.show_file_locations()
        elif choice == 3:
            self.show_about()
    
    def show_file_locations(self):
        """Wyświetla informacje o lokalizacji plików"""
        self.clear_screen()
        self.print_header("Lokalizacja Plików")
        
        current_dir = os.getcwd()
        print(f"\n📁 Katalog roboczy: {current_dir}")
        print(f"📚 Quizy: {current_dir}/quizy/")
        print(f"🗄️  Baza danych: {current_dir}/data/zakuzaku.db")
        
        print("\n📝 Obsługiwane formaty:")
        print("   • JSON (.json) - strukturalne quizy")
        print("   • Markdown (.md) - proste quizy tekstowe")
        
        print("\n💡 Przykład pliku JSON:")
        print('''   {
     "hello": "cześć",
     "goodbye": "żegnaj"
   }''')
        
        print("\n💡 Przykład pliku Markdown:")
        print('''   Q: Jak się masz?
   A: Dobrze, dziękuję
   
   Q: Co robisz?
   A: Uczę się''')
        
        input("\nNaciśnij Enter, aby wrócić...")
    
    def show_about(self):
        """Wyświetla informacje o aplikacji"""
        self.clear_screen()
        self.print_header("O Aplikacji")
        
        print("\n🎓 ZakuZaku - Aplikacja Edukacyjna")
        print("📅 Wersja 1.0")
        print("\n📋 Funkcje:")
        print("   • System inteligentnych powtórek (SRS)")
        print("   • Obsługa plików JSON i Markdown")
        print("   • Śledzenie postępów nauki")
        print("   • Analiza problematycznych pytań")
        print("   • Statystyki i raporty")
        
        print("\n🛠️  Technologie:")
        print("   • Python 3.x")
        print("   • SQLite (baza danych)")
        print("   • Interface terminalowy")
        
        print("\n💡 Algorytm SRS:")
        print("   Pytania są prezentowane w optymalnych interwałach")
        print("   na podstawie Twojej skuteczności w odpowiedziach.")
        
        input("\nNaciśnij Enter, aby wrócić...")
