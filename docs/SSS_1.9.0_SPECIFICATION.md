# SSS 1.9.0 — Emotional State Memory

## 1. Cel
Wersja 1.9.0 dodaje dziennik zdarzeń dla autorsko zdefiniowanych szyfrów emocji. Pozwala zapisywać migawki stanów, jawne przejścia między stanami, filtrować historię oraz eksportować i importować zapis w formacie JSON.

## 2. Model zdarzenia
Każdy wpis zawiera:
- \`entry_id\` — unikalny identyfikator zdarzenia;
- \`event_type\` — \`SNAPSHOT\` albo \`TRANSITION\`;
- \`occurred_at\` — czas ISO-8601 z wymaganym offsetem strefy czasowej, normalizowany do UTC;
- \`operator\` — operator źródłowego wyrażenia SSS;
- \`from_symbol_ids\` — symbole stanu poprzedniego (puste dla migawki);
- \`to_symbol_ids\` — symbole stanu zapisanego w zdarzeniu;
- \`previous_entry_id\` — odnośnik do poprzedniego wpisu;
- \`metadata\` — jawne metadane zdarzenia i wyrażenia.

## 3. Migawka i przejście
- \`record_state(...)\` zapisuje migawkę stanu. Może rozpocząć historię lub utworzyć punkt kontrolny.
- \`record_transition(...)\` zapisuje jawne przejście z ostatniego zapisanego stanu do nowego stanu. Wymaga wcześniejszej migawki lub wpisu w historii.
- Przejście zachowuje oba końce relacji i identyfikator poprzedniego wpisu.
- Wpisy są dopisywane; istniejąca historia nie jest nadpisywana przez te metody.

## 4. Czas i kolejność
- Daty muszą mieć strefę czasową (np. \`2026-11-15T10:30:00Z\` lub \`2026-11-15T11:30:00+01:00\`).
- Wpisy są przechowywane w porządku chronologicznym; czas wcześniejszy niż poprzedni wpis jest odrzucany.
- Równe znaczniki czasu są dozwolone; kolejność wpisów rozstrzyga kolejność dodania.
- \`state_at(t)\` zwraca ostatni stan zarejestrowany nie później niż czas \`t\`.

## 5. Historia i wymiana danych
- \`history(...)\` filtruje po zakresie czasu, typie zdarzenia i identyfikatorze symbolu.
- \`to_json()\` eksportuje historię wraz z wersją schematu.
- \`from_json(...)\` odtwarza historię i sprawdza wersję schematu, unikalność ID, chronologię oraz spójność łańcucha przejść.
- JSON jest formatem wymiany i zapisu. Sam moduł przechowuje dane w pamięci procesu; aplikacja integrująca odpowiada za zapis pliku lub bazy danych.

## 6. Prywatność i granice interpretacji
Pamięć zapisuje identyfikatory symboli oraz jawnie podane metadane. Nie odczytuje emocji człowieka, nie diagnozuje i nie wyciąga wniosków o stanie konkretnej osoby. Nie należy umieszczać w metadanych haseł, danych identyfikujących ani niepotrzebnych prywatnych opisów. Moduł nie szyfruje eksportu JSON — ochronę pliku musi zapewnić aplikacja, która go przechowuje.

## 7. Przykład
\`\`\`python
from datetime import datetime, timezone
from sss import EmotionExpression, EmotionStateMemory

memory = EmotionStateMemory()
memory.record_state(
    EmotionExpression("BASE", [{"symbol_id": "E1", "label": "symbol A"}]),
    datetime(2026, 11, 15, 10, 0, tzinfo=timezone.utc),
)
memory.record_transition(
    EmotionExpression("BLEND", [
        {"symbol_id": "E2", "label": "symbol B"},
        {"symbol_id": "E3", "label": "symbol C"},
    ]),
    datetime(2026, 11, 15, 10, 5, tzinfo=timezone.utc),
)
backup = memory.to_json()
restored = EmotionStateMemory.from_json(backup)
print(restored.current_state)
\`\`\`

## 8. Zakres wersji
Wersja 1.9.0 dostarcza lokalny dziennik w pamięci procesu i format wymiany JSON. Nie zawiera synchronizacji sieciowej, szyfrowania danych, automatycznego zapisu na dysk ani mechanizmu oceny emocji.
