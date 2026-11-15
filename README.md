# SSS — Spatial Symbol System

**Emotion Cipher System** — przestrzenny system zapisu, kompozycji i odczytu autorsko zdefiniowanych szyfrów emocji.

## Wersje
- **1.7.0 — Emotion Cipher Engine:** kodowanie i dekodowanie symboli emocjonalnych.
- **1.8.0 — Emotional Pattern Recognition:** deterministyczne rozpoznawanie zatwierdzonych konfiguracji symboli.
- **1.9.0 — Emotional State Memory:** dziennik stanów i jawnych przejść z eksportem/importem JSON.
- **2.0.0 — Spatial Emotion Intelligence:** siatka 7×7×7, pozycje względne, sąsiedztwo i rozpoznawanie przestrzennych reguł.

## Zasada nadrzędna
SSS interpretuje znaczenia przypisane przez autora. Nie przypisuje automatycznie emocji prawdziwym osobom ani nie traktuje kodu jako diagnozy psychologicznej. Dopasowanie wzorca oznacza wyłącznie spełnienie jawnej reguły symbolicznej lub przestrzennej.

## Moduły
- `sss/emotion.py` — rejestr symboli, wektory opisowe oraz kompozycje.
- `sss/patterns.py` — regułowe rozpoznawanie wzorców sekwencyjnych.
- `sss/memory.py` — historia stanów, przejścia i wymiana JSON.
- `sss/spatial.py` — kostka 7×7×7, geometria, sąsiedztwo i wzorce przestrzenne.
- `tests/` — testy jednostkowe.

## Uruchomienie testów
Z katalogu głównego repozytorium:
```bash
python -m unittest discover -s tests -v
```

GitHub Actions uruchamia zestaw testów dla wspieranych wersji Pythona przy każdym pushu i pull requeście.

## Geometria SSS 2.0.0
Kostka ma 343 komórki. Współrzędne każdej osi mieszczą się w zakresie 0..6. Komórka może przechowywać wiele symboli, a ich kolejność jest zachowana. Reguły sąsiedztwa mogą używać 6-, 18- lub 26-connectivity.

## Wersja
Aktualna wersja: **2.0.0 — Spatial Emotion Intelligence**.

Moduł przestrzenny eksportuje i importuje siatkę przez JSON. Nie implementuje jeszcze edytora wizualnego, synchronizacji sieciowej ani automatycznego tworzenia znaczeń symboli.
