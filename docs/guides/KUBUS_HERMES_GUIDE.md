# Przewodnik dla Kubusia: Jak korzystać z RAE-Suite i RAE-CRL w pracy doktorskiej (z agentem Hermes)

Witaj Kubuś! Ten dokument to praktyczny przewodnik, jak wykorzystać **Node 1 (Lumina)**, silnik pamięci **RAE-Suite** oraz moduł naukowy **RAE-CRL (Cognitive Research Loop)** w Twoich badaniach doktoranckich i przy codziennej pracy programistycznej z agentem **Hermes**.

---

## 1. Co to jest i po co Ci to w doktoracie?

Badania naukowe i doktorat to długi proces, w którym po 6–12 miesiącach łatwo zapomnieć:
- *Dlaczego zmieniliśmy ten hiperparametr lub założenie algorytmu?*
- *Jakie próby zakończyły się fiaskiem i czego nas nauczyły (aby nie powtarzać tych samych błędów)?*
- *Które decyzje architektoniczne były oparte na twardych danych, a które na intuicji?*

Tradycyjne repozytoria kodu (Git) pamiętają **co** się zmieniło w kodzie, ale nie pamiętają **procesu myślowego i przyczyn**. 

**RAE-CRL (Cognitive Research Loop)** to Twoje cyfrowe rusztowanie epistemologiczne (Electronic Lab Notebook nowej generacji), które współpracuje z silnikiem pamięci **RAE-Suite**:
1. **6 typów artefaktów badawczych**:
   - `Hypothesis` (Hipoteza): np. *„Zwiększenie głębokości sieci do 12 warstw poprawi dokładność na rzadkich danych o 5%”*.
   - `Assumption` (Założenie): np. *„Czujnik/dane wejściowe są znormalizowane do rozkładu N(0,1)”*.
   - `Experiment` (Eksperyment): procedura badawcza, skrypt, parametry uruchomieniowe.
   - `Observation` (Obserwacja): surowy wynik, logi, metryki (np. MSE = 0.042).
   - `Decision` (Decyzja): wybór drogi (np. *„Odrzucamy wariant A, wdrażamy wariant B”*).
   - `Reflection` (Refleksja): metakognitywny wniosek (np. *„Gradient zanikał przez brak LayerNorm”*).
2. **Epistemic Forks (Rozgałęzienia hipotez)**: Możliwość rozwidlenia interpretacji wyników, gdy pojawiają się dwie sprzeczne teorie.
3. **Porażka jako zysk naukowy (`record_failure`)**: Eksperyment, który się nie powiódł, nie ląduje w koszu — zostaje oznaczony jako `FAILED_BUT_INFORMATIVE` i zasila pamięć długoterminową agenta.
4. **Grace Period (24h karencji)**: Szybkie notatki (`quick_note`) są w 100% prywatne i nie wychodzą do wspólnej pamięci, dopóki ich nie dopracujesz lub nie minie okres ochronny.

---

## 2. Architektura środowiska na Twoim komputerze (Node 1)

Wszystkie usługi działają lokalnie na Twojej maszynie (Node 1 Lumina, Arch Linux, procesor i7-14700KF, 64 GB RAM, karta graficzna NVIDIA GeForce RTX 4080 z 16 GB VRAM):

| Usługa | Adres / Port | Rola w badaniach |
| :--- | :--- | :--- |
| **RAE-CRL Web Desk** | `http://localhost:8503` (lub `http://100.68.166.117:8503`) | Interaktywny pulpit badawczy (NiceGUI): przeglądanie grafu hipotez, dodawanie notatek, eksport raportów |
| **RAE Memory API** | `http://localhost:8000` | Silnik pamięci semantycznej, epizodycznej i refleksyjnej (wektory + Qdrant) |
| **SonarQube Community** | `http://localhost:9000` | Ciągła analiza jakości i bezpieczeństwa Twojego kodu (Bugs: 0, Vulnerabilities: 0, Coverage >90%) |
| **Ollama (Lokalne LLM)** | `http://localhost:11434` | Lokalne modele LLM napędzane RTX 4080 (`hermes3:8b`, `qwen2.5-coder:14b`, `deepseek-r1:8b`) |
| **Qdrant Vector DB** | `http://localhost:6333` | Wektorowa baza danych do szybkiego wyszukiwania semantycznego wspomnień i kodu |

