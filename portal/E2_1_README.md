# E2.1 — Canonical 3D laboratory

Entry point: [lab.html](lab.html), opened through an HTTP(S) web server. This standalone ESM page imports Three.js and OrbitControls from esm.sh, so an internet connection is currently required and a static-file (`file://`) open is not a supported delivery route.

## Implemented
- One persistent Three.js scene containing a floor, structural supports, wraparound gallery, glass partitions, stair run, planters, daylight and ten station rooms.
- Fixed station registry: 1 Candidate Intake; 2 Contract Normalization; 3 Strict Mechanism Audit; 4 Pattern Extraction; 5 Rival Generation; 6 Falsification Design; 7 Execution & Validation; 8 Working-Theory Update; 9 Failure Diagnostics; 10 Rejection Archive.
- Four camera presets reusing the same geometry: Overview, Discovery, Challenge and Evidence.
- Orbit, zoom, rotation, reset and clickable station focus. Reduced-motion preference disables camera easing.
- Research-scene disclaimer: no animated pipeline, evidence trace, run status, or experiment outcome is inferred by the 3D objects.

## Implementation boundaries
This is a geometric **first pass**, not a reconstruction of the reference image at exact fidelity. Buildings and fixtures are procedural low-detail approximations; no external 3D meshes, characters, textures, or moving carriers are integrated. E2.2 will require data-backed path design and animated transport; E2.3 will refine camera and interaction. Historical experiments remain unchanged.

## Verification performed
- GitHub readback confirmed the new entry point and content.
- Static checks confirmed 10 distinct station IDs, 4 camera presets, one scene, focus/selection controls, resize handling, and reduced-motion support.
- **Not yet verified:** end-to-end web rendering, WebGL performance, browser controls, visual alignment with the approved screenshots, CDN accessibility, mobile device behavior. No deployment or scientific test was performed.

## Manual browser acceptance checklist
Serve `portal` over HTTP, open `/lab.html` on desktop and mobile, confirm all 10 station rooms are visible and individually selectable, switch among four zone cameras without architectural resets, check orbit/zoom against clipping and stairs, test reduced-motion behavior, and inspect console for module/WebGL errors.

## Scientific integrity
E2.1 is a **conceptual environment only**, not a replay. Actual Experiment 17-C findings remain inconclusive (1/9 analysable units). UI metadata will be connected only after an evidence-adapter validation gate. No claim of active experiments, passing rates or professor responses is permitted without recorded provenance.
