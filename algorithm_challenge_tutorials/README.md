# Algorithm Challenge Tutorials

Step-by-step Jupyter notebooks for the MUnitQuest **Algorithm Challenge**: load the familiarisation dataset, decompose HD-EMG recordings, and export spike trains for leaderboard submission.

| Notebook | Task type | Open in Colab |
|---|---|---|
| [01 – Familiarisation: Isometric](01_familiarisation_isometric.ipynb) | Isometric contractions | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MUnitQuest/MUnitQuest_tutorials/blob/main/algorithm_challenge_tutorials/01_familiarisation_isometric.ipynb) |
| [02 – Familiarisation: Dynamic](02_familiarisation_dynamic.ipynb) | Dynamic contractions | [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/MUnitQuest/MUnitQuest_tutorials/blob/main/algorithm_challenge_tutorials/02_familiarisation_dynamic.ipynb) |

---

## Installation

All notebooks require the [`muniverse`](https://github.com/dfarinagroup/muniverse) package. Install it once before running any notebook:

```bash
python -m venv .venv && source .venv/bin/activate   # recommended: use a virtual env
pip install --extra-index-url https://test.pypi.org/simple/ muniverse==0.0.1.dev2
```

On **Google Colab** the virtual environment step is not needed — just run this in a notebook cell:

```python
!pip install muniverse-emg
```

---

## Helper utilities

[`utils.py`](utils.py) contains shared helper functions used across notebooks:

- **`export_submission(spikes, edf_path, fsamp)`** — converts a spike dict to BIDS-style `*_desc-decomposition_events.tsv` required for leaderboard upload.
- **`validate_submission(tsv_path, fsamp)`** — validates a submission TSV for correct columns, onset/sample consistency, and sort order before upload.
