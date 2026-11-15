# SSS 2.0.0 — Spatial Emotion Intelligence

## 1. Cel wersji
SSS 2.0.0 wprowadza model kostki 7×7×7. Symbole są rozmieszczane w komórkach przestrzennych, a autorskie wzorce mogą uwzględniać pozycję względną, zawartość komórek oraz jawne relacje sąsiedztwa.

Wersja nie nadaje emocjom uniwersalnych znaczeń. Interpretacja wynika wyłącznie z reguł zdefiniowanych i zatwierdzonych przez autora systemu.

## 2. Model przestrzeni
- Rozmiar siatki: 7×7×7, łącznie 343 komórki.
- Współrzędne komórek: \`(x, y, z)\`, każda oś w zakresie 0..6.
- Komórka może zawierać wiele identyfikatorów symboli.
- Kolejność symboli w komórce jest zachowywana.
- Puste komórki nie muszą być zapisywane.
- Siatka nie zmienia ani nie interpretuje semantyki symbolu.

## 3. Sąsiedztwo
Dostępne są trzy jawne definicje sąsiedztwa:
- **6-connectivity** — wspólna ściana (sześć kierunków osiowych);
- **18-connectivity** — wspólna ściana lub krawędź;
- **26-connectivity** — wspólna ściana, krawędź lub narożnik.

Funkcja \`neighbor_coordinates(...)\` zwraca wyłącznie współrzędne mieszczące się w granicach kostki.

## 4. Definicje wzorców przestrzennych
\`SpatialPatternDefinition\` zawiera:
- \`pattern_id\`, \`label\`;
- \`cells\` — wymagane komórki opisane offsetami względem kotwicy;
- \`relations\` — opcjonalne relacje symboli;
- \`match_mode\` — \`exact\` lub \`contains\`;
- \`status\` — \`draft\`, \`confirmed\` albo \`retired\`;
- \`priority\` — priorytet porządkujący wyniki.

Każdy wzorzec musi zawierać komórkę kotwicy o offsecie \`(0, 0, 0)\`. Pozostałe offsety mogą być ujemne lub dodatnie w zakresie -6..6.

### Tryby dopasowania zawartości komórki
- **exact** — identyczna sekwencja symboli, z zachowaniem kolejności.
- **contains** — wszystkie wymagane symbole muszą występować w komórce; kolejność jest nieważna, ale liczba powtórzeń ma znaczenie.

Wzorce są przesuwane po wszystkich możliwych kotwicach kostki. Dopasowanie wychodzące poza granice siatki nie jest uwzględniane.

## 5. Relacje
- \`same_cell\` — symbole muszą znajdować się w tej samej komórce.
- \`adjacent\` — symbole muszą być w różnych komórkach sąsiadujących według wybranego connectivity.
Relacje są sprawdzane wyłącznie w komórkach należących do danego dopasowania wzorca, a nie w dowolnym miejscu całej kostki.

## 6. Wyniki
Każdy \`SpatialPatternMatch\` zwraca identyfikator i etykietę wzorca, kotwicę, komórki które spełniły regułę, relacje oraz priorytet. Wyniki są uporządkowane według priorytetu malejąco, identyfikatora wzorca i współrzędnych kotwicy.

Tylko wzorce o statusie \`confirmed\` są rozpoznawane.

## 7. Serializacja
\`SpatialGrid.to_json()\` eksportuje rozmiar siatki i listę komórek. \`SpatialGrid.from_json(...)\` waliduje format, rozmiar, współrzędne, niepuste sekwencje symboli i duplikaty komórek.

## 8. Przykład
\`\`\`python
from sss import (
    SpatialCellRequirement,
    SpatialGrid,
    SpatialPatternDefinition,
    SpatialPatternRecognizer,
    SpatialRelation,
)

grid = SpatialGrid({
    (3, 3, 3): ("E1", "E2"),
    (4, 3, 3): ("E3",),
})

pattern = SpatialPatternDefinition(
    pattern_id="CENTER_TO_RIGHT",
    label="Autorski układ przestrzenny",
    cells=(
        SpatialCellRequirement((0, 0, 0), ("E1", "E2")),
        SpatialCellRequirement((1, 0, 0), ("E3",)),
    ),
    relations=(SpatialRelation("E2", "E3", "adjacent", 6),),
    status="confirmed",
)

matches = SpatialPatternRecognizer([pattern]).recognize(grid)
\`\`\`

## 9. Granice interpretacji
Dopasowanie oznacza wyłącznie spełnienie jawnej reguły rozmieszczenia symboli. System nie rozpoznaje automatycznie prawdziwych emocji osób, nie diagnozuje i nie wyprowadza znaczenia psychologicznego z samego położenia. Reguły przestrzenne muszą zostać zdefiniowane przez autora.

## 10. Zakres i ograniczenia
Wersja 2.0.0 implementuje lokalną siatkę, reguły komórek, trzy definicje sąsiedztwa i deterministyczne rozpoznawanie wzorców. Nie implementuje jeszcze wizualnego edytora kostki, synchronizacji sieciowej, automatycznego generowania semantyki ani trwałego magazynu danych.
