#!/usr/bin/env python3
"""
ZakuZaku - Aplikacja edukacyjna z systemem inteligentnych powtórek
Główny plik uruchamiający aplikację
"""

import sys
import os
from src.quiz_manager import QuizManager
from src.database import Database
from src.ui import TerminalUI


def main():
    """Główna funkcja aplikacji"""
    print("🎓 Witaj w ZakuZaku - Twojej aplikacji do nauki!")
    print("=" * 50)
    
    # Inicjalizacja bazy danych
    db = Database()
    
    # Inicjalizacja menedżera quizów
    quiz_manager = QuizManager(db)
    
    # Inicjalizacja interfejsu użytkownika
    ui = TerminalUI(quiz_manager, db)
    
    try:
        ui.run()
    except KeyboardInterrupt:
        print("\n\n👋 Do zobaczenia następnym razem!")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Wystąpił błąd: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
