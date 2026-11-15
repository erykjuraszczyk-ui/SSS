# SSS 1.8.0 — Emotional Pattern Recognition

## 1. Cel wersji
Wersja 1.8.0 dodaje deterministyczne rozpoznawanie złożonych konfiguracji symboli emocjonalnych. Wzorce są jawnie definiowane przez autora SSS. Silnik nie tworzy psychologicznych wniosków i nie zgaduje znaczenia nieznanych układów.

## 2. Model wzorca
Każdy wzorzec zawiera:
- \`pattern_id\` — stabilny identyfikator;
- \`label\` — autorską nazwę wzorca;
- \`components\` — uporządkowaną krotkę identyfikatorów symboli;
- \`operators\` — opcjonalną listę operatorów, dla których wzorzec jest aktywny;
- \`match_mode\` — sposób dopasowania;
- \`status\` — \`draft\`, \`confirmed\` albo \`retired\`;
- \`priority\` — całkowitą wartość porządkującą wyniki;
- \`metadata_equals\` — opcjonalne warunki równości metadanych.

Tylko wzorce o statusie \`confirmed\` są uwzględniane. Kolejność wyników to priorytet malejąco, a następnie \`pattern_id\` rosnąco.

## 3. Tryby dopasowania
1. **exact** — wszystkie identyfikatory muszą wystąpić w tej samej kolejności i bez dodatkowych składników.
2. **ordered_subsequence** — wszystkie identyfikatory wzorca muszą pojawić się w tej samej kolejności; pomiędzy nimi mogą występować inne symbole.
3. **contains** — wszystkie symbole wzorca muszą być obecne niezależnie od kolejności. Liczba powtórzeń ma znaczenie.

Indeksowanie dopasowanych składników rozpoczyna się od zera i odnosi się do listy składników w wyrażeniu wejściowym.

## 4. Warunki dodatkowe
- \`operators\` ogranicza dopasowanie do wskazanych operatorów. Pusta krotka oznacza dowolny poprawny operator.
- \`metadata_equals\` wymaga dokładnej równości wskazanych pól metadanych na najwyższym poziomie.
- Wzorzec draft lub retired nie jest wynikiem rozpoznania.
- Brak dopasowania zwraca pustą listę.
- Nieprawidłowa struktura wyrażenia powoduje jawny błąd walidacji.

## 5. Przykład użycia
\`\`\`python
from sss import (
    EmotionCipherEngine,
    EmotionPatternRecognizer,
    EmotionSymbol,
    PatternDefinition,
)

engine = EmotionCipherEngine([
    EmotionSymbol("E1", "autorski_symbol_A", status="confirmed"),
    EmotionSymbol("E2", "autorski_symbol_B", status="confirmed"),
])
expression = engine.compose("BLEND", "E1", "E2")

recognizer = EmotionPatternRecognizer([
    PatternDefinition(
        pattern_id="PATTERN_A_B",
        label="Autorska konfiguracja A-B",
        components=("E1", "E2"),
        operators=("BLEND",),
        match_mode="exact",
        status="confirmed",
    )
])
matches = recognizer.recognize(expression)
\`\`\`

## 6. Interpretacja i granice
Rozpoznanie oznacza wyłącznie: „wejściowe symbole spełniają autorską regułę wzorca”. Nie oznacza, że system ustalił, co naprawdę czuje konkretna osoba. Wynik nie jest diagnozą, oceną osobowości ani odczytem stanu psychicznego.

## 7. Zakres wersji
Wersja 1.8.0 rozpoznaje wzorce na poziomie listy składników wyrażenia. Pełna analiza sąsiedztwa komórek i geometrii przestrzennej pozostaje zakresem planowanej wersji 2.0.0.
