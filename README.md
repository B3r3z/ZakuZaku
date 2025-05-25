# ZakuZaku - Aplikacja Edukacyjna 🎓

Prosta, darmowa aplikacja edukacyjna w stylu Quizleta, która działa lokalnie w terminalu. Implementuje system inteligentnych powtórek (SRS) do skutecznej nauki.

## ✨ Funkcje

- 📚 **Obsługa różnych formatów**: pliki JSON i Markdown
- 🎯 **Pytania wielokrotnego wyboru**: obsługa pytań ABCD (jedno- i wielokrotnego wyboru)
- 🧠 **System SRS**: inteligentne powtórki oparte na algorytmie rozłożonych powtórzeń
- 📊 **Śledzenie postępów**: szczegółowe statystyki i analiza błędów
- 🎯 **Tryby nauki**: powtórki i tryb losowy
- 🔍 **Analiza problemów**: identyfikacja trudnych pytań
- 💾 **Lokalna baza danych**: wszystkie dane przechowywane lokalnie
- 🚀 **Łatwe rozszerzanie**: prosty format plików z quizami

## 🚀 Instalacja i Uruchomienie

### Wymagania
- Python 3.6 lub nowszy
- Standardowe biblioteki Python (sqlite3, json, re, os, time)

### Uruchomienie
```bash
# Przejdź do katalogu projektu
cd ZakuZaku

# Uruchom aplikację
python main.py
```

## 📖 Jak używać

### 1. Pierwsze uruchomienie
Po pierwszym uruchomieniu aplikacja:
- Utworzy katalog `data/` dla bazy danych
- Zaproponuje utworzenie przykładowych quizów
- Przygotuje strukturę katalogów

### 2. Tworzenie quizów

#### Format JSON - Prosty słownik
```json
{
  "hello": "cześć",
  "goodbye": "żegnaj",
  "please": "proszę",
  "thank you": "dziękuję"
}
```

#### Format JSON - Strukturalny
```json
{
  "title": "Quiz z Historii",
  "questions": [
    {
      "id": "hist_1",
      "question": "Kto był pierwszym królem Polski?",
      "answer": "Bolesław Chrobry",
      "category": "historia",
      "type": "text"
    },
    {
      "id": "hist_2",
      "question": "Które z poniższych miast były stolicami Polski?",
      "options": ["Kraków", "Warszawa", "Gdańsk", "Gniezno"],
      "correct_answers": ["Kraków", "Warszawa", "Gniezno"],
      "answer": "Kraków, Warszawa, Gniezno",
      "type": "multiple_choice",
      "category": "historia"
    },
    {
      "id": "hist_3",
      "question": "W którym roku Polska przyjęła chrześcijaństwo?",
      "options": ["966", "1000", "1025", "955"],
      "answer": "966",
      "type": "single_choice",
      "category": "historia"
    }
  ]
}
```

#### Format Markdown
```markdown
# Quiz: Podstawy Pythona

Q: Jak zdefiniować funkcję w Pythonie?
A: def nazwa_funkcji():

Q: Jakie słowo kluczowe służy do importowania?
A: import

## Jak stworzyć listę?
[]

**Co oznacza PEP?**
Python Enhancement Proposal

Q: Który operator służy do sprawdzania równości?
A) =
B) ==
C) ===
D) eq
Answer: B

Q: Które z poniższych są typami danych w Pythonie?
A) int
B) string  
C) boolean
D) array
Answer: A, B, C
```

### 3. Struktura katalogów
```
ZakuZaku/
├── main.py              # Główny plik aplikacji
├── src/                 # Kod źródłowy
│   ├── database.py      # Obsługa bazy danych
│   ├── quiz_parser.py   # Parsowanie plików z quizami
│   ├── quiz_manager.py  # Logika aplikacji
│   └── ui.py           # Interfejs użytkownika
├── quizy/              # Pliki z quizami (.json, .md)
├── data/               # Baza danych SQLite
└── README.md           # Ten plik
```

## 🎯 Typy pytań

### Pytania tekstowe
Tradycyjne pytania otwarte gdzie użytkownik wpisuje odpowiedź tekstową.

### Pytania jednokrotnego wyboru (ABCD)
Pytania z 2-4 opcjami, gdzie tylko jedna odpowiedź jest poprawna.
- W JSON: ustaw `"type": "single_choice"` i podaj `"options"`
- W Markdown: użyj formatu z opcjami A), B), C), D) i `Answer: A`

### Pytania wielokrotnego wyboru  
Pytania gdzie można wybrać kilka poprawnych odpowiedzi.
- W JSON: ustaw `"type": "multiple_choice"` i podaj `"correct_answers"` jako listę
- W Markdown: użyj `Answer: A, C, D` dla wielu odpowiedzi
- Użytkownik może odpowiadać literami (A, C) lub pełnymi tekstami oddzielonymi przecinkami

