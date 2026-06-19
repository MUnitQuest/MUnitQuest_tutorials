"""Shared utilities for MUnitQuest algorithm-challenge notebooks."""

import json
import os
from typing import Any
from pathlib import Path
from dataclasses import dataclass, asdict
from collections import Counter, defaultdict

import numpy as np
import pandas as pd

_REQUIRED_LOG_KEYS = {"GeneratedBy", "Execution", "Environment"}
_REQUIRED_GENERATED_BY_KEYS = {"Name", "CodeURL"}


@dataclass
class ValidationItem:
    """ 
    Data class to configure errors and warnings 

    Args
    ----
    code : str
        code of the warning, error
    
    severity : str
        error or warning
    
    location : str
        file the error/warning occured in
    
    origin : str
        to adhere to validator from data challenge.
        Only resolves to MUnitQuest Custom Validator
    
    issueMessage : str
        detailed description of the error/warning

    """
    code: str
    location: str
    issueMessage: str
    severity: str = "error"
    origin: str = "MUnitQuest Custom Validator"

    def itemize(self):
        return asdict(self)


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

    _errors: list[dict] = []
    _warnings: list[dict] = []

    if not submission_dir.is_dir():
        _errors.append(
            ValidationItem(
                code="SUBMISSION_DIRECTORY_NOT_FOUND",
                location=submission_dir,
                issueMessage=f"Submission directory not found: {submission_dir}"
            ).itemize()
        )
        # TODO
        _print_report(_errors, _warnings)
        return False, _errors, _warnings

    _names = {f.name for f in submission_dir.iterdir() if f.is_file()}

    def _read_tsv(name):
        return pd.read_table(submission_dir / name)

    source_edfs = sorted(data_dir.rglob("*_emg.edf"))
    if not source_edfs:
        _warnings.append(
            ValidationItem(
                code="NO_RECORDINGS_FOUND",
                location=data_dir,
                issueMessage=f"No *_emg.edf files found in data_dir ({data_dir}); skipping coverage check.",
                severity="warning"
            ).itemize()
        )
        return True, _errors, _warnings

    # if len(_names) < len(source_edfs):
    #     _warnings.append(
    #         f"Submission contains {len(_names)} file(s); expected "
    #         f"{len(source_edfs)*2}. Some recordings may have been skipped."
    #     )

    n_valid = 0
    for edf in source_edfs:
        stem = edf.stem.replace("_emg", "_desc-decomposition")
        expected_tsv  = stem + "_events.tsv"
        expected_log  = stem + "_log.json"

        # Check events tsv files
        if expected_tsv not in _names:
            _warnings.append(
                ValidationItem(
                    code="MISSING_PREDICTION",
                    location=edf.name,
                    issueMessage=f"No submission TSV for recording: {edf.name}; ensure accurate filename conventions.",
                    severity="warning"
                ).itemize()
            )
            continue

        # try:
        #     df = _read_tsv(expected_tsv)
        # except Exception as exc:
        #     _errors.append(f"{expected_tsv}: could not read file — {exc}")
        #     continue
        tsv_ok, tsv_errors, tsv_warnings = _validate_prediction_file(os.path.join(submission_dir, expected_tsv))
        # for err in tsv_errors:
        #     _errors.append(f"{expected_tsv}: {err}")

        # Check metadata log files
        # if expected_log not in _names:
        #     _errors.append(f"Missing metadata log for recording: {edf.name} (expected {expected_log})")
        #     log_ok = False
        # else:
            # try:
            #     log_data = json.loads((submission_dir / expected_log).read_text())
            # except Exception as exc:
            #     _errors.append(f"{expected_log}: could not parse JSON — {exc}")
            #     log_ok = False
        #     else:
        log_ok, log_errors, log_warnings = _validate_prediction_log(os.path.join(submission_dir, expected_log))
        # for err in log_errors:
        #     _errors.append(f"{expected_log}: {err}")

        _errors += tsv_errors + log_errors
        _warnings += tsv_warnings + log_warnings

        if tsv_ok and log_ok:
            n_valid += 1

    _print_report(_errors, _warnings, n_valid=n_valid, n_total=len(source_edfs))
    return len(_errors) == 0, _errors, _warnings


