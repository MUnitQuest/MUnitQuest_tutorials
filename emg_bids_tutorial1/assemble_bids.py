"""
Assemble a BIDS-EMG dataset from source data.

For each row in recordings.csv this script:
  1. Writes the HD-sEMG signals as an EDF file (sub-XX/.../emg/*_emg.edf)
  2. Copies behavioural event annotations as a TSV sidecar (*_events.tsv)
  3. Writes spike-train events to derivatives/motor-unit-decomposition/

It also writes a root-level events.json describing the custom event columns,
a derivatives/dataset_description.json required by the BIDS validator, and a
.bidsignore file to suppress validator warnings for the derivatives folder.

If metadata_zip is provided (recommended), it is extracted into output_dir
first, supplying dataset_description.json, participants files, channels TSVs,
coordsystem JSONs, and per-recording emg.json sidecars.

Usage:
    python assemble_bids.py

Requires: numpy, pandas, pyedflib
"""

import json
import numpy as np
import pandas as pd
import pyedflib
import zipfile
from pathlib import Path


def get_channel_names(channels_csv, setup):
    """Return ordered channel names for a given setup.

    Excludes REF electrodes (those with channel_name == "n/a").
    """
    ch = pd.read_csv(channels_csv, keep_default_na=False, na_values=[""])
    mask = (ch["setup"] == setup) & ch["channel_name"].notna() & (ch["channel_name"].str.strip() != "n/a")
    return ch.loc[mask, "channel_name"].str.strip().tolist()


def write_edf(out_path, data, channel_names, fs):
    """Write data array to EDF.

    data: np.ndarray, shape (n_channels, n_samples), float32/64, physical units
    """
    out_path = Path(out_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)

    headers = []
    for ch in channel_names:
        headers.append({
            "label":            ch,
            "sample_frequency": fs,
        })

    with pyedflib.EdfWriter(str(out_path), len(channel_names)) as f:
        f.setSignalHeaders(headers)
        f.writeSamples(data)


def write_events_tsv(out_path: Path, spike_trains: dict, fs: float) -> None:
    """Write BIDS events.tsv from a dict of {mu_label: sample_index_array}."""
    out_path.parent.mkdir(parents=True, exist_ok=True)

    rows = []
    for mu_label in sorted(spike_trains.keys()):
        for sample in spike_trains[mu_label]:
            rows.append({
                "onset": round(float(sample) / fs, 4),
                "duration": 0.0,
                "sample": sample,
                "unit_id": int(mu_label[-2:]),
                "description": "motor-unit-spike"
            })

    df = pd.DataFrame(rows, columns=["onset", "duration", "sample", "unit_id", "description"])
    df = df.sort_values("onset").reset_index(drop=True)
    df.to_csv(out_path, sep="\t", index=False)


PIPELINE_NAME = "motor-unit-decomposition"


