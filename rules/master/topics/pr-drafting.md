# Draft PRs by default, follow the repo's template, keep them concise

When opening a pull/merge request, always open it in draft mode and follow the repo's own PR template. If none exists, fall back to a common shape. Keep the description concise, readable, and backed by links rather than inline explanation.

## Rules

- **Always open in draft mode**, unless the user explicitly says otherwise.
- **Use the repo's PR template if it has one** (e.g. `.github/PULL_REQUEST_TEMPLATE.md`). If none exists, fall back to a common shape — `## Summary`, `## How was it tested?`, `## Reviewers`.
- **Write for someone with little context on the change.** They should understand what changed and why without needing background beyond the description and the diff.
- **Bullets, not prose.** Avoid long blocks of text — short, scannable bullets only.
- **Only include what's relevant to this change.** Don't restate history, alternatives considered, or context the diff already shows.
- **Use links as evidence, not inline explanation.** Link to the CI run, design doc, related PR, or Slack thread instead of summarizing its contents inline — this is what keeps the description short.

## Applies to

Any pull/merge request description, on any platform (GitHub, GitHub Enterprise, GitLab, etc.).
