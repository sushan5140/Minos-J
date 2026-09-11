# Meno-J WESAD Acquisition Constraint Audit

Status: **BLOCKED PENDING COMPLETE DATASET**

## Verified official source

- UCI record: <https://archive.ics.uci.edu/dataset/465/wesad>
- University dataset page: <https://www.eti.uni-siegen.de/ubicomp/home/datasets/icmi18/index.html.en?lang=en>
- Official public archive endpoint: <https://uni-siegen.sciebo.de/public.php/dav/files/HGdUkoNlW1Ub0Gx/?accept=zip>
- Advertised archive size: 2.1 GB
- Permitted use stated by the source: scientific, non-commercial work with attribution.

## Exact local state

- Partial file: `C:\Users\DELL\Downloads\Unconfirmed 231915.crdownload`
- Partial size: 6,291,456 bytes (6 MiB)
- Complete `WESAD.zip`: absent
- Replacement resumable part: absent
- Extracted WESAD directory: absent
- Available space on drive C: 94,237,769,728 bytes (87.77 GB)
- The partial file has been preserved and has not been renamed, extracted, or treated as valid data.

## Blocking constraints

1. Storage is sufficient.
2. The shell cannot connect to the official host from the network sandbox.
3. The sandbox can read `Downloads` but cannot create or rename files there.
4. This session's approval policy rejects sandbox-elevation requests, so a narrow resumable `curl` transfer cannot be authorized from this task.
5. The available in-app browser exposes a session-bound download rather than a persistent resumable file handle.
6. The earlier browser wait ended when its automation execution timed out, leaving the stagnant 6 MiB partial.
7. Secondary public copies discovered during source checking were repackaged, substantially larger, or incomplete. They were rejected for an integrity-sensitive primary analysis.

No permitted mechanism in this session simultaneously provides outbound access to the official host, persistent writes to `Downloads`, HTTP range continuation, and a long-lived transfer process.

## Integrity gate before Experiment 9

Experiment 9 must not produce dataset-dependent claims until all of these pass:

1. Complete official ZIP acquisition.
2. ZIP central-directory and CRC validation.
3. Safe extraction with path-traversal checks.
4. Expected subject pickle-file inventory validation.
5. SHA-256 archive and extracted-file manifest.

## Completed work revalidated

- Baseline pipeline contract: PASS
- Enriched pipeline contract: PASS
- Cross-question synthesis contract: PASS
- Pattern falsification contract: PASS
- Experiment 5 P4-F2 validation: PASS
- Experiment 6 P4-F1 validation: PASS
- Experiment 8 deterministic replay and credential scan: PASS

No Experiment 9 dataset-dependent output has been created.

## Required next action

Complete the official archive download outside this restricted automation session, or provide a session with both outbound shell access and write permission to `Downloads`. Keep the existing partial until the replacement archive has passed integrity validation.