def _print_report(errors, submission_warnings, n_valid=None, n_total=None):
    valid: bool = len(errors) == 0
    print(f"Validation Results: {'VALID' if valid else 'INVALID'}")
    print(f"{n_valid}/{n_total} TSVs passed")

    def _aggregate_by_key(items: list[dict], key: str) -> tuple[Counter, defaultdict]:
        """
        Aggregate level details on validation results

        Args:
            items (list[dict]): warning or errors
            key (str): by which key to aggregate

        Returns:
            tuple[Counter, defaultdict]: category counts and grouped items by category
        """
        counter: Counter = Counter()
        grouped: defaultdict = defaultdict(list)

        for item in items:
            res: str = item[key]
            counter[res] += 1
            grouped[res].append(item)

        return counter, grouped

    err_counter, _ = _aggregate_by_key(errors, key="code")
    
    print(f"\nErrors: {len(errors)}\n")
    if len(errors) > 0:
        for err_code, err_count in err_counter.items():
            print(f"- {err_code}: {err_count}")
        print("\n" + json.dumps(errors, indent=4))

    warn_counter, _ = _aggregate_by_key(submission_warnings, key="code")

    print(f"\nWarnings: {len(submission_warnings)}\n")
    if len(submission_warnings) > 0:
        for warn_code, warn_count in warn_counter.items():
            print(f"- {warn_code}: {warn_count}")
        print("\n" + json.dumps(submission_warnings, indent=4))
    
    # Legacy
    # for w in submission_warnings:
    #     print(f"[WARNING] {w}")
    # for e in errors:
    #     print(f"[ERROR]   {e}")
    # if n_valid is not None:
    #     status = "VALID" if not errors else "INVALID"
    #     print(
    #         f"\nSubmission {status}: {n_valid}/{n_total} TSVs passed, "
    #         f"{len(errors)} error(s), {len(submission_warnings)} warning(s)."
    #     )


# DEPRECATED
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


# DEPRECATED
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