def assemble_bids_dataset(recordings_csv, channels_csv, data_dir,
                           output_dir, fs, metadata_zip=None):
    """
    Build a BIDS dataset folder.

    recordings_csv -- path to recordings.csv
    channels_csv   -- path to channels_electrodes.csv
    data_dir       -- root folder; path_to_emg_file values are relative to this
                      (.npy: shape n_channels x n_samples)
    output_dir     -- destination folder (created if needed)
    fs             -- sampling frequency in Hz
    metadata_zip   -- optional path to metadata.zip; if given, extracted first
    """
    output_dir = Path(output_dir)

    if metadata_zip is not None:
        with zipfile.ZipFile(metadata_zip) as zf:
            zf.extractall(output_dir)

    recs = pd.read_csv(recordings_csv, dtype=str).fillna("")
    has_derivatives = False

    for _, row in recs.iterrows():
        sub   = f"sub-{int(row['sub']):02d}"
        ses   = row.get("ses", "").strip()
        task  = row["task_name"].strip()
        run   = row.get("run", "").strip()
        setup = row["setup"].strip()

        parts = [sub]
        if ses:  parts.append(f"ses-{int(ses):02d}")
        parts.append(f"task-{task}")
        if run:  parts.append(f"run-{int(run):02d}")
        bids_stem = "_".join(parts)

        ses_folder = f"ses-{int(ses):02d}" if ses else ""
        subdir     = output_dir / sub / ses_folder

        # --- EDF ---
        out_path = subdir / "emg" / (bids_stem + "_emg.edf")
        src      = Path(data_dir) / row["path_to_emg_file"].strip()
        data     = np.load(src)["data"] if src.suffix == ".npz" else np.load(src)
        data     = data.astype(np.float32)

        channel_names = get_channel_names(channels_csv, setup)
        if data.shape[0] != len(channel_names):
            raise ValueError(
                f"{bids_stem}: data has {data.shape[0]} channels but "
                f"{len(channel_names)} names from channels_electrodes.csv "
                f"(setup={setup})"
            )

        write_edf(out_path, data, channel_names, fs)
        print(f"  wrote {out_path.relative_to(output_dir)}")

        # --- Behavioural events TSV ---
        events_rel = row.get("path_to_events_file", "").strip()
        if events_rel:
            src_events = Path(data_dir) / events_rel
            if not src_events.exists():
                print(f"  SKIP behavioural events (not found): {src_events}")
            else:
                evts = pd.read_csv(src_events)
                events_out = subdir / "emg" / (bids_stem + "_events.tsv")
                events_out.parent.mkdir(parents=True, exist_ok=True)
                evts.to_csv(events_out, sep="\t", index=False)
                print(f"  wrote {events_out.relative_to(output_dir)}")

        # --- Spike-train events TSV (derivatives) ---
        labels_rel = row.get("path_to_labels_file", "").strip()
        if labels_rel:
            deriv_subdir = output_dir / "derivatives" / PIPELINE_NAME / sub / ses_folder
            events_path  = deriv_subdir / "emg" / (bids_stem + "_desc-decomposition_events.tsv")

            src_labels = Path(data_dir) / labels_rel
            if src_labels.exists():
                npz = np.load(src_labels)
                spike_trains = {k: npz[k] for k in npz.files}
            else:
                print(f"  WARNING: spike-train file not found, writing empty events: {src_labels}")
                spike_trains = {}

            write_events_tsv(events_path, spike_trains, fs)

            total = sum(len(v) for v in spike_trains.values())
            print(f"  wrote {events_path.relative_to(output_dir)}  "
                  f"({len(spike_trains)} MUs, {total} spikes)")
            has_derivatives = True

    # events.json — column descriptions for all _events.tsv files
    events_json = {
        "sample": {
            "Description": "Sample index of the event onset at the recording sampling frequency"
        },
        "mvc_level": {
            "Description": "Target force level as a percentage of maximum voluntary contraction",
            "Units": "%MVC"
        },
        "event_type": {
            "Description": "Category of the event",
            "Levels": {
                "rest":         "Resting EMG recording with no voluntary contraction",
                "muscle_on":    "Start of voluntary contraction",
                "linear_ramp":  "Linear ramp in target force level",
                "steady_hold":  "Steady isometric contraction at constant target force",
                "muscle_off":   "End of voluntary contraction",
            }
        },
        "description": {
            "Description": "Free-text description of the event"
        },
    }
    (output_dir / "events.json").write_text(json.dumps(events_json, indent=2))
    print(f"  wrote events.json")

    # derivatives/dataset_description.json (required by the BIDS validator)
    if has_derivatives:
        deriv_root = output_dir / "derivatives" / PIPELINE_NAME
        deriv_root.mkdir(parents=True, exist_ok=True)
        desc = {
            "Name":        PIPELINE_NAME,
            "BIDSVersion": "1.11.1",
            "DatasetType": "derivative",
            "GeneratedBy": [{
                "Name":    PIPELINE_NAME,
                "CodeURL": "https://github.com/MUnitQuest/MUnitQuest_tutorials/tree/main/emg_bids_tutorial1",
            }],
        }
        (deriv_root / "dataset_description.json").write_text(
            json.dumps(desc, indent=2)
        )
        print(f"  wrote derivatives/{PIPELINE_NAME}/dataset_description.json")

    bidsignore = output_dir / ".bidsignore"
    if not bidsignore.exists():
        bidsignore.write_text("derivatives/\n")
        print(f"  wrote .bidsignore")

    print(f"\nDone. BIDS dataset at: {output_dir}")


if __name__ == "__main__":
    SOURCE = Path(__file__).parent / "source_data"
    OUTPUT = Path(__file__).parent / "MUnitQuest_BIDS_Tutorial"

    assemble_bids_dataset(
        recordings_csv = SOURCE / "recordings.csv",
        channels_csv   = SOURCE / "channels_electrodes.csv",
        data_dir       = SOURCE,
        output_dir     = OUTPUT,
        fs             = 2048,
        metadata_zip   = SOURCE / "metadata.zip",
    )
