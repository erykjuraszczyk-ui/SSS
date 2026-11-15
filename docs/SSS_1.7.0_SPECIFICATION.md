# SSS 1.7.0 — Emotion Cipher Engine

## 1. Cel
Silnik koduje i odczytuje szyfry emocji zdefiniowane przez autora. Obsługuje pojedyncze symbole oraz kompozycje wielu symboli.

## 2. Model symbolu
Każdy symbol ma stabilny identyfikator, glif (opcjonalny), autorską etykietę emocjonalną, wektor parametrów, status i pochodzenie definicji.

Wektor v = (V, A, D, I): V — walencja [-1,1], A — pobudzenie [0,1], D — dominacja/poczucie kontroli [0,1], I — intensywność [0,1]. Wartości są opcjonalne. To parametry opisowe wybrane przez autora, nie uniwersalna prawda o emocji.

## 3. Reguły kompozycji
- BASE(x): znaczenie pojedynczego symbolu.
- BLEND(x,y,...): kompozycja; zachowuje składniki i nie redukuje ich automatycznie do jednej etykiety.
- INTENSIFY(x,k): skaluje I przez k, ograniczając wynik do 1.
- ATTENUATE(x,k): skaluje I przez k z zakresu [0,1].
- CONTRAST(x,y): zapisuje kontrast jako relację, bez zakładania przeciwieństwa bez jawnej reguły.
- TRANSITION(x,y,t): zapisuje przejście od x do y w czasie t.
- CONTEXT(x,c): dołącza kontekst jako metadane, nie zmieniając po cichu znaczenia x.

## 4. Zasady interpretacji
1. Nieznany symbol powoduje błąd, nie zgadywanie.
2. Status draft nie jest zatwierdzoną semantyką.
3. Kompozycja zachowuje kolejność i pochodzenie składników.
4. Sąsiedztwo przestrzenne może dostarczyć kontekstu, ale samo nie nadaje znaczenia.
5. Brak parametru oznacza unknown, a nie zero.

## 5. Geometria
Współrzędne lokalne komórki: x,y,z ∈ {0,...,6}. Komórka może zawierać wiele symboli. Wersja 1.7.0 przechowuje pozycję i kolejność, lecz nie narzuca globalnej kolejności odczytu wielu ścian.

## 6. Bezpieczeństwo semantyczne
SSS jest systemem reprezentacji autorskiego kodu, nie narzędziem diagnozowania stanu psychicznego. Nie wnioskuje o emocjach konkretnej osoby bez jawnego, świadomego opisu źródłowego.

## 7. Status
Reguły i parametry są propozycją bazową SSS 1.7.0. Glify i ich konkretne znaczenia pozostają do uzupełnienia przez autora.
