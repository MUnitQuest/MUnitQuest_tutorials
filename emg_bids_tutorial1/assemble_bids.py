"""
Assemble BIDS-EMG dataset from source data.

Adapted from the script in walkthrough.md, with the following changes:
  - get_channel_names filters out REF rows (channel_name == "n/a")
  - Run and session numbers are zero-padded (run-01, ses-01)
  - metadata_zip is optional: pass None to skip sidecar extraction
  - Spike-train events are written to derivatives/<pipeline_name>/

Usage (from repo root):
    python tutorial/assemble_bids.py

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
                "onset":      round(float(sample) / fs, 6),
                "duration":   0.0,
                "trial_type": mu_label,
            })

    df = pd.DataFrame(rows, columns=["onset", "duration", "trial_type"])
    df = df.sort_values("onset").reset_index(drop=True)
    df.to_csv(out_path, sep="\t", index=False)


def assemble_bids_dataset(recordings_csv, channels_csv, data_dir,
                           output_dir, fs, metadata_zip=None,
                           pipeline_name="motor-unit-decomposition"):
    """
    Build a BIDS dataset folder.

    recordings_csv -- path to recordings.csv
    channels_csv   -- path to channels_electrodes.csv
    data_dir       -- root folder; path_to_emg_file values are relative to this
                      (.npy: shape n_channels x n_samples)
    output_dir     -- destination folder (created if needed)
    fs             -- sampling frequency in Hz
    metadata_zip   -- optional path to metadata.zip; if given, extracted first
    pipeline_name  -- name of the derivatives sub-folder for spike-train events
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

        # --- Events TSV (derivatives) ---
        labels_rel = row.get("path_to_labels_file", "").strip()
        if labels_rel:
            src_labels = Path(data_dir) / labels_rel
            if not src_labels.exists():
                print(f"  SKIP events (not found): {src_labels}")
                continue

            deriv_subdir = output_dir / "derivatives" / pipeline_name / sub / ses_folder
            events_path  = deriv_subdir / "emg" / (bids_stem + "_desc-decomposition_events.tsv")

            npz = np.load(src_labels)
            spike_trains = {k: npz[k] for k in npz.files}
            write_events_tsv(events_path, spike_trains, fs)

            total = sum(len(v) for v in spike_trains.values())
            print(f"  wrote {events_path.relative_to(output_dir)}  "
                  f"({len(spike_trains)} MUs, {total} spikes)")
            has_derivatives = True

    # derivatives/dataset_description.json (required by the BIDS validator)
    if has_derivatives:
        deriv_root = output_dir / "derivatives" / pipeline_name
        deriv_root.mkdir(parents=True, exist_ok=True)
        desc = {
            "Name":        pipeline_name,
            "BIDSVersion": "1.11.1",
            "DatasetType": "derivative",
            "GeneratedBy": [{"Name": pipeline_name}],
        }
        (deriv_root / "dataset_description.json").write_text(
            json.dumps(desc, indent=2)
        )
        print(f"  wrote derivatives/{pipeline_name}/dataset_description.json")

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
