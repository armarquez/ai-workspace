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
- **Quote another document's defined terms and keep their exact noun.** Phase names, outcome IDs, and threat IDs belong to the source doc: write `the "Catalog" phase`, not `the Catalog stage` or `the Catalog cycle`. Paraphrasing the noun ("phase" into "cadence") silently breaks traceability back to the source. Skip the quotes only inside diagram labels, where the delimiters collide.
- **Never coin a term in conversation and then use it in the doc as if established.** Working vocabulary from a drafting session ("the amplification lens", "the corpus layer") reads as real terminology to whoever wrote it and as noise to everyone else. Either define it in the doc or replace it with a generic example.
- **Metrics may use X placeholders** ("reduce enablement time by X%") when the shape of the metric is agreed but the target is not. Commit to what gets measured before what the number is.
- **Fence scope aggressively.** "This is beyond the scope of this document; see [link]" is a legitimate and preferred move. Link out rather than explain inline.
- **Name owners in a table** (RACI or Owner/Deadline) for anything with cross-team execution.

## Voice to preserve

- **First person plural.** "We", "our", the team name — not "I", even in sole-authored docs.
- **Gloss abstractions with concrete instances inline** using i.e. / e.g. — "low-trust environments (e.g. staging, sandbox accounts)". This is a real strength: it keeps abstract claims verifiable. Keep it, but at most one gloss per sentence.
- **Link every claim** to a doc, PR, dashboard, or runbook inline.
- **Hedge honestly.** "Initial analysis shows", "appears to be", "we believe" are correct when the evidence is partial. Do not upgrade them to certainty.
- **Plain working English, never academic register.** The test: if I would not say the word out loud in a meeting, do not write it. "Unfalsifiable" is the canonical offender — write "a bar we can never show we have met". Same for other philosophy-of-science or theory vocabulary that sounds precise but is not how I talk.

## Conciseness — where my drafts actually fail

Measured on an 8,775-word proposal of mine: mean sentence 29.5 words, median 26, longest 102, and **18% of sentences over 40 words**. Target mean 15–20 with almost nothing over 40. Enforce this on my behalf.

- **Never write "utilize".** 23 instances in that one doc. Use "use" — "use" itself is never the problem, the fancy synonyms are. Same for "utilization" → "use", "leverage" → "use", and figurative verbs like "ride" or "harness" → "use".
- **Cut these on sight:** "it is important to note that", "it is essential/crucial to", "in order to" → "to", "the ability to" → "can", "a variety of" → name them or say "several", "Overall,", "aims to" → "will".
- **Kill nominalizations.** "the establishment of safety measures, process definitions, and careful considerations for architecture" → "establishing safety measures, defining processes, and considering architecture". Look for -tion/-ment nouns doing a verb's job.
- **One idea per sentence.** My habit is stacking three clauses joined by "and thus", "while", "given that". Split them.
- **Do not restate the Motivation in the Goals section.** These two consistently say the same thing twice in my drafts. Motivation = why this is broken. Goals = what will be true when it is fixed.
- **A bullet is a sentence, not a paragraph.** Plain list bullets stay under ~30 words. Bold-summary bullets (bold lead plus explanation, per [writing-style.md](./writing-style.md)) may run to ~45 because the lead carries its own weight — but the part after the bold is at most two sentences.
- **Prefer bullets over paragraphs for independent points.** If consecutive paragraphs each open with a bold lead, they are already bullets — convert them.
- **Replace prose with a diagram or table wherever one fits.** This is the highest-leverage cut available: a paragraph describing a flow becomes a five-node diagram, and three parallel items become a table. If a section is running long, ask what in it is actually a picture before trimming words.

When drafting for me: write it in this voice, then do a dedicated pass before showing me. That pass has two parts, both mandatory:

1. **Cut.** Apply the conciseness rules above. Report the cut if it was substantial.
2. **Sweep for coined vocabulary.** Grep the draft for every noun and label that came from our conversation rather than from a source document or published standard — structure names, stage or layer labels, category names, shorthand. For each, either cite where it comes from, define it in the doc, or replace it with plain description. Assume I will ask "where did this come from?" about anything that reads like established terminology, and answer that question in the doc before I have to ask it.

The sweep is not optional and not conditional on suspicion. Coined vocabulary reads as real terminology to whoever wrote it, so it is invisible without a deliberate check.
