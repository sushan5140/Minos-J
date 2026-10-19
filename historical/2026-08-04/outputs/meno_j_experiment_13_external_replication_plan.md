# Meno-J Experiment 13 — Independent Wearable-Dataset Replication Plan

Status: **dataset selected; acquisition pending**

## Selected dataset

The selected external cohort is PhysioNet's [Wearable Device Dataset from Induced Stress and Structured Exercise Sessions, version 1.0.1](https://physionet.org/content/wearable-device-dataset/1.0.1/), DOI `10.13026/he0v-tf17`.

The official release reports 36 stress-session volunteers and Empatica E4 blood-volume pulse, electrodermal activity, skin temperature, and three-axis acceleration. It is open under the Open Data Commons Attribution License v1.0. The complete archive is reported as 69.7 MB compressed and 247.4 MB uncompressed.

This dataset is the strongest practical external test because it was collected independently of WESAD, uses a different wearable placement and stress protocol, contains more subjects, and shares EDA, temperature, and acceleration modalities with the current Meno-J feature representation.

## Planned falsification

The primary study will use stress sessions and compare a subject-disjoint raw representation with per-subject median/IQR normalization. It will use only shared EDA, temperature, and acceleration summary features. Protocol baseline/rest and cognitive/social stress blocks will remain distinct from self-reported stress scores in the data model.

Coverage, worst-subject coverage, classifier accuracy, prediction-set size, and full-label-set frequency will be reported together. Failure to reproduce the normalization benefit will weaken its claimed generality; success would move the representation gate beyond WESAD.

## Frozen acquisition sequence

1. Validate the ZIP structure, CRCs, safe paths, archive size, and expected files.
2. Extract without overwriting an existing validated copy.
3. Build a subject, signal, tag, and stage inventory without computing outcomes.
4. Freeze exact exclusions, interval mapping, minimum window counts, subject folds, and decision thresholds.
5. Only then run the external replication.

Known primary complete-case exclusions are S02 because of duplicated stress signals, f07 because its temperature and PPG sensors were covered, and f14 because its stress recording is split across files. The split f14 session may enter only a separately validated sensitivity analysis.

## Current blocker

Direct outbound download is blocked in the execution environment. The in-app browser reached 27,181,002 bytes before the transfer stalled; that incomplete file has not been moved, extracted, or accepted. No dataset-dependent result has been produced.

Official archive: [download version 1.0.1 ZIP](https://physionet.org/content/wearable-device-dataset/get-zip/1.0.1/)

Once the completed ZIP is in the Downloads folder, the prepared integrity gate can validate, copy, and extract it without rerunning Experiments 9–12.

## Verified sources

- [PhysioNet dataset description and access terms](https://physionet.org/content/wearable-device-dataset/1.0.1/)
- [Official sensor data dictionary](https://physionet.org/content/wearable-device-dataset/1.0.1/Data_Dictionary.csv)
- [Official data constraints](https://physionet.org/content/wearable-device-dataset/1.0.1/data_constraints.txt)
- [V1 self-reported stress stages](https://physionet.org/content/wearable-device-dataset/1.0.1/Stress_Level_v1.csv)
- [V2 self-reported stress stages](https://physionet.org/content/wearable-device-dataset/1.0.1/Stress_Level_v2.csv)
