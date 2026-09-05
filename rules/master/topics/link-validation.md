# Link validation

Every hyperlink written into a produced document (design docs, RRAs, questions docs, shift summaries, runbook references, etc.) must be validated before the document is finalised.

## Rules

- **Attempt each link up to 3 times** using the best available fetch tool. A successful response (HTTP 200 or readable content) counts as validated — no annotation needed.
- **If all 3 attempts fail and the link is important** (e.g. a design doc, Jira ticket, or runbook), keep the link but append `*(link unverified)*` immediately after it.
- **If all 3 attempts fail and the link is not important** (e.g. a convenience reference with an obvious fallback), omit it rather than leaving a broken link.
- **Never silently include unverified links** — every link is either validated, annotated as unverified, or omitted.

## HTTP status is not the only evidence

Single-page apps commonly return a 404 status while serving the app shell, so the page renders correctly in a browser and only a fetcher sees the error. MITRE ATLAS does exactly this: `https://atlas.mitre.org/techniques/AML.T0111` returns 404 with the full Vue shell, then client-side routing renders the technique.

- **A 404 carrying a full HTML app shell is a hosting artifact, not a dead link.** Check whether the body is the app shell before discarding the URL.
- **Prefer validating the underlying resource over the URL** when a machine-readable source exists. Confirming an ID appears in the project's own data file is stronger evidence than a status code, because it proves the target exists rather than that a route resolves.
- **Say which way a link was validated** if it was not a plain 200, so the reader knows the check was deliberate.
