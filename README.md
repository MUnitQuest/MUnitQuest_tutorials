# MUnitQuest Tutorials

Tutorials and reference material for the [MUnitQuest](https://munitquest.github.io) competition. The competition has two tracks: a **Data Challenge** (share an HD-EMG dataset in BIDS format) and an **Algorithm Challenge** (submit a motor-unit decomposition algorithm). Tutorials are organised by topic below.

---

## 1. Codabench Platform

[`codabench_tutorials/`](codabench_tutorials/codabench_tutorial.md)

How to sign up, create a team, navigate competitions, submit results, and read leaderboards on the [Codabench](https://www.codabench.org) platform. Competition links:

- [Data Challenge](https://www.codabench.org/competitions/15762/)
- [Algorithm Challenge](https://www.codabench.org/competitions/15749/)

---

## 2. EMG-BIDS Tutorials

The Data Challenge requires datasets formatted to the [EMG-BIDS](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electromyography.html) standard. These tutorials show two ways to get there.

### Tutorial 1 — CSV-based workflow

[`emg_bids_tutorial1/`](emg_bids_tutorial1/)

Uses five simple CSV files to describe participants, recordings, hardware, electrode layouts, and coordinate systems. The MUnitQuest metadata tool generates BIDS sidecar files from those CSVs automatically. Includes a synthetic 10-recording example dataset (2 subjects, 3 setups) with runnable Python scripts.

Read the full walkthrough at [munitquest.github.io/walkthrough](https://munitquest.github.io/walkthrough/).

### Tutorial 2 — Python/MUniverse

Step-by-step Jupyter notebook converting a fictional HD-EMG dataset to EMG-BIDS using the Python-based [`MUniverse`](https://github.com/dfarinagroup/muniverse/tree/main) package.

[`emg_bids_tutorial2/`](emg_bids_tutorial2/) · [`emg_bids_tutorial2.ipynb `](emg_bids_tutorial2/emg_bids_tutorial2.ipynb)


---

## 3. Algorithm Challenge Tutorials

[`algorithm_challenge_tutorials/`](algorithm_challenge_tutorials/)

How to load the competition datasets, decompose HD-EMG recordings with CBSS, and export spike trains for leaderboard submission.

| Notebook | Task | Open in Colab |
|---|---|---|
| [02 – Familiarisation: Isometric](algorithm_challenge_tutorials/02_familiarisation_isometric.ipynb) | Isometric task | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pranavm19/MUnitQuest_tutorials/blob/main/algorithm_challenge_tutorials/02_familiarisation_isometric.ipynb) |
| [03 – Familiarisation: Dynamic](algorithm_challenge_tutorials/03_familiarisation_dynamic.ipynb) | Dynamic task | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/pranavm19/MUnitQuest_tutorials/blob/main/algorithm_challenge_tutorials/03_familiarisation_dynamic.ipynb) |
