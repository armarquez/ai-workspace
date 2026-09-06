# Design doc voice

How to draft design docs, RFCs, and proposals in my voice. Complements [writing-style.md](./writing-style.md) — that rule covers bullets and bold summaries; this one covers document structure, word choice, and the specific ways my drafts get bloated.

## Structural moves to preserve

- **Always pair scope with anti-scope.** Every doc gets Goals/Non-Goals or Supported/Non-Supported Use Cases. State what is explicitly excluded and where it is handled instead. This is the single most consistent thing I do — never drop it.
- **Current State before Proposed State.** Establish today's architecture and its concrete failures first, then propose. Never lead with the solution.
- **Document rejected alternatives, with the reason.** Each alternative gets its own section and its own Pros/Cons. A doc that only shows the chosen path is incomplete.
- **Pros/Cons on the recommendation too, not just the alternatives.** State the cost of what I am proposing.
- **Diagram first, prose second.** Any flow, sequence, architecture, or set of relationships belongs in a diagram, not a paragraph. Reach for one by default rather than treating it as optional illustration — a diagram is both clearer and shorter than the prose it replaces. Format per [diagrams.md](./diagrams.md): MermaidJS always, never ASCII art.
- **Architecture diagrams come in a Current → Proposed → Alternative set**, each with a numbered caption ("Figure 2: Proposed architecture and relevant request flows"). Reference them as "the figure below illustrates…". Offer a simplified version alongside a detailed one when the detailed one is dense.
- **Carry a Caveats field into mitigations and decisions.** When a control is in place but imperfect, say what is still wrong. Do not let a mitigation table imply a solved problem.
- **Keep an Open Questions section, populated.** Real unknowns, phrased as questions I would ask if I were reviewing.
- **Define acronyms on first use** — "Non-Human Identity (NHI)" — and add a Definitions or Terminology section when the doc has more than ~4.
- **Metrics may use X placeholders** ("reduce enablement time by X%") when the shape of the metric is agreed but the target is not. Commit to what gets measured before what the number is.
- **Fence scope aggressively.** "This is beyond the scope of this document; see [link]" is a legitimate and preferred move. Link out rather than explain inline.
- **Name owners in a table** (RACI or Owner/Deadline) for anything with cross-team execution.

## Voice to preserve

- **First person plural.** "We", "our", the team name — not "I", even in sole-authored docs.
- **Gloss abstractions with concrete instances inline** using i.e. / e.g. — "low-trust environments (e.g. staging, sandbox accounts)". This is a real strength: it keeps abstract claims verifiable. Keep it, but at most one gloss per sentence.
- **Link every claim** to a doc, PR, dashboard, or runbook inline.
- **Hedge honestly.** "Initial analysis shows", "appears to be", "we believe" are correct when the evidence is partial. Do not upgrade them to certainty.

## Conciseness — where my drafts actually fail

Measured on an 8,775-word proposal of mine: mean sentence 29.5 words, median 26, longest 102, and **18% of sentences over 40 words**. Target mean 15–20 with almost nothing over 40. Enforce this on my behalf.

- **Never write "utilize".** 23 instances in that one doc. Use "use". Same for "utilization" → "use", "leverage" → "use".
- **Cut these on sight:** "it is important to note that", "it is essential/crucial to", "in order to" → "to", "the ability to" → "can", "a variety of" → name them or say "several", "Overall,", "aims to" → "will".
- **Kill nominalizations.** "the establishment of safety measures, process definitions, and careful considerations for architecture" → "establishing safety measures, defining processes, and considering architecture". Look for -tion/-ment nouns doing a verb's job.
- **One idea per sentence.** My habit is stacking three clauses joined by "and thus", "while", "given that". Split them.
- **Do not restate the Motivation in the Goals section.** These two consistently say the same thing twice in my drafts. Motivation = why this is broken. Goals = what will be true when it is fixed.
- **A bullet is a sentence, not a paragraph.** If a bullet exceeds ~30 words it needs splitting or trimming.
- **Replace prose with a diagram or table wherever one fits.** This is the highest-leverage cut available: a paragraph describing a flow becomes a five-node diagram, and three parallel items become a table. If a section is running long, ask what in it is actually a picture before trimming words.

When drafting for me: write it in this voice, then do a dedicated cutting pass before showing me. Report the cut if it was substantial.
