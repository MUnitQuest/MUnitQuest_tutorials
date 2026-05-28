# EMG-BIDS Tutorial

This folder contains the scripts and source data for the [MUnitQuest EMG-BIDS walkthrough](https://munitquest.github.io/walkthrough/).

The walkthrough explains the full process of preparing a real HD-EMG dataset for sharing using the [EMG-BIDS](https://bids-specification.readthedocs.io/en/stable/modality-specific-files/electromyography.html) standard. This folder has the runnable code and CSV source files that accompany it.

## Contents

```
emg_bids_tutorial1/
├── generate_source_data.py   # generates synthetic EMG recordings and event files
├── assemble_bids.py          # converts source_data/ into a BIDS dataset
├── source_data/
│   ├── participants.csv
│   ├── recordings.csv
│   ├── setup.csv
│   ├── coordsystems.csv
│   ├── channels_electrodes.csv
│   ├── form_inputs.json       # dataset-level fields for the metadata tool
│   └── metadata.zip           # BIDS sidecar files from the MUnitQuest metadata tool
└── MUnitQuest_BIDS_Tutorial/  # pre-built BIDS output (regenerate with assemble_bids.py)
```

The large binary EMG recordings (`.npy`, `.npz`) are not stored in the repo — run `generate_source_data.py` to create them locally before running `assemble_bids.py`.

## Setup

```bash
pip install numpy pandas pyedflib
```

## Running the tutorial

**Step 1 — generate synthetic source data** (`.npy` EMG arrays, `.npz` spike trains, and `.csv` event annotations written into `source_data/`):

```bash
python generate_source_data.py
```

**Step 2 — assemble the BIDS dataset** (reads `source_data/`, overwrites `MUnitQuest_BIDS_Tutorial/`):

```bash
python assemble_bids.py
```

The output is a complete BIDS-compliant dataset with EDF recordings, behavioural event sidecars, a root-level `events.json`, and motor-unit decomposition derivatives.

## CSV files

The five CSV files in `source_data/` are the inputs described in the walkthrough. You can open and edit them to try out your own dataset structure before running `assemble_bids.py`. The `metadata.zip` was generated from `form_inputs.json` and those CSVs using the [MUnitQuest metadata tool](https://munitquest.github.io/metadata-form/).