def _validate_prediction_file(
    file: str,
) -> tuple[bool, list[dict], list[dict]]:
    """
    Validate a BIDS-like motor unit events table.

    Required columns:
    - onset       : float >= 0
    - duration    : must be 0
    - sample      : integer
    - unit_id     : integer
    - description : must include "motor-unit-spike"

    Args
    ----
        file : str
            Path to the file   

    Returns
    -------
        is_valid : bool
            True if file is valid.

        errors : list of str
            List of validation error messages.
    """

    # Init list of errors
    errors: list[dict] = []
    warnings: list[dict] = []  # template for raising warnings

    # Define required column names
    required_columns = {
        "onset",
        "duration",
        "sample",
        "unit_id",
        "description",
    }

    # Load the file
    try:
        df = pd.read_table(file)
    except Exception as e:
        errors.append(
            ValidationItem(
                code="UNREADABLE_EVENTS_TSV_FORMAT",
                location=file,
                issueMessage=f"Error when reading {file}. Please validate file format. Error message: {e}"
            ).itemize()
        )
        return False, errors, warnings

    # Check if required columns are present
    missing = required_columns - set(df.columns)

    if missing:
        errors.append(
            ValidationItem(
                    code="MISSING_EVENT_COLUMN",
                    location=file,
                    issueMessage=f"Missing required columns: {sorted(missing)}"
            ).itemize()
        )

        # Cannot continue safely
        return False, errors, warnings


    # Check if the file includes motor unit spike events
    mu_df = df[df["description"] == "motor-unit-spike"]

    if len(mu_df) == 0:
        errors.append(
            ValidationItem(
                code="MISSING_MU_SPIKE_EVENTS",
                location=file,
                issueMessage="motor-unit-spike missing in event description column"
            ).itemize()
        )
        return False, errors, warnings

    # Check if all onset values are numeric values and larger than zero
    if not pd.api.types.is_numeric_dtype(mu_df["onset"]):
        errors.append(
            ValidationItem(
                code="ONSET_MUST_BE_NUMERIC",
                location=file,
                issueMessage="Onset must be numeric"
            ).itemize()
        )
    else:
        invalid = mu_df["onset"] < 0

        if invalid.any():
            bad_idx = mu_df.index[invalid].tolist()
            errors.append(
                ValidationItem(
                    code="ONSET_NOT_LARGER_ZERO",
                    location=file,
                    issueMessage=f"Onset must be >= 0, invalid rows: {bad_idx}"
                ).itemize()
            )

    # Check if the duration of all motor unit spikes is zero
    invalid = mu_df["duration"] != 0

    if invalid.any():
        bad_idx = mu_df.index[invalid].tolist()
        errors.append(
            ValidationItem(
                code="DURATION_NOT_ZERO",
                location=file,
                issueMessage=f"Duration for MU spikes must always be 0, invalid rows: {bad_idx}"
            ).itemize()
        )

    # Check if the sample columns contains only integers
    if not pd.api.types.is_integer_dtype(mu_df["sample"]):
        errors.append(
            ValidationItem(
                code="SAMPLE_MUST_BE_INTEGER",
                location=file,
                issueMessage="Sample must be of type Integer"
            ).itemize()
        )
    else:
        invalid: pd.Series[bool] = mu_df["sample"] < 0
        if invalid.any():
            bad_idx = mu_df.index[invalid].tolist()
            errors.append(
                ValidationItem(
                    code="SAMPLE_NOT_LARGER_ZERO",
                    location=file,
                    issueMessage=f"Sample must be >= 0, invalid_rows: {bad_idx}"
                ).itemize()
            )

    # Check if the unit_id is always an integer
    if not pd.api.types.is_integer_dtype(mu_df["unit_id"]):
        errors.append(
            ValidationItem(
                code="ID_MUST_BE_INTEGER",
                location=file,
                issueMessage="Unit ID must be of type Integer"
            ).itemize()
        )
    else:
        invalid: pd.Series[bool] = mu_df["unit_id"] < 0
        if invalid.any():
            bad_idx = mu_df.index[invalid].tolist()
            errors.append(
                ValidationItem(
                    code="UNIT_ID_NOT_LARGER_ZERO",
                    location=file,
                    issueMessage=f"unit_id must be >= 0, invalid_rows: {bad_idx}"
                ).itemize()
            )

    # Final validation
    is_valid = len(errors) == 0

    return is_valid, errors, warnings