Usługi są zarządzane przez `systemd --user` — wstają automatycznie przy starcie systemu.

---

## 3. Integracja z agentem Hermes (przez protokół MCP)

Hermes (lub dowolny inny agent AI, np. Claude Desktop, Cursor, VS Code Continue) może bezpośrednio kontrolować RAE-CRL oraz pamięć RAE za pomocą standardowego protokołu **Model Context Protocol (FastMCP)**.

### A. Konfiguracja MCP dla Hermesa / Claude / Cursora

W pliku konfiguracyjnym MCP Twojego agenta (np. `~/.config/hermes/mcp.json` lub w ustawieniach Cursora/Claude Desktop):

```json
{
  "mcpServers": {
    "rae-crl": {
      "command": "/home/operator/RAE-CRL/.venv/bin/python",
      "args": [
        "/home/operator/RAE-CRL/apps/crl/mcp_server.py"
      ],
      "env": {
        "RAE_CORE_URL": "http://localhost:8000",
        "DATABASE_URL": "sqlite+aiosqlite:////home/operator/RAE-CRL/rae_crl.db"
      }
    }
  }
}
```

### B. Jakie narzędzia Hermes otrzymuje do dyspozycji?

Gdy Hermes ma włączony serwer `rae-crl`, zyskuje zestaw dedykowanych funkcji badawczych:

1. `quick_note(content, project, author)`:
   - Szybkie zapisanie luźnej myśli, wątpliwości lub obserwacji z laboratorium.
   - Domyślnie prywatne, objęte 24-godzinnym okresem ochronnym.
2. `refine_artifact(artifact_id, new_type, title, description)`:
   - Podniesienie luźnej notatki do rangi formalnej: `hypothesis`, `experiment`, `observation`, `decision`, `reflection`, `assumption`.
3. `record_failure(experiment_id, reason)`:
   - Zapisanie nieudanego eksperymentu z dokładnym wyjaśnieniem przyczyny (bardzo ważne w doktoracie!).
4. `fork_artifact(original_id, new_author, reason)`:
   - Stworzenie alternatywnej interpretacji badawczej i połączenie jej relacją `has_alternative_interpretation`.
5. `list_my_traces(project)`:
   - Wyświetlenie listy szkiców oczekujących na dopracowanie w danym projekcie.
6. `request_approval(artifact_id, approver_name)` & `approve_artifact(artifact_id, approver_name)`:
   - Formalny obieg recenzji i zatwierdzania (np. akceptacja promotora / PI przed publikacją).

---

## 4. Scenariusze z życia: Jak Hermes pomaga Ci w pracy

### Scenariusz 1: Pisanie i automatyczne testowanie programów naukowych

Gdy tworzysz moduły obliczeniowe, algorytmy analizy danych czy symulacji:

**Przykładowy prompt do Hermesa:**
> *„Hermes, napisałem nowy moduł `simulation/fem_solver.py`. Wykorzystaj RAE-Suite, aby przygotować do niego pełny zestaw testów w pytest (jednostkowe, brzegowe, testy wydajnościowe). Upewnij się, że pokrycie kodu wyniesie powyżej 90%, a kod spełnia standardy czystego kodu. Następnie sprawdź, czy testy przechodzą i zarejestruj wynik w RAE-CRL jako eksperyment.”*

Hermes:
1. Analizuje kod i generuje testy parametryzowane w `tests/test_fem_solver.py`.
2. Uruchamia `pytest --cov=simulation` na Twoim Node 1.
3. Może uruchomić skaner SonarQube (`sonar-scanner`), aby sprawdzić wskaźniki: Bugs: 0, Vulnerabilities: 0, Code Smells: 0.
4. Zapisuje formalny artefakt eksperymentu z numerem commita i metrykami pokrycia.

---

### Scenariusz 2: Rejestrowanie eksperymentów i nieudanych prób

W trakcie uczenia modeli uczenia maszynowego lub symulacji numerycznych:

