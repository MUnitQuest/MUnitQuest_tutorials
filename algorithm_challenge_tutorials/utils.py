"""Shared utilities for MUnitQuest algorithm-challenge notebooks."""

import io
import json
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd


def spikes_to_events_tsv(spikes, edf_path, fsamp, output_dir=None):
    """Write a spike dict to a BIDS-style *_desc-decomposition_events.tsv.

    Parameters
    ----------
    spikes : dict
        {unit_id: array-like of spike sample indices} as returned by decompose_cbss.
    edf_path : str or Path
        Path to the source EDF file (used to derive the output filename).
    fsamp : int
        Sampling frequency in Hz.
    output_dir : str or Path, optional
        Directory to write the TSV. Defaults to the same directory as edf_path.

    Returns
    -------
    Path
        Absolute path of the written TSV file.
    """
    rows = []
    for uid, samples in sorted(spikes.items()):
        for sample in np.asarray(samples):
            rows.append({
                "onset":       round(int(sample) / fsamp, 6),
                "duration":    0,
                "sample":      int(sample),
                "unit_id":     uid,
                "description": "motor-unit-spike",
            })
    df = pd.DataFrame(rows)
    if not df.empty:
        df = df.sort_values("onset").reset_index(drop=True)

    edf_path = Path(edf_path)
    stem = edf_path.stem.replace("_emg", "_desc-decomposition")
    out_dir = Path(output_dir) if output_dir else edf_path.parent
    out_path = out_dir / f"{stem}_events.tsv"
    df.to_csv(out_path, sep="\t", index=False, na_rep="n/a")
    return out_path


def validate_submission(submission_dir, data_dir, expected_n_files=200):
    """Validate a submission directory (or zip) before leaderboard upload.

    Checks:
    - ``dataset_description.json`` is present and contains required metadata.
    - Every source recording in ``data_dir`` has a matching decomposition TSV
      (missing files emit warnings, not errors — algorithms may skip recordings
      where no reliable units were found).
    - A warning is emitted when the total number of submitted files is fewer
      than ``expected_n_files``.
    - Each present TSV passes column-level validation via
      :func:`_validate_decomp_events`.

    Parameters
    ----------
    submission_dir : str or Path
        Directory *or* ``.zip`` archive containing the submission files.
    data_dir : str or Path
        Directory containing the source ``*_emg.edf`` files (BIDS-flat
        layout). Used to derive the expected set of decomposition TSVs.
    expected_n_files : int
        Expected total number of files in the submission (default 200).
        A warning is printed if the actual count is lower.

    Returns
    -------
    is_valid : bool
        ``True`` if there are no errors (warnings do not count as failures).
    errors : list of str
        Validation errors that must be fixed before upload.
    submission_warnings : list of str
        Non-fatal issues (e.g. skipped recordings).
    """
    submission_dir = Path(submission_dir)
    data_dir = Path(data_dir)

    _errors = []
    _warnings = []

    # --- resolve zip vs directory -------------------------------------------
    if submission_dir.suffix == ".zip":
        if not submission_dir.exists():
            _errors.append(f"Zip archive not found: {submission_dir}")
            _print_report(_errors, _warnings)
            return False, _errors, _warnings
        _zip = zipfile.ZipFile(submission_dir)
        _names = {Path(n).name for n in _zip.namelist() if not n.endswith("/")}
        def _read_text(name):
            return _zip.read(name).decode()
        def _read_tsv(name):
            return pd.read_table(io.BytesIO(_zip.read(name)))
    else:
        if not submission_dir.is_dir():
            _errors.append(f"Submission directory not found: {submission_dir}")
            _print_report(_errors, _warnings)
            return False, _errors, _warnings
        _names = {f.name for f in submission_dir.iterdir() if f.is_file()}
        def _read_text(name):
            return (submission_dir / name).read_text()
        def _read_tsv(name):
            return pd.read_table(submission_dir / name)

    # --- total file count check ---------------------------------------------
    if len(_names) < expected_n_files:
        _warnings.append(
            f"Submission contains {len(_names)} file(s); expected "
            f"{expected_n_files}. Some recordings may have been skipped."
        )

    # --- dataset_description.json -------------------------------------------
    REQUIRED_META_KEYS = {"Name", "GeneratedBy", "runtime_seconds", "hardware"}
    if "dataset_description.json" not in _names:
        _errors.append("Missing required file: dataset_description.json")
    else:
        try:
            meta = json.loads(_read_text("dataset_description.json"))
            missing_keys = REQUIRED_META_KEYS - set(meta.keys())
            if missing_keys:
                _errors.append(
                    f"dataset_description.json missing required keys: {sorted(missing_keys)}"
                )
            if "GeneratedBy" in meta:
                gb = meta["GeneratedBy"]
                if not isinstance(gb, list) or len(gb) == 0:
                    _errors.append("'GeneratedBy' must be a non-empty list")
                elif "Name" not in gb[0]:
                    _errors.append("Each 'GeneratedBy' entry must have a 'Name' field")
            if "hardware" in meta and "cpu" not in meta["hardware"]:
                _errors.append("'hardware' dict must contain a 'cpu' field")
        except json.JSONDecodeError as exc:
            _errors.append(f"dataset_description.json is not valid JSON: {exc}")

    # --- per-recording TSV checks -------------------------------------------
    source_edfs = sorted(data_dir.glob("*_emg.edf"))
    if not source_edfs:
        _warnings.append(f"No *_emg.edf files found in data_dir ({data_dir}); skipping coverage check.")

    n_valid = 0
    for edf in source_edfs:
        expected_name = edf.stem.replace("_emg", "_desc-decomposition") + "_events.tsv"
        if expected_name not in _names:
            _warnings.append(f"No submission TSV for recording: {edf.name}")
            continue
        try:
            df = _read_tsv(expected_name)
        except Exception as exc:
            _errors.append(f"{expected_name}: could not read file — {exc}")
            continue
        # write to a temp path that _validate_decomp_events can open, or inline the logic
        is_valid, tsv_errors = _validate_decomp_events_df(df, expected_name)
        if is_valid:
            n_valid += 1
        else:
            for err in tsv_errors:
                _errors.append(f"{expected_name}: {err}")

    _print_report(_errors, _warnings, n_valid=n_valid, n_total=len(source_edfs))
    return len(_errors) == 0, _errors, _warnings


