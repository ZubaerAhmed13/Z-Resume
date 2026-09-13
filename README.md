# Z-Resume / ResumeForge

A browser-first resume workspace that runs as a static site. The hardened build keeps ordinary resume data in the browser, provides local rule-based writing/CV checks, and uses the browser print dialog as the faithful **Print / Save as PDF** path.

## Privacy and security

- First launch is blank; demo data is synthetic.
- Workspace data is stored locally in the browser unless the user explicitly exports a backup.
- The static build does **not** contain or accept provider API keys and does not send CV/job/interview content to an AI provider.
- A CSP blocks network `connect-src` requests. Remote photo URLs are an explicit user choice and are validated before use.
- Backup imports reject prototype-pollution keys before modifying workspace state.
- **Delete local workspace** removes ResumeForge local storage and the photo IndexedDB after explicit confirmation.

## Exports

- **Print / Save as PDF** opens the browser print dialog. This is the supported PDF path because it preserves the selected HTML/CSS template and selectable text.
- **ATS Word export (.docx)** is a text-first Word export. It is not advertised as pixel-identical to the visual preview.
- TXT is a simple text-first export.
- Full JSON backups include IndexedDB-backed photo bytes where they can be resolved, so they are portable to a fresh browser profile.

## AI / ATS wording

The static build uses deterministic local suggestions and an **ATS compatibility preflight**. It does not claim to be an employer ATS parser and cannot guarantee an employer's score. Optional external-AI functions intentionally fail closed unless a secure server-side integration is added in a future deployment.

## Development

No build step is required for the current static application.

Run locally:

```bash
python -m http.server 8000
```

Then open `http://localhost:8000/`.

Run the dependency-free hardening regression tests:

```bash
python tests/test_static_hardening.py
```

The test also runs `node --check` against every JavaScript asset when Node.js is available.

## Current architecture note

The audited source arrived as a ~600 KB single-file application rather than a maintainable source tree. This repair hardens the existing application and splits editable CSS/JavaScript into `assets/` instead of pretending a full framework migration was completed. Further architecture work should stay incremental and preserve user-data migrations.
