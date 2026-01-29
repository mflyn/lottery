# Project Context: Lottery Analysis & Generation Tool

## 1. Project Overview
This project is a comprehensive Python-based tool for analyzing and generating numbers for Chinese Lotteries: **Double Color Ball (SSQ)** and **Super Lotto (DLT)**. It combines historical data analysis, statistical modeling, and a Tkinter-based GUI to assist users in selecting numbers.

## 2. Technical Architecture
-   **Language:** Python 3.8+
-   **GUI Framework:** Tkinter (standard library).
-   **Data Processing:** Pandas, NumPy.
-   **Visualization:** Matplotlib.
-   **Entry Point:** `run.py`

### Directory Structure
-   `src/core/`: Core business logic (Analysis, Generation, Evaluation, Data Management).
-   `src/gui/`: UI implementation (Main Window, Generation Tab, Analysis Tab, Evaluation Tab).
-   `data/`: Storage for historical lottery data (CSV/JSON).
-   `docs/`: Detailed feature documentation and implementation summaries.
-   `scripts/`: Utility scripts (e.g., `find_top_ssq.py`).
-   `tests/`: Unit and integration tests.

## 3. Key Features & Current Status

### A. Supported Lotteries
-   **SSQ (双色球):** Red (1-33, pick 6) + Blue (1-16, pick 1).
-   **DLT (大乐透):** Front (1-35, pick 5) + Back (1-12, pick 2).

### B. Generation Strategies (`src/core/generators`)
1.  **Random:** Purely random selection.
2.  **Smart/Frequency:** Based on hot/cold numbers.
3.  **Mixed:** Combination of strategies.
4.  **Top Scored (Highest Score):**
    -   *Recent Feature:* integrated into GUI.
    -   Uses a scoring algorithm weighing frequency, omission, and other factors.
    -   Configurable "Search Period" and "Pool Size" in GUI.
    -   Scores are displayed alongside generated numbers.

### C. Analysis & Evaluation
-   **Trends:** Visual charts for number frequency and omission.
-   **Number Evaluation:** Scores specific number combinations based on historical performance (30/100 periods).
-   **Anti-Popular:** Algorithms to avoid common patterns (e.g., birthdays, arithmetic sequences) to reduce prize dilution.

## 4. Development Standards

### Code Style
-   Follow PEP 8.
-   Use docstrings for complex functions.
-   Keep UI logic (`src/gui`) separate from Core logic (`src/core`) where possible.
-   **Threading:** Use `threading` for computationally intensive tasks (like "Top Scored" search) to prevent GUI freezing.

### Testing
-   **Framework:** `pytest`
-   **Key Test Files:**
    -   `test_top_scored_generation.py` (Manual/Integration test for top scored feature).
    -   `demo_top_scored_features.py` (Automated feature demo).
    -   `tests/` directory for unit tests.

## 5. User Preferences & Active Context
*Derived from memory and recent interactions.*
-   **Anti-Pattern:** User avoids combinations with >4 numbers overlapping with recent history.
-   **Evaluation Focus:** Prefers analyzing 30 and 100-period windows.
-   **Anti-Popular:** Strong interest in avoiding "human patterns" (birthdays, dates).
-   **DLT Support:** DLT analysis is a priority alongside SSQ.

## 6. Recent Implementation Context (Reference)
-   **Top Scored Strategy:** Recently completed. It links the "Evaluation" tab's weights to the "Generation" tab, preventing configuration duplication.
-   **GUI:** Added real-time status updates and parameter exposure for the search algorithm.
