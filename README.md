# SSS — Spatial Symbol System

**Emotion Cipher System** — przestrzenny system zapisu, kompozycji i odczytu autorsko zdefiniowanych szyfrów emocji.

## Roadmap
- **1.7.0 — Emotion Cipher Engine:** kodowanie i dekodowanie symboli emocjonalnych.
- **1.8.0 — Emotional Pattern Recognition:** deterministyczne rozpoznawanie zatwierdzonych konfiguracji symboli.
- **1.9.0 — Emotional State Memory:** dziennik stanów i jawnych przejść z eksportem/importem JSON.
- **2.0.0 — Spatial Emotion Intelligence:** przestrzenna interpretacja całych konfiguracji.

## Zasada nadrzędna
SSS interpretuje znaczenia przypisane przez autora. Nie przypisuje automatycznie emocji prawdziwym osobom ani nie traktuje kodu jako diagnozy psychologicznej. Rozpoznanie wzorca oznacza wyłącznie dopasowanie danych symbolicznych do jawnej reguły.

## Moduły
- \`sss/emotion.py\` — rejestr symboli, wektory opisowe oraz kompozycje.
- \`sss/patterns.py\` — regułowe rozpoznawanie wzorców.
- \`sss/memory.py\` — historia stanów, przejścia i wymiana JSON.
- \`tests/\` — testy jednostkowe.

## Uruchomienie testów
Z katalogu głównego repozytorium:
\`\`\`bash
python -m unittest discover -s tests -v
\`\`\`

## Wersja
Aktualna wersja: **1.9.0 — Emotional State Memory**.

Pamięć działa w procesie aplikacji. Dane można eksportować przez \`to_json()\` i odtworzyć przez \`EmotionStateMemory.from_json(...)\`. Moduł nie szyfruje plików i nie zapisuje ich automatycznie na dysku.
