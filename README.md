# Z-Resume / ResumeForge

A privacy-conscious, browser-first resume workspace for static GitHub Pages deployment. The hardened build keeps ordinary résumé data in the current browser, uses transparent local writing/CV-quality tools, and uses the browser print engine as the supported **Print / Save as PDF** path.

## Build layout

The connected GitHub write transport used for this repair could not write several legacy source files in one request. To preserve the **exact locally validated bytes**, the deployable source is stored in an integrity-checked `tar.xz` transport pack split across `src/site-pack/*.b64`. `src/site-manifest.json` records the only permitted output paths plus exact byte counts and SHA-256 hashes. `scripts/build_site.py` validates the archive and every extracted file before writing `index.html`, CSS, or JavaScript.

Build ordinary source files locally:

```bash
python scripts/build_site.py --output .
python -m http.server 8000
```

The reconstruction is deterministic with respect to the deployable files: it reproduces the locally tested `index.html`, 2 CSS assets, and 7 JavaScript assets byte-for-byte. CI reconstructs them before testing; the Pages workflow reconstructs into `_site/` before deployment from `main`.

## Privacy and security

- First launch is blank; demo content is synthetic.
- CVs, job descriptions, interview notes, versions, and preferences stay in browser storage unless explicitly exported.
- Large photos are stored once in IndexedDB and referenced by stable IDs; portable backups include image bytes for clean-profile restoration.
- The static build contains no provider API key and no browser-side external-AI endpoint.
- CSP keeps scripts self-only; `connect-src` is `none`; objects/frames are disabled.
- Imported JSON/backups are shape-checked, prototype-pollution keys are rejected, photo URLs are allowlisted, and hostile rendered text stays inert.
- **Delete local workspace** removes local workspace storage and the photo database after confirmation.

## Canonical resume model

Schema v3 supports personal/header information, summary, work experience, education, projects, skills, tools, languages with CEFR A1–C2, certificates with optional credential URLs, achievements, hobbies/interests, volunteering, publications, coursework, references, custom sections, photo references, per-CV visual preferences, per-CV section order, and section-ID page breaks.

Master Profile summary data is canonical at `masterProfile.personal.summary`; migration normalizes historical shapes and retains a pre-migration recovery snapshot.

## Templates and ordering

All seven templates are regression-tested with every standard section plus custom content. Legacy template gaps use compatibility rendering instead of silently dropping data. Section order is stored per CV. Tabular reordering moves heading-plus-row units together; One-Pager preserves its intentional columns and reorders within the relevant column.

## Exports

- **Print / Save as PDF** uses the browser print engine, preserving the selected HTML/CSS template, selectable text, links, section order, and tested Unicode text.
- **ATS Word export (.docx)** is text-first rather than pixel-identical to the preview. It uses OOXML bullets, real hyperlink relationships, Unicode text, and deliberate page-break metadata.
- Full workspace backups are versioned and portable; imports validate before replacement and retain a pre-import recovery snapshot.

## Local assistant and ATS wording

The GitHub Pages build uses deterministic local suggestions and an **ATS compatibility preflight**. These are advisory rules, not an employer ATS parser or guaranteed ATS score. Missing job requirements remain gaps until the user truthfully confirms an editable suggestion. No external provider or secret key is required by the static site.

## Verification

```bash
python scripts/build_site.py --output .
python tests/test_static_hardening.py
for f in assets/js/*.js; do node --check "$f"; done
python tests/test_browser_workflows.py
libreoffice --headless --convert-to pdf --outdir test-artifacts/lo test-artifacts/resume.docx
```

CI installs Chromium, Poppler, LibreOffice Writer, Playwright, and pinned `axe-core@4.13.0` and runs the same security/template/accessibility/export suite.

## Known limitations

- Chromium Print / Save-as-PDF is structurally valid, selectable, and Unicode-safe in the release fixture, but `pdfinfo` reports `Tagged: no`; the product therefore does **not** claim tagged-PDF accessibility.
- CSP still needs `style-src 'unsafe-inline'` because the inherited interface has many inline style attributes/dynamic style values. JavaScript is self-only and inline JavaScript event handlers have been removed.
- Automated axe/keyboard/mobile checks do not substitute for a formal manual screen-reader audit.
- The transport pack is less convenient for code review than ordinary committed source files. Running the build script produces the normal source tree byte-for-byte; a future direct Git transport can flatten those generated files into the repository without changing application behavior.