def _validate_prediction_log(
        logfile: str,
        schema: dict={
            "GeneratedBy": {
                "Name": {
                    "required": True,
                    "type": str
                },
                "Description": {
                    "required": True,
                    "type": str
                },
                "CodeURL": {
                    "required": True,
                    "type": str
                },
                "License": {
                    "required": True,
                    "type": str
                },
                "Version": {
                    "required": False,
                    "type": str | None
                },
                # "Container": {
                #     "required": False,
                #     "type": str | None
                # }
            },
            "Environment": dict,
            "Execution": dict
        }
    ) -> tuple[bool, list[dict], list[dict]]:
    """
    Checks existence and required contents of the logfile
    accompanying each prediction. That logfile is searched for by
    naming conventions.

    Args:
        prediction (str): path to prediction,
        schema (dict): schema for the validator to follow
    
    Returns:
        tuple[bool, list[dict], list[dict]]: valid indicator, errors and warnings
    """    
    errors: list[dict] = []
    warnings: list[dict] = []

    if not os.path.exists(logfile):
        prediction_path: str = logfile.replace("log.json", "events.tsv")
        errors.append(
            ValidationItem(
                code="MISSING_LOGFILE_FOR_PREDICTION",
                location=prediction_path,
                issueMessage=f"Logfile missing for prediction: {prediction_path}. Please provide a logfile {logfile}"
            ).itemize()
        )

        return False, errors, warnings
    
    with open(logfile, "r", encoding="utf-8") as f:
        try:
            prediction_log: dict = json.load(f)
        except Exception as e:
            errors.append(
                ValidationItem(
                    code="LOGFILE_NOT_READABLE",
                    location=logfile,
                    issueMessage=f"could not read {logfile}: {e}"
                ).itemize()
            )
            return False, errors, warnings

        # top-level keys
        missing = schema.keys() - prediction_log.keys()
        if len(missing) > 0:
            errors.append(
                ValidationItem(
                    code="MISSING_LOG_REQUIREMENT",
                    location=logfile,
                    issueMessage=f"Missing required keys for logfile {logfile}: {missing}"
                ).itemize()
            )

        for key, data in prediction_log.items():
            # different cases for data being a list or another dict
            if key == "GeneratedBy":
                if not isinstance(data, list):
                    errors.append(
                        ValidationItem(
                            code="INVALID_LOG_SCHEMA",
                            location=logfile,
                            issueMessage=f"Content for {key} must be list"
                        ).itemize()
                    )
                elif not len(data) > 0:
                    errors.append(
                        ValidationItem(
                            code="EMPTY_LOG_REQUIREMENT",
                            location=logfile,
                            issueMessage=f"No entries for {key}"
                        ).itemize()
                    )
                else:
                    for i in range(len(data)):
                        generated_by: dict = data[i]
                        for k, v in schema[key].items():
                            if not k in generated_by.keys():
                                if schema[key][k]["required"]:
                                    errors.append(
                                        ValidationItem(
                                            code="MISSING_LOG_REQUIREMENT",
                                            location=logfile,
                                            issueMessage=f"Please provide {k} in logfile for {key} at index {i}"
                                        ).itemize()
                                    )
                                else:
                                    warnings.append(
                                        ValidationItem(
                                            code="MISSING_LOG_REQUIREMENT",
                                            location=logfile,
                                            issueMessage=f"It is recommended to provide {k} in logfile for {key} at index {i}",
                                            severity="warning"
                                        ).itemize()
                                    )
                            elif not isinstance(generated_by[k], v["type"]):
                                errors.append(
                                    ValidationItem(
                                        code="INVALID_DATATYPE_LOGFILE",
                                        location=logfile,
                                        issueMessage=f"Data type of {k} is expected to be {v["type"]} for {key} at index {i}"
                                    ).itemize()
                                )
                            elif generated_by[k] in ["", "n/a", None]:
                                # code url is allowed to be empty
                                required: bool = schema[key][k]["required"]
                                if required:
                                    errors.append(
                                        ValidationItem(
                                            code="EMPTY_LOG_REQUIREMENT",
                                            location=logfile,
                                            issueMessage=f"Value for {k} required, but empty or not provided, for {key} at index {i}",
                                        ).itemize()
                                    )
                                else:
                                    warnings.append(
                                        ValidationItem(
                                            code="EMPTY_LOG_REQUIREMENT",
                                            location=logfile,
                                            issueMessage=f"Value for {k} is empty or not provided, for {key} at index {i}",
                                            severity="warning"
                                        ).itemize()
                                    )                    
            
            elif key == "Execution":
                if not isinstance(data, schema[key]):
                    errors.append(
                        ValidationItem(
                            code="INVALID_DATATYPE_LOGFILE",
                            location=logfile,
                            issueMessage=f"Data type of {key} is expected to be {schema[key]["type"]}"
                        ).itemize()
                    )
                elif not "Runtime" in data.keys():
                    errors.append(
                        ValidationItem(
                            code="MISSING_LOG_REQUIREMENT",
                            location=logfile,
                            issueMessage=f"Runtime: float needs to be specified in {key}"
                        )
                    )
                else:
                    runtime: Any = data["Runtime"]
                    if not isinstance(runtime, float):
                        errors.append(
                            ValidationItem(
                                code="INVALID_DATATYPE_LOGFILE",
                                location=logfile,
                                issueMessage=f"Data type of Runtime is expected to be float"
                            ).itemize()
                        )
                    elif not runtime > 0.:
                        errors.append(
                            ValidationItem(
                                code="INVALID_RUNTIME_ENTRY",
                                location=logfile,
                                issueMessage=f"Runtime must be > 0."
                            ).itemize()
                        )

    valid: bool = len(errors) == 0

    return valid, errors, warnings
