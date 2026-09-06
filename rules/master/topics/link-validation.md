# Link validation

Every hyperlink written into a produced document (design docs, RRAs, questions docs, shift summaries, runbook references, etc.) must be validated before the document is finalised.

## Rules

- **Attempt each link up to 3 times** using the best available fetch tool. A successful response (HTTP 200 or readable content) counts as validated — no annotation needed.
- **If all 3 attempts fail and the link is important** (e.g. a design doc, Jira ticket, or runbook), keep the link but append `*(link unverified)*` immediately after it.
- **If all 3 attempts fail and the link is not important** (e.g. a convenience reference with an obvious fallback), omit it rather than leaving a broken link.
- **Never silently include unverified links** — every link is either validated, annotated as unverified, or omitted.
