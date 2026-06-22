# 1. General Instructions
Competition-agnostic first steps on the codabench competition platform.
[codabench](https://www.codabench.org/) is an open-source platform allowing organizers to configure ML benchmarks.
```
@article{codabench,
    title = {Codabench: Flexible, easy-to-use, and reproducible meta-benchmark platform},
    author = {Zhen Xu and Sergio Escalera and Adrien Pavão and Magali Richard and
                Wei-Wei Tu and Quanming Yao and Huan Zhao and Isabelle Guyon},
    journal = {Patterns},
    volume = {3},
    number = {7},
    pages = {100543},
    year = {2022},
    issn = {2666-3899},
    doi = {https://doi.org/10.1016/j.patter.2022.100543},
    url = {https://www.sciencedirect.com/science/article/pii/S2666389922001465}
}
```
**The official documentation can be found here:** https://docs.codabench.org/latest/
## 1.1 Sign-Up
Sign-up to the competition platform by creating an account: https://www.codabench.org/accounts/signup
<img width="326" height="305" alt="Pasted image 20260420090832" src="https://github.com/user-attachments/assets/4ad448fc-32ba-4f28-9e5f-659ae36e17e2" />

## 1.2 Creating Teams/Organizations
You can create organizations enabling participation in competitions as a team.
Click `Create Organization`<br/>
<img width="218" height="419" alt="Pasted image 20260420091115" src="https://github.com/user-attachments/assets/efe01121-2148-45f4-8526-dd1fc4115521" />

Within the form `Create an Organization` provide the information necessary and press `submit`
<img width="544" height="441" alt="Pasted image 20260420091316" src="https://github.com/user-attachments/assets/bf4d4d70-2eca-4ffb-be71-699e84a62d14" />

Upon submission, you can curate the organization members, by editing your organization
<img width="600" height="310" alt="Pasted image 20260420092348" src="https://github.com/user-attachments/assets/c3334627-3ffc-425d-aa06-cc8611049b22" />

<img width="600" height="500" alt="Pasted image 20260420092540" src="https://github.com/user-attachments/assets/a8d01b19-d969-496d-b423-5b562aa69c11" />

>[!Note]
>Each member requires an individual codabench account
## 1.3 Participate
You can find the **MUnitQuest**-competition implementations here:
- [Data Challenge](https://www.codabench.org/competitions/15762/)
- [Algorithm Challenge](https://www.codabench.org/competitions/15749/)

Register for the competition (tbd.)
Once registered, you can navigate the benchmark.
>[!Tip]
>codabench provides an individualized competition-dashboard for quick future access
><br/><img width="959" height="167" alt="Pasted image 20260420094519" src="https://github.com/user-attachments/assets/0cd8b652-a446-4237-86ea-358b62d9e767" />

## 1.4 Navigate a Competition
First familiarize yourselves with the competition details by viewing the `Get Started`-Pane
<img width="590" height="411" alt="Pasted image 20260420094102" src="https://github.com/user-attachments/assets/7be6855c-2efd-4f7d-a0c6-bd3806dc2901" />

## 1.4.1 Competition Resources
A competition usually contains public and private resources. Example resources may be
- the scoring functions used to score submissions
- a starter kit, providing detailed instructions and exemplary submissions
- training- and validation data
- ...

Publicly available assets are downloadable via the `files`-page in the `Get Started`-Pane
<img width="590" height="411" alt="Pasted image 20260420095223" src="https://github.com/user-attachments/assets/f4ba9fcd-385e-422b-9519-777a35c2784f" />

## 1.4.2 Phases
A competition may be structured in multiple sequential phases. You can find individual phase-details via the `Phases`-Pane
<img width="590" height="411" alt="Pasted image 20260420095554" src="https://github.com/user-attachments/assets/657bfa79-86fa-4827-95b1-ba6ecea26743" />

## 1.4.3 Submissions
In the `My Submissions`-Pane you can submit a new submission and/or view past submissions. Additionally, you can choose the submissions to be considered in the leaderboard and whether you want to submit as an organization.
<img width="670" height="605" alt="Pasted image 20260420095912" src="https://github.com/user-attachments/assets/0f55a68c-a6e4-4c65-9002-9e1f01fe765a" />

If a competition consists of multiple phase choose the according phase. Additionally, a phase may consist of multiple tasks to be chosen from during submission, depending on the task the submission contributes to.
>[!Note]
>You can find more details on the submission within 2.X and 3.X respectively.
## 1.4.4 Leaderboards
For each potential phase, there exists a leaderboard pivoted by the tasks per phase. The leaderboards can be viewed in the `Results`-Pane
<img width="590" height="411" alt="Pasted image 20260420100609" src="https://github.com/user-attachments/assets/eac9db4c-3c67-41aa-9ee6-6077395b3f65" />

>[!Warning]
>Leaderboards within the **MunitQuest**-Challenges are at any point provisionary.
>The official, result-relevant leaderboards will be published after the respective phases/challenges have finished
## 1.5 General
**Coming soon**
# 2. Data Challenge
Specific information for the Data Challenge
<br/>
## 2.1 Submission Format
codabench requires submission to be a zip-Archive. The zip-Archive should have the following structure for the automated validator to run.
```
root/
└── BIDSDataset  -> name of the dataset
    ├── dataset_description.json
    ├── participants.tsv
    ├── participants.json
    ├── README
    ├── sub-01/
    │   ├── emg/
    │   │   ├── sub-01_task-xxx_emg.edf
    │   │   ├── sub-01_task-xxx_channels.tsv
    │   │   ├── sub-01_task-xxx_events.tsv
    │   │   ├── sub-01_task-xxx_electrodes.tsv
    │   │   └── sub-01_task-xxx_coordsystem.json
    │   └── ...
    └── sub-02/
        └── ...
```

>[!Warning]
>To save storage, please do not upload the actual EMG-recordings, but only the metadata.
>After successful metadata validation, we will provide a link to the cloud storage, where to
>upload the full dataset

## 2.2 How to Submit
1. In the codabech-competition navigate to `My Submissions` (see 1.4.3)
2. Choose whether to submit as yourself or as a registered team (see 1.2)
3. Upload the zip-Archive
4. Wait for preliminary, automated dataset validation results

>[!Tip]
>The integrated stdout/stderr terminal window may be incomplete. To see the full stdout/stderr of your submission, you can view to the logs displayed in detail, when clicking on your submission and navigating to the `LOGS`-Tab.
><img width="811" height="125" alt="image" src="https://github.com/user-attachments/assets/3ad7d494-768b-466a-ad3c-50d6eb3bff2c" />


5. Download submission artifacts (especially `detailed_results.html`) by navigating to your submission and downloading `Output from scoring step`
6. Investigate `detailed_results.html`, which contains an upload link, if and only if the metadata validation has been successful
7. Choose whether the submission should appear on the competition's leaderboard, by pressing the `table`-icon in the submissions overview

>[!Warning]
>We highly encourage you to upload different datasets and, thus, enable multiple leaderboard-effective submissions. If you, however, wish to update an already submitted dataset on the leaderboard, make sure to remove the old version from the leaderboard. Please notify the organizers when submitting multiple datasets!


<img width="1000" height="500" alt="image" src="https://github.com/user-attachments/assets/daa9d930-3caa-40e5-96c3-c67ba9d452c0" />

<img width="750" height="400" alt="image" src="https://github.com/user-attachments/assets/94a72293-3eb9-4509-9fdf-0ade9b6a33d8" />

<img width="750" height="400" alt="image" src="https://github.com/user-attachments/assets/be14c161-6216-43b8-a19c-be6c2d2b1b3c" />

<img width="1288" height="317" alt="image" src="https://github.com/user-attachments/assets/b4f91796-a24d-4753-b819-f5fcc20d847e" />

<img width="1747" height="326" alt="image" src="https://github.com/user-attachments/assets/7541798d-b91f-4ed8-a690-a45c1777286b" />


# 3. Algorithm Challenge
Specific information for the Algorithm Challenge
## 3.1 Submission Format
codabench requires submission to be a zip-Archive. The predictions are expected to be submitted as a flat list of [BIDS event files](https://bids-specification.readthedocs.io/en/stable/modality-agnostic-files/events.html) and their corresponding log-files located at the root of the zip-Archive.
```
exampleSubmission.zip
├── recording-001_challenge-<dynamic | isometric>_desc-decomposed_events.tsv
├── recording-001_challenge-<dynamic | isometric>_desc-decomposed_log.json
├── ...
├── recording-100_challenge-<dynamic | isometric>_desc-decomposed_events.tsv
└── recording-100_challenge-<dynamic | isometric>_desc-decomposed_log.json
```

>[!Tip]
>These Tutorials provide code examples and guidelines for submitting valid predictions. Additionally,  validator can indicate pre-submission validity.
>This validator works as follows:
>```python
>from utils import validate_submission
>
>is_valid, errors, warnings = validate_submission(
>    submission_dir=SUBMISSION_FOLDER,
>    data_dir=DATASET_ROOT,
>)
>```

### 3.1.1 BIDS Event File
The following is a minimal example of predcited spike-trains in BIDS notation

<table style="width: 100%; table-layout: fixed;">
  <thead>
    <tr>
      <th style="width: 20%;">onset</th>
      <th style="width: 20%;">duration</th>
      <th style="width: 20%;">sample</th>
      <th style="width: 20%;">unit_id</th>
      <th style="width: 20%;">description</th>
    </tr>
  </thead>

  <tbody>
    <tr>
      <td>0.001</td>
      <td>0</td>
      <td>1</td>
      <td>0</td>
      <td>motor-unit-spike</td>
    </tr>
    <tr>
      <td>0.005</td>
      <td>0</td>
      <td>5</td>
      <td>1</td>
      <td>motor-unit-spike</td>
    </tr>
    <tr>
      <td>0.011</td>
      <td>0</td>
      <td>11</td>
      <td>0</td>
      <td>motor-unit-spike</td>
    </tr>
    <tr>
      <td>0.012</td>
      <td>0</td>
      <td>12</td>
      <td>2</td>
      <td>motor-unit-spike</td>
    </tr>
    <tr>
      <td>0.016</td>
      <td>0</td>
      <td>16</td>
      <td>1</td>
      <td>motor-unit-spike</td>
    </tr>
    <tr>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>...</td>
      <td>motor-unit-spike</td>
    </tr>
  </tbody>
</table>

- *onset*: Onset (in seconds) of the event, measured from the beginning of the acquisition.
- *duration*: Duration of the event (measured from onset) in seconds. As a motor unit spike can be regarded as a Dirac impulse, its duration is zero.  
- *sample*: Sample index of the event onset (zero-indexing).
- *unit_id*: Unique identifier (integer value) of the motor unit corresponding to the detected spike.
- *description*: Human-readable free-text description of the event.

For more information and code-examples for prediction export follow our notebook-Tutorials: https://github.com/MUnitQuest/MUnitQuest_tutorials/tree/main/algorithm_challenge_tutorials

### 3.1.2 Prediction log
Each prediction is to be accompanied by a logfile providing some algorithm- and runtime meta information.<br/>
**Required Fields**:
| Field | Type | Required sub-keys | Description |
|---|---|---|---|
| `GeneratedBy` | `list[dict]` | `Name`, `Description`, `CodeURL`, `License`| Algorithm name, a short plain-English description, and a URL pointing to the code (GitHub, GitLab, or similar). `Version` is optional. **`CodeURL` is required even if your repository is private** — it is used to verify algorithm identity, not to access the code. |
| `Execution` | `dict` | `Runtime` | Total wall-clock execution time for the decomposition (seconds, as a number) |
| `RuntimeEnvironment`| `dict` | — | Hardware used: CPU model, total RAM, and GPU (if applicable) |

Please note that we validate towards the existence of the field `RuntimeEnvironment`, but do not enforce a specific structure of that field. Useful information might be the usage of GPUs, software packages, RAM, etc..

The following shows a minimal example of a valid prediction log:
```json
{
    "GeneratedBy": [
        {
            "Name": "MUniverse",
            "CodeURL": "https://github.com/dfarinagroup/muniverse",
            "License": "GPLv3",
            "Description": "Exemplary dynamic prediction"
        }
    ],
    "RuntimeEnvironment": {
        "CPU": "",
        "GPU": "if applicable",
        "RAM_GB": ""
    },
    "Execution": {
        "Runtime": 22.34597
    }
}
```

## 2.2 How to Submit
1. In the codabech-competition navigate to `My Submissions` (see 1.4.3)
2. Select the task you want to submit to. **Please note**, that it is possible to submit for both tasks at the same time. In doing so, the prediction-zip must contain the predictions for both tasks.
3. Choose whether to submit as yourself or as a registered team (see 1.2)
4. Upload the zip-Archive
5. Wait for the automation to finish.

>[!WARNING]
>The presented codabench Terminal seems very stale as there are issues in processing stdout and stderr. Please do not worry, something is happening 😉.<br/>
>A full dynamic submission should roughly take 10 - 30 min.<br/>
>A full is isometric submission can take up to $1 \frac{1}{2}$ h. <br/>
>Monitor the submission status.

6. Download submission artifacts (especially `detailed_results.html`) by navigating to your submission and downloading `Output from scoring step`
7. Investigate `detailed_results.html`, which contains useful aggregated information and detailed prediction-level information. Additionally, it contains the validation results of the submission.<br/>**Please Note** that invalid, but evaluable predictions will be evaluated anyways. Only in the case of validity, however, will you receive a leaderboard-effective global score.
8. Choose whether the submission should appear on the competition's leaderboard, by pressing the `table`-icon in the submissions overview
