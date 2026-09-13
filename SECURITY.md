# Security and privacy

ResumeForge is a static, browser-first application. Do not commit real CV data, credentials, provider API keys, private addresses, phone numbers, or email addresses to this repository.

Security-sensitive changes should preserve these release invariants:

- no browser-side AI/provider secret;
- no silent network transmission of CV, job-description, interview, or photo data;
- hostile imported/pasted text remains inert;
- backup/JSON imports are validated before workspace replacement;
- the production CSP keeps scripts self-only and `connect-src 'none'`;
- demo/test fixtures remain synthetic.

If reporting a vulnerability, use a minimal synthetic reproduction and do not attach real resume data.
