# CLAUDE.md

Behavioral guidelines to reduce common LLM coding mistakes. Merge with project-specific instructions as needed.

**Tradeoff:** These guidelines bias toward caution over speed. For trivial tasks, use judgment.

## 1. Think Before Coding

**Don't assume. Don't hide confusion. Surface tradeoffs.**

Before implementing:
- State your assumptions explicitly. If uncertain, ask.
- If multiple interpretations exist, present them - don't pick silently.
- If a simpler approach exists, say so. Push back when warranted.
- If something is unclear, stop. Name what's confusing. Ask.

## 2. Simplicity First

**Minimum code that solves the problem. Nothing speculative.**

- No features beyond what was asked.
- No abstractions for single-use code.
- No "flexibility" or "configurability" that wasn't requested.
- No error handling for impossible scenarios.
- If you write 200 lines and it could be 50, rewrite it.

Ask yourself: "Would a senior engineer say this is overcomplicated?" If yes, simplify.

## 3. Surgical Changes

**Touch only what you must. Clean up only your own mess.**

When editing existing code:
- Don't "improve" adjacent code, comments, or formatting.
- Don't refactor things that aren't broken.
- Match existing style, even if you'd do it differently.
- If you notice unrelated dead code, mention it - don't delete it.

When your changes create orphans:
- Remove imports/variables/functions that YOUR changes made unused.
- Don't remove pre-existing dead code unless asked.

The test: Every changed line should trace directly to the user's request.

## 4. Goal-Driven Execution

**Define success criteria. Loop until verified.**

Transform tasks into verifiable goals:
- "Add validation" → "Write tests for invalid inputs, then make them pass"
- "Fix the bug" → "Write a test that reproduces it, then make it pass"
- "Refactor X" → "Ensure tests pass before and after"

For multi-step tasks, state a brief plan:
```
1. [Step] → verify: [check]
2. [Step] → verify: [check]
3. [Step] → verify: [check]
```

Strong success criteria let you loop independently. Weak criteria ("make it work") require constant clarification.

---

## Project Context

**Project:** Football Analytics Web App
**Owner:** Nahid

**What this project does:**
A personal web app to analyze soccer matches (EPL + Saudi Pro League), generate visualizations (passing maps, heat maps, shot maps, pressing maps), and produce newsletter + Twitter content drafts in Nahid's voice.

**Data sources:**
- StatsBomb Open Data (free, event-level data — used in Stage 1)
- API-Football (broad league coverage including Saudi Pro League)
- FBref via soccerdata (advanced stats)
- Claude API (content generation)

**Current stage:** Stage 1 — Data pipeline + visualizations (Python scripts only, no web app yet)

**Key libraries:**
- `statsbombpy` — fetching StatsBomb open data
- `mplsoccer` — drawing football pitches and overlaying data
- `pandas` — data manipulation
- `matplotlib` — generating static images for export

**Coding preferences:**
- Nahid is learning software engineering — always explain the why behind decisions
- Prefer readable code over clever code
- Add comments that teach, not just describe
- Build in stages: make each script useful on its own before adding complexity
- All visualization scripts should save output images to an `/outputs` folder

**Teaching expectations — proactively explain, don't wait to be asked:**
- When introducing any new concept (file trees, design patterns, architectural terms), explain it in plain English before or immediately after using it — never assume it's obvious
- When sharing a file structure or diagram, always explain how to read it and what it's telling Nahid about the app
- When making a decision that has a name (e.g. "separation of concerns", "DRY", "caching"), define the term in plain English in the same message
- If something would prompt a "what does that mean?" or "why?" from a learner, answer it proactively
- The standard: would a patient senior engineer explain this to a junior without being asked? If yes, explain it

**Before proceeding with any task, always:**
- State what you are about to do and why before doing it
- Flag any architectural or approach assumptions explicitly (e.g. local vs. deployed, manual vs. automated, one script vs. multiple)
- If a decision has meaningful alternatives, name them and ask Nahid to choose
- Never silently pick an approach just because it seems obvious — what's obvious to an engineer is not always obvious to someone learning
- Wait for a green light before writing code on anything non-trivial

**Stage 1 deliverable:**
A Python script that takes a StatsBomb match ID and outputs 3-4 saved images:
1. Passing network
2. Heat map (by player)
3. Shot map with xG
4. Press intensity map
