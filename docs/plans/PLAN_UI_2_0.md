# RAE-CRL UI 2.0: From Notebook to Cockpit
Cel: Przekształcenie technicznego MVP w narzędzie, które "sprzedaje" możliwości systemu.

## Filozofia
Interfejs ma być **przezroczysty**, ale musi dawać poczucie **kontroli** nad procesem badawczym (Projekty, Czas, Relacje).

## 1. Context & Identity (Fundament)
Obecnie: Hardcoded `default-lab` / `me`.
Zmiana:
- **Sidebar**:
    - Dropdown: "Aktywny Projekt" (Tworzenie/Przełączanie).
    - User Profile: Proste pole "Twoje imię" (persystowane w local storage/cookie).
- **Efekt**: Dane wreszcie mają sensowną strukturę własności.

## 2. The Timeline (Epizodyczność)
Obecnie: Płaska lista kart.
Zmiana:
- **Grupowanie dzienne**: "Dzisiaj", "Wczoraj", "W zeszłym tygodniu".
- **Wizualizacja Grace Period**: Pasek postępu odliczający czas do upublicznienia (24h).
- **Statusy**: Kolorowe badge (Draft 🔒, Team 👥, Public 🌍).

## 3. Visualizing Relationships (Graf)
Obecnie: Brak. Relacje są tylko w bazie.
Zmiana:
- **Widok "Graph"**: Wykorzystanie `ui.mermaid` lub `vis.js` w NiceGUI.
- **Interakcja**: Kliknij węzeł -> Zobacz szczegóły.
- **Forking UI**: Przycisk "Fork" na węźle, który wizualnie tworzy nową gałąź.

## 4. Sync & Health (Poczucie bezpieczeństwa)
Obecnie: Przycisk "Sync Now".
Zmiana:
- **Status Indicator**: "🟢 Synced", "🟡 Pending (Grace)", "🔴 Offline".
- **Logs Console**: Podgląd co system wysyła do RAE (dla zaufania).

## Plan Wdrożenia
1. Refaktoryzacja `ui/main.py` na moduły (`components/sidebar.py`, `components/timeline.py`).
2. Implementacja Zarządzania Stanem (Project/User) w `nicegui.app.storage`.
3. Dodanie widoku Grafu.
