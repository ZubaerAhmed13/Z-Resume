# Production hardening completion report

This branch repairs the audited static ResumeForge build without a framework rewrite.

## Fixed subsystems

- **Privacy/security:** blank first launch; synthetic demo; no embedded personal résumé data; strict self-only script CSP; no browser provider endpoint; hostile text rendered inert; validated HTTPS/data/blob photo sources; prototype-pollution rejection; bounded JSON/backup import.
- **Canonical model/migration:** schema v3 normalization; Master Profile summary canonicalized to `personal.summary`; sequential migration helper; recovery snapshot before older-workspace migration; every standard section including references/custom sections normalized.
- **Templates/order/page breaks:** all seven templates retain every standard/custom section; missing legacy-template sections use compatibility rendering; per-CV section order; Tabular moves complete heading+rows; One-Pager preserves columns; page breaks target stable section keys and calculate preview spacing to the next real page boundary.
- **Exports:** removed the handwritten PDF writer; faithful PDF path is browser Print/Save-as-PDF; DOCX uses real OOXML bullets, hyperlink relationships, Unicode and deliberate page-break metadata; Word export is explicitly text-first/ATS-oriented.
- **Storage/backups/photos:** large-photo IndexedDB references stay stable in canonical state; orphan cleanup; portable photo bytes in full backup; integrity metadata; temporary validation; pre-import recovery snapshot; rollback on persistence failure.
- **Destructive actions:** exact workspace/current-CV wording; undo snapshots for current-CV replacement; deleting the last CV deterministically creates a new blank CV.
- **Local assistant / ATS:** static external AI disabled; Local Assistant wording; nonexistent backend integrations removed from UI; ATS labelled as compatibility preflight; proficiency-aware language matching; missing requirements cannot silently become claimed skills; scripted onboarding has one deterministic transition per answer.
- **Accessibility/mobile:** modal dialog semantics/focus trap/focus restoration; Escape routing; pointer-based photo crop; reduced-motion override; 390×844 viewport regression check; keyboard-operable section move buttons; CI-pinned `axe-core@4.13.0` WCAG A/AA audits for the main editor and CV-library dialog.

## Verification executed locally

- `python tests/test_static_hardening.py` — PASS.
- `node --check assets/js/*.js` — PASS for every asset.
- `python tests/test_browser_workflows.py` — PASS: seven-template content preservation, malicious-input inertness, CEFR negative case, per-CV order isolation, modal semantics/Escape, mobile overflow, DOCX package assertions, Chromium PDF + `pdfinfo`/`pdftotext`.
- `libreoffice --headless --convert-to pdf --outdir test-artifacts/lo test-artifacts/resume.docx` — PASS; LibreOffice opens the OOXML and converts it to A4 PDF.
- `pdftotext` on the browser PDF and LibreOffice-converted DOCX PDF preserved the fixture text including `Café — résumé`, `Straße`, `Zürich`, Bengali text, projects and custom sections.
- Browser PDF validation: 2-page A4, selectable text, Unicode retained; `pdfinfo` reports `Tagged: no`.
- LibreOffice opening/conversion of the DOCX: 2-page A4; `pdfinfo` reports `Tagged: yes`; extracted Unicode text retained.
- CI is configured to install exact `axe-core@4.13.0` and fail on WCAG A/AA violations in the main editor and CV-library dialog.

## Remaining limitations

- **Medium/accessibility:** Chromium Print / Save-as-PDF is not a tagged PDF (`Tagged: no` in the release check). This is documented and the UI does not claim tagged-PDF accessibility. A future server/desktop export path with validated tagging would be required for that guarantee.
- **Low/maintainability:** `style-src 'unsafe-inline'` is still required because the legacy application uses many inline style attributes and dynamic style values. JavaScript is self-only and inline event-handler attributes have been removed. A future CSS-component refactor can remove this remaining style allowance without changing persisted data.
- **Manual-accessibility scope:** automated axe/keyboard/mobile checks cannot certify full WCAG conformance or screen-reader behavior; manual assistive-technology review remains appropriate before making a formal compliance claim.
