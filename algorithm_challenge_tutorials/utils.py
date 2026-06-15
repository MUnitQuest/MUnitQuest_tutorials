"""Shared utilities for MUnitQuest algorithm-challenge notebooks."""

import json
from pathlib import Path

import numpy as np
import pandas as pd

_REQUIRED_LOG_KEYS = {"GeneratedBy", "Runtime", "Environment"}
_REQUIRED_GENERATED_BY_KEYS = {"Name", "CodeURL"}


def export_events_file(spike_times, unit_ids, edf_path, fsamp, output_dir=None):
    """Write spike trains to a BIDS-style *_desc-decomposition_events.tsv.

    Parameters
    ----------
    spike_times : array-like of int
        Spike sample indices.
    unit_ids : array-like of int
        Motor unit label for each spike. Must be the same length as
        ``spike_times``.
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
    spike_times = np.asarray(spike_times)
    unit_ids    = np.asarray(unit_ids)
    assert len(spike_times) == len(unit_ids), (
        f"spike_times and unit_ids must have the same length "
        f"(got {len(spike_times)} and {len(unit_ids)})"
    )

    df = pd.DataFrame({
        "onset":       np.round(spike_times / fsamp, 6),
        "duration":    0,
        "sample":      spike_times.astype(int),
        "unit_id":     unit_ids.astype(int),
        "description": "motor-unit-spike",
    })
    df = df.sort_values("onset").reset_index(drop=True)

    edf_path = Path(edf_path)
    stem = edf_path.stem.replace("_emg", "_desc-decomposition")
    out_dir = Path(output_dir) if output_dir else edf_path.parent
    out_path = out_dir / f"{stem}_events.tsv"
    df.to_csv(out_path, sep="\t", index=False, na_rep="n/a")
    return out_path


def export_metadata(metadata_log, edf_path, output_dir=None):
    """Write a metadata log dict to a *_desc-metadata_log.json file.

    Parameters
    ----------
    metadata_log : dict
        Metadata to serialise (GeneratedBy, Runtime, Environment, …).
    edf_path : str or Path
        Path to the source EDF file (used to derive the output filename).
    output_dir : str or Path, optional
        Directory to write the JSON. Defaults to the same directory as edf_path.

    Returns
    -------
    Path
        Absolute path of the written JSON file.
    """
    edf_path = Path(edf_path)
    stem = edf_path.stem.replace("_emg", "_desc-decomposition_log")
    out_dir = Path(output_dir) if output_dir else edf_path.parent
    out_path = out_dir / f"{stem}.json"
    out_path.write_text(json.dumps(metadata_log, indent=2))
    return out_path


def validate_submission(submission_dir, data_dir):
    """Validate a submission directory before leaderboard upload.

    Checks:
    - Every source recording in ``data_dir`` has a matching decomposition TSV
      (missing files emit warnings, not errors — algorithms may skip recordings
      where no reliable units were found).
    - A warning is emitted when the total number of submitted TSVs is fewer
      than the number of recordings in ``data_dir``.
    - Each present TSV passes column-level validation via
      :func:`_validate_decomp_events`.

    Parameters
    ----------
    submission_dir : str or Path
        Directory containing the submission files.
    data_dir : str or Path
        Directory containing the source ``*_emg.edf`` files (BIDS-flat
        layout). Used to derive the expected set of decomposition TSVs.

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

    if not submission_dir.is_dir():
        _errors.append(f"Submission directory not found: {submission_dir}")
        _print_report(_errors, _warnings)
        return False, _errors, _warnings

    _names = {f.name for f in submission_dir.iterdir() if f.is_file()}

    def _read_tsv(name):
        return pd.read_table(submission_dir / name)

    source_edfs = sorted(data_dir.glob("*_emg.edf"))
    if not source_edfs:
        _warnings.append(f"No *_emg.edf files found in data_dir ({data_dir}); skipping coverage check.")

    if len(_names) < len(source_edfs):
        _warnings.append(
            f"Submission contains {len(_names)} file(s); expected "
            f"{len(source_edfs)*2}. Some recordings may have been skipped."
        )

    n_valid = 0
    for edf in source_edfs:
        stem = edf.stem.replace("_emg", "_desc-decomposition")
        expected_tsv  = stem + "_events.tsv"
        expected_log  = stem + "_log.json"

        # Check events tsv files
        if expected_tsv not in _names:
            _warnings.append(f"No submission TSV for recording: {edf.name}")
            continue

        try:
            df = _read_tsv(expected_tsv)
        except Exception as exc:
            _errors.append(f"{expected_tsv}: could not read file — {exc}")
            continue
        tsv_ok, tsv_errors = _validate_decomp_events_df(df, expected_tsv)
        for err in tsv_errors:
            _errors.append(f"{expected_tsv}: {err}")

        # Check metadata log files
        if expected_log not in _names:
            _errors.append(f"Missing metadata log for recording: {edf.name} (expected {expected_log})")
            log_ok = False
        else:
            try:
                log_data = json.loads((submission_dir / expected_log).read_text())
            except Exception as exc:
                _errors.append(f"{expected_log}: could not parse JSON — {exc}")
                log_ok = False
            else:
                log_ok, log_errors = _validate_decomp_log(log_data)
                for err in log_errors:
                    _errors.append(f"{expected_log}: {err}")

        if tsv_ok and log_ok:
            n_valid += 1

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


def _validate_decomp_log(log_data):
    """Validate a decomposition metadata log dict.

    Returns
    -------
    is_valid : bool
    errors : list of str
    """
    errors = []

    if not isinstance(log_data, dict):
        errors.append("File must contain a JSON object at the top level")
        return False, errors

    missing = _REQUIRED_LOG_KEYS - set(log_data.keys())
    if missing:
        errors.append(f"Missing required keys: {sorted(missing)}")
        return False, errors

    runtime = log_data["Runtime"]
    if not isinstance(runtime, (int, float)):
        errors.append(f"'Runtime' must be a numeric value (got {type(runtime).__name__})")

    generated_by = log_data["GeneratedBy"]
    if not isinstance(generated_by, dict):
        errors.append("'GeneratedBy' must be a JSON object")
    else:
        missing_gb = _REQUIRED_GENERATED_BY_KEYS - set(generated_by.keys())
        if missing_gb:
            errors.append(f"'GeneratedBy' is missing required keys: {sorted(missing_gb)}")

    return len(errors) == 0, errors