## 🧠 System SRS (Spaced Repetition System)

Aplikacja implementuje uproszczony algorytm rozłożonych powtórzeń:

- **Nowe pytania**: pojawiają się natychmiast
- **Poprawne odpowiedzi**: zwiększają interwał powtórzeń
- **Błędne odpowiedzi**: resetują interwał do 1 dnia
- **Współczynnik łatwości**: dostosowuje się do Twoich wyników

### Algorytm interwałów:
1. Pierwsza powtórka: 1 dzień
2. Druga powtórka: 6 dni  
3. Kolejne: poprzedni_interwał × współczynnik_łatwości

## 📊 Funkcje analityczne

### Statystyki sesji
- Liczba zadanych pytań
- Dokładność odpowiedzi
- Czas sesji
- Średni czas odpowiedzi

### Statystyki globalne
- Postęp w nauce dla każdego quizu
- Identyfikacja problematycznych pytań
- Śledzenie długoterminowych trendów

### Analiza problemów
- Automatyczne wykrywanie trudnych pytań
- Statystyki dokładności per pytanie
- Priorytetyzacja powtórek

## 🎮 Tryby nauki

### 1. Tryb powtórek (SRS)
- Prezentuje pytania gotowe do powtórki
- Optymalizuje harmonogram nauki
- Koncentruje się na trudnych materiałach

### 2. Tryb losowy
- Losowe pytania z wybranego quizu
- Przydatny do szybkich powtórek
- Nie wpływa na harmonogram SRS

## 🛠️ Zaawansowane funkcje

### Normalizacja odpowiedzi
- Ignoruje różnice w wielkości liter
- Usuwa nadmiarowe spacje
- Obsługuje częściowe dopasowania dla długich odpowiedzi

### Zarządzanie bazą danych
- Automatyczne tworzenie kopii zapasowych
- Migracje schemy przy aktualizacjach
- Optymalizacja wydajności

### Rozszerzalność
- Łatwe dodawanie nowych formatów plików
- Modularna architektura
- API do integracji z zewnętrznymi narzędziami

## 📝 Przykłady użycia

### Nauka języków obcych
```json
{
  "english_basics": {
    "cat": "kot",
    "dog": "pies", 
    "house": "dom",
    "car": "samochód"
  }
}
```

### Terminologia techniczna
```markdown
# IT Terms

Q: Co oznacza API?
A: Application Programming Interface

Q: Czym jest REST?
A: Representational State Transfer

Q: Co to jest JSON?
A: JavaScript Object Notation
```

### Fakty historyczne
```json
{
  "questions": [
    {
      "question": "Kiedy rozpoczęła się II wojna światowa?",
      "answer": "1 września 1939",
      "category": "historia"
    }
  ]
}
```

## 🔧 Rozwój i wkład

### Struktura kodu
- `database.py`: Operacje na bazie danych SQLite
- `quiz_parser.py`: Parsowanie różnych formatów plików
- `quiz_manager.py`: Główna logika aplikacji i SRS
- `ui.py`: Interfejs terminalowy

### Dodawanie nowych funkcji
1. Dodaj nowy moduł w `src/`
2. Zaimplementuj odpowiednie interfejsy
3. Zaktualizuj `main.py` i `ui.py`
4. Dodaj testy i dokumentację

## 🐛 Rozwiązywanie problemów

### Częste problemy

**Błąd: "Plik nie istnieje"**
- Sprawdź czy plik znajduje się w katalogu `quizy/`
- Upewnij się że ma rozszerzenie `.json` lub `.md`

**Błąd parsowania JSON**
- Sprawdź poprawność składni JSON
- Użyj walidatora JSON online

**Problemy z bazą danych**
- Usuń plik `data/zakuzaku.db` aby przebudować bazę
- Sprawdź uprawnienia do zapisu w katalogu

### Logi i debugging
Dodaj parametr `-v` lub `--verbose` do uruchomienia z dodatkowymi informacjami.

## 📜 Licencja

Ten projekt jest dostępny na licencji MIT. Zobacz plik LICENSE dla szczegółów.

## 🤝 Współpraca

Zapraszamy do współpracy! Możesz pomóc przez:
- Zgłaszanie błędów (issues)
- Proponowanie nowych funkcji
- Tworzenie pull requestów
- Ulepszanie dokumentacji

## 📞 Kontakt

Jeśli masz pytania lub sugestie, utwórz issue w repozytorium projektu.

---

**Miłej nauki! 🎓✨**