def _print_report(errors, submission_warnings, n_valid=None, n_total=None):
    for w in submission_warnings:
        print(f"[WARNING] {w}")
    for e in errors:
        print(f"[ERROR]   {e}")
    if n_valid is not None:
        status = "VALID" if not errors else "INVALID"
        print(
            f"\nSubmission {status}: {n_valid}/{n_total} TSVs passed, "
            f"{len(errors)} error(s), {len(submission_warnings)} warning(s)."
        )


def _validate_decomp_events(tsv_path):
    try:
        df = pd.read_table(tsv_path)
    except Exception:
        return False, [f"Failed loading file {tsv_path}."]
    return _validate_decomp_events_df(df, tsv_path)


def _validate_decomp_events_df(df, label="<dataframe>"):
    """Validate a motor unit events DataFrame (column-level checks).

    Returns
    -------
    is_valid : bool
    errors : list of str
    """
    errors = []

    required_columns = {"onset", "duration", "sample", "unit_id", "description"}

    # Check if required columns are present
    missing = required_columns - set(df.columns)

    if missing:
        errors.append(
            f"Missing required columns: {sorted(missing)}"
        )

        # Cannot continue safely
        return False, errors


    # Check if the file includes motor unit spike events
    mu_df = df[df["description"] == "motor-unit-spike"]

    if len(mu_df) == 0:
        errors.append(
            "No rows with description == 'motor-unit-spike'"
        )
        return False, errors

    # Check if all onset values are numeric values and larger than zero
    if not np.issubdtype(mu_df["onset"].dtype, np.number):
        errors.append("'onset' must be numeric")
    else:
        invalid = mu_df["onset"] < 0

        if invalid.any():
            bad_idx = mu_df.index[invalid].tolist()
            errors.append(
                f"'onset' must be >= 0 "
                f"(invalid rows: {bad_idx})"
            )

    # Check if the duration of all motor unit spikes is zero
    invalid = mu_df["duration"] != 0

    if invalid.any():
        bad_idx = mu_df.index[invalid].tolist()
        errors.append(
            f"'duration' must always be 0 "
            f"(invalid rows: {bad_idx})"
        )

    # Check if the sample columns contains only integers
    if not np.issubdtype(mu_df["sample"].dtype, np.integer):

        invalid = np.mod(mu_df["sample"], 1) != 0

        if invalid.any():
            bad_idx = mu_df.index[invalid].tolist()
            errors.append(
                f"'sample' must contain integers "
                f"(invalid rows: {bad_idx})"
            )

    # Check if the unit_id is always an integer
    if not np.issubdtype(mu_df["unit_id"].dtype, np.integer):

        invalid = np.mod(mu_df["unit_id"], 1) != 0

        if invalid.any():
            bad_idx = mu_df.index[invalid].tolist()
            errors.append(
                f"'unit_id' must contain integers "
                f"(invalid rows: {bad_idx})"
            )

    # Final validation
    is_valid = len(errors) == 0

    return is_valid, errors
