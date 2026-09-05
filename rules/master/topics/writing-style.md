# Writing style

All writing — especially technical content like design docs, proposals, and explanations — must be concise and scannable.

## Core rules

- **Use bullet points over prose paragraphs.** Narrative paragraphs are only appropriate for brief introductions or context-setting (1–2 sentences max). Everything else goes in bullets.
- **Lead with bold summaries.** Every bullet should open with a **bolded phrase** that captures the point, followed immediately by explanatory prose in the same bullet. The bold text must stand alone as a scannable summary — a reader skimming only the bold text should understand the structure of the argument.
- **Cut ruthlessly.** If a word doesn't add meaning, remove it. Prefer short sentences. Avoid filler phrases like "it's worth noting that", "in order to", or "as mentioned above".
- **No redundant restatements.** Don't summarize what was just said. Don't repeat a heading's content in the first bullet beneath it.

## Bold summary bullet format

**Correct:**
- **Audit first** — enumerate all existing violations before enforcing anything, so enforcement changes don't cause surprise breakage.
- **Prefer explicit over implicit** — a flag that's visible in config is easier to audit than one inferred from environment state.

**Wrong:**
- We should start by auditing things before we enforce them because this avoids surprise breakage.
- It is generally better to be explicit rather than implicit when possible.

## Applies to

Design docs, RFCs, incident write-ups, code comments (where comments are warranted), Slack messages intended as reference material, and any other technical writing.