**Przykładowy prompt do Hermesa:**
> *„Hermes, próba treningu modelu z batch_size=128 i learning_rate=0.01 wywołała wybuch gradientu (NaN po 40 epokach). Zapisz to jako porażkę eksperymentu 'Run-ML-042' w RAE-CRL z wnioskiem: konieczne zastosowanie gradient clippingu oraz zmniejszenie LR do 0.001. Następnie stwórz nową hipotezę na kolejny przebieg.”*

Hermes wywołuje w tle:
- `record_failure(experiment_id="...", reason="Exploding gradient, loss=NaN at epoch 40")`
- `refine_artifact` lub dodaje nową hipotezę do projektu `doktorat-kubus`.

---

### Scenariusz 3: Odzyskiwanie wiedzy po 6 miesiącach

Przed pisaniem rozdziału dysertacji lub publikacji konferencyjnej:

**Przykładowy prompt do Hermesa:**
> *„Hermes, przeszukaj pamięć RAE-CRL dla projektu 'doktorat-kubus': dlaczego w listopadzie zrezygnowaliśmy z filtru Kalmana na rzecz filtru cząsteczkowego? Jakie były ówczesne wyniki pomiarów szumu?”*

Hermes:
1. Odpytuje semantyczną bazę pamięci RAE i bazę CRL.
2. Zwraca dokładny cytat z Twojej ówczesnej decyzji, powiązane obserwacje liczbowe oraz wykres zależności.

---

## 5. Korzystanie z Pulpitu Badawczego (Lab Desk Web UI)

Jeśli wolisz interfejs graficzny:

1. Otwórz w przeglądarce: **`http://localhost:8503`** (na Node 1) lub **`http://100.68.166.117:8503`** (z dowolnego urządzenia w sieci Tailscale).
2. Zobaczysz:
   - **Pulpit artefaktów**: filtrowanie po typie (`Hypothesis`, `Experiment`, `Observation` itd.).
   - **Graf zależności**: wizualna sieć powiązań między Twoimi pomysłami a eksperymentami.
   - **Szybki notatnik (Quick Trace)**: do wpisywania myśli w trakcie pracy laboratoryjnej.
   - **Panel dostępności (WCGA)**: tryb wysokiego kontrastu i czytelne fonty monospace (`JetBrains Mono`).

---

## 6. Szybkie polecenia CLI w terminalu

Z poziomu dowolnego terminala na Node 1 możesz korzystać z narzędzia `rae-crl`:

```bash
# 1. Sprawdzenie pomocy
rae-crl --help

# 2. Inicjalizacja kontekstu Twojego doktoratu
rae-crl init "doktorat-kubus"

# 3. Zapisanie nowej hipotezy
rae-crl add hypothesis "Nowa funkcja aktywacji zredukuje czas zbieżności o 20%" "Testy na benchmarku CIFAR-100" "doktorat-kubus"

# 4. Zapisanie eksperymentu
rae-crl add experiment "Uruchomienie skryptu train.py z seed=42 i nową aktywacją" "Epoki: 100, optymalizator AdamW" "doktorat-kubus"

# 5. Odpytanie historii badawczej (wyszukiwanie semantyczne)
rae-crl query "funkcja aktywacji zbieżność" "doktorat-kubus"
```

---

## 7. Jak zarządzać usługami na Node 1

Wszystkie procesy działają w tle pod Twoim kontem użytkownika (`operator`):

```bash
# Status Web Desku RAE-CRL:
systemctl --user status rae-crl.service

# Restart RAE-CRL:
systemctl --user restart rae-crl.service

# Podgląd logów na żywo:
journalctl --user -u rae-crl.service -f

# Sprawdzenie pamięci RAE-Suite:
systemctl --user status rae-api.service

# Sprawdzenie serwera SonarQube:
systemctl --user status sonarqube.service
```

---

## Podsumowanie

Dzięki połączeniu **Hermesa + RAE-CRL + RAE-Suite**:
- Hermes staje się Twoim **asystentem naukowym**, który nie tylko pisze kod i testy, ale pilnuje rygoru metodologicznego.
- Twój doktorat zyskuje pełną **audytowalność i powtarzalność** (zgodną z wymogami publikacji w czasopismach z listy filadelfijskiej).
- Żadna udana ani nieudana próba badawcza nie zginie w historii konsoli.
