# Project Learnings

A running log of software engineering concepts, decisions, and lessons learned while building the Football Analytics App. Updated as we go.

---

## How to Read This File

Each entry has:
- **What** — the concept or decision
- **Why it matters** — the practical reason this exists
- **In plain English** — a simple explanation without jargon

---

## Stage 1 Scripts — How Each One Works

### passing_network.py
**Data:** StatsBomb event data for a specific match (Arsenal 4-2 Liverpool, 2003/04). Fetched via `statsbombpy`.
**What we do with it:** Filter to Arsenal's successful passes between the starting XI, before the first substitution. Calculate each player's average passing position (where they stood when passing). Count how many times each pair of players passed to each other.
**Visualization:** Each player is a dot on the pitch, positioned at their average location. Lines connect players who passed to each other — thicker lines mean more passes between that pair. Dot size reflects how many passes that player made. Drawn using `mplsoccer`'s `Pitch` and `matplotlib`.
**Key design decisions:** Goalkeeper included automatically only if their connections clear the minimum pass threshold. Display names handled via an override dictionary for awkward StatsBomb name formats.

---

### heat_map.py
**Data:** Same StatsBomb match events. Fetched via `statsbombpy`.
**What we do with it:** Filter to all events where a chosen player (`PLAYER_NAME`) was involved and a location was recorded — passes, carries, shots, ball receipts, everything. Extract x/y coordinates from each event.
**Visualization:** A KDE (Kernel Density Estimation) heat map overlaid on the pitch. Areas where the player appeared most frequently glow brightest in the team's primary color. Background is cool grey; low-density areas fade back into it naturally. `bw_adjust=0.6` keeps the blobs tight rather than spread across the whole pitch.
**Key design decisions:** Gradient runs from pitch color → team color (not a fixed palette like 'hot') so the map is always tied to the club's identity. `TEAM` filter added to prevent silently showing a wrong-team player in the right-team color.

---

### shot_map.py
**Data:** Same StatsBomb match events. Fetched via `statsbombpy`.
**What we do with it:** Filter to all Arsenal shots. Extract location, outcome (Goal / Saved / Blocked / Off Target), and xG (expected goals — a 0–1 probability of the shot being a goal).
**Visualization:** A vertical half-pitch (attacking half only, since all shots happen there). Each shot is a dot at its location. Dot size scales with xG — bigger dot = better chance. Non-goals are team color at low opacity. Goals are bright green (`#00C853`) at full opacity with a dark outline so they immediately stand out. Goal scorer and minute are labeled above each goal dot.
**Key design decisions:** Vertical orientation chosen because it makes the goal mouth obvious at the top. Green for goals because it universally reads as "success" without the yellow card association of gold.

---

### press_map.py
**Data:** Same StatsBomb match events. Fetched via `statsbombpy`.
**What we do with it:** Filter to all `Pressure` events by Arsenal — moments when an Arsenal player actively closed down an opponent. StatsBomb records these from the pressing team's perspective, so `team == 'Arsenal'` correctly captures presses applied *by* Arsenal (not to them). Extract x/y coordinates. Count presses in each third of the pitch.
**Visualization:** A KDE heat map on a full horizontal pitch (full pitch is essential — it shows whether the team pressed high or sat deep). Purple gradient instead of team color, so it's immediately visually distinct from the player heat map. Dashed lines divide the pitch into thirds; each zone is annotated with the press count and percentage.
**Key design decisions:** Purple chosen specifically to signal "pressing / defensive analysis" — different from team-color heat maps at a glance. Zone annotations add a quantitative layer that makes the map readable in a newsletter or tweet without needing the reader to interpret the density gradient alone.

---

### config.py
**Not a visualization script** — a shared settings file imported by all four scripts above.
**What it contains:** `CLUB_COLORS` (14 clubs), pitch style constants (`PITCH_COLOR`, `LINE_COLOR`, etc.), `PRESS_COLOR`, `GOAL_COLOR`. Centralising these here means changing a color or adding a club only needs to happen in one place. This is the DRY principle in practice.

---

## Software Engineering Concepts

### How to Read a File Tree
- **What:** A file tree is a visual map of how a project's files and folders are organized on your computer. It shows you what exists and where it lives
- **How to read it:** Indentation = depth. A file indented under a folder lives inside that folder. The symbols `├──` and `└──` are just connectors — `├──` means more items follow, `└──` means last item in that folder
- **Example:**
  ```
  src/                    ← folder called src
  ├── app.py              ← file inside src
  └── visualizations/     ← folder inside src
      └── heat_map.py     ← file inside visualizations, which is inside src
  ```
- **What it tells you beyond structure:** A well-designed file tree communicates responsibility. Each folder or file should have one clear job. If you look at a file tree and can immediately guess what each file does, it's well organized. If names are vague or everything is dumped in one folder, it's a warning sign
- **Real example from this project:** `visualizations/` contains only drawing code. `data_loader.py` contains only data fetching. `app.py` contains only UI code. The structure itself communicates the design

### Separation of Concerns
- **What:** A design principle that says each part of your code should have one clear responsibility and shouldn't do anyone else's job
- **Why it matters:** When something breaks, you immediately know which file to look in. When you want to add something new, you know exactly where it goes. When you want to change how data is fetched, you only touch one file — not four
- **In plain English:** Give every file one job and one job only. Don't let your drawing code fetch data. Don't let your UI code do calculations
- **Real example from this project:** `data_loader.py` talks to StatsBomb — nothing else does. `visualizations/` draws charts — nothing else draws. `app.py` runs the UI — it doesn't fetch data or draw anything itself, it just calls the other files and shows the result
- **The opposite (what to avoid):** One giant script that fetches data, processes it, draws charts, saves files, and handles UI all in the same place. Works for a prototype, becomes a nightmare to maintain

### Feature Flags
- **What:** A setting (usually a True/False variable) at the top of a script or config file that turns a behaviour on or off without changing the underlying logic
- **Why it matters:** Instead of rewriting code for every situation, you expose a knob. The code stays the same — only the setting changes
- **In plain English:** A light switch for a feature. Flip it on or off depending on the situation
- **Real example from this project:** `INCLUDE_GOALKEEPER = True/False` — lets you decide per analysis whether to include the GK in the passing network, without touching any of the logic below
- **Where you'll see this in the real world:** Every major tech product uses feature flags — to roll out new features gradually, run A/B tests, or turn things off quickly if something breaks
- **Evolution of this idea:** The best feature flags eventually become unnecessary — when the code is smart enough to decide the right behaviour itself based on the data (see: Smart/Data-Driven Decisions below)

### Smart / Data-Driven Decisions (vs. Manual Flags)
- **What:** Instead of a human setting a flag manually, the script looks at the data and decides the right behaviour automatically
- **Why it matters:** Manual flags require the user to know things in advance (e.g. "is this GK heavily involved?"). A smart script figures it out from the data itself — no prior knowledge needed
- **In plain English:** Don't ask the user to decide what the data can decide for itself
- **Real example from this project:** Instead of `INCLUDE_GOALKEEPER = True/False`, the script checks whether the GK's passing connections clear the threshold. If they do, the GK appears automatically. If not, they're excluded automatically. The data makes the call
- **This is a better design than a feature flag** when the decision can be derived from the data — it removes a point of human error and makes the tool smarter

### DRY — Don't Repeat Yourself
- **What:** A principle that says every piece of information or logic should exist in exactly one place in your code
- **Why it matters:** If the same value (e.g. a color, a number, a string) is hardcoded in multiple places and you need to change it, you have to hunt down every instance. Miss one and you get inconsistencies and bugs
- **In plain English:** Give things names. Change the name once, it updates everywhere
- **Real example from this project:** Instead of writing `'#2d5a27'` in 4 different places, we defined `PITCH_COLOR = '#2d5a27'` once at the top. Now changing the pitch color is a one-line edit
- **The opposite (what to avoid):** "Magic numbers/strings" — hardcoded values scattered through the code with no explanation of what they mean
- **Related principle:** If you find yourself copying and pasting the same code block, that's a signal you should name it and reuse it instead

### Virtual Environments
- **What:** An isolated Python installation scoped to a single project
- **Why it matters:** Different projects need different library versions. Without isolation, they conflict with each other and break
- **In plain English:** Each project gets its own bubble. What happens inside the bubble stays inside the bubble
- **Command to create:** `python3 -m venv venv`
- **Command to activate:** `source venv/bin/activate` (Mac/Linux)
- **How to tell it's active:** Your terminal prompt shows `(venv)` at the start

### Why the Virtual Environment Folder is Called "venv"
- **What:** `venv` is just the name given to the virtual environment folder — it's a convention, not a rule
- **Why it matters:** The whole industry uses `venv` as the standard name, so any developer picking up your project knows immediately where the virtual environment lives
- **In plain English:** It could be called anything, but calling it `venv` is like naming your main branch `main` — everyone expects it
- **The command explained:** `python3 -m venv venv` = "use Python's venv module (`-m venv`) to create a virtual environment, and name the folder `venv`"

### requirements.txt
- **What:** A plain text file listing all the Python libraries a project needs
- **Why it matters:** Anyone (including future you) can recreate your exact environment by running `pip install -r requirements.txt`
- **In plain English:** A shopping list for your project's dependencies

### .gitignore
- **What:** A file that tells Git which files and folders to ignore and not track
- **Why it matters:** You don't want to accidentally commit your virtual environment (thousands of files), API keys, or auto-generated outputs to version control
- **In plain English:** A list of things Git should pretend don't exist

### CLAUDE.md
- **What:** A special markdown file that Claude Code reads automatically at the start of every session in that project folder
- **Why it matters:** It gives Claude context about your project, your preferences, and behavioral rules — so you don't have to re-explain everything each session
- **In plain English:** A briefing document Claude reads before every work session. The better it's written, the better Claude performs
- **Credit:** Guidelines based on Andrej Karpathy's published approach to LLM-assisted coding

---

## Build Approach & Architecture

### Why We Build in Stages
- **What:** Breaking a large project into 5 sequential stages, each useful on its own
- **Why it matters:** Building everything at once means when something breaks, you don't know where the problem is. Stages isolate problems and build understanding layer by layer
- **In plain English:** Test the recipe before opening the restaurant. Don't build the restaurant first.
- **Our stages:**
  1. Local Python scripts → validate data + visualizations
  2. Streamlit prototype → wrap scripts in a basic UI
  3. Claude API integration → add content generation
  4. Real web app (Next.js + FastAPI) → build the proper product
  5. Polish + expand → newsletter, Saudi league, Twitter posting

### Why Stage 1 is Local (Not Deployed)
- **What:** We start with plain Python scripts on your machine, not a deployed web app
- **Why it matters:** A web app adds a layer of infrastructure complexity. If something breaks, you'd have two places to debug: your code, and your infrastructure. Starting local means only one place to look
- **In plain English:** Get the analysis right first. Wrap it in a web app once you know it works
- **Lesson learned:** Always ask "what layer are we on?" before assuming where code should run

### Always Ask Before Assuming
- **What:** Before starting any non-trivial task, state what you're about to do, name the alternatives, and get confirmation
- **Why it matters:** What seems like an obvious approach to an engineer may not match what the owner had in mind
- **In plain English:** Say what you're going to do before you do it. Get a green light first

---

## Tech Stack Decisions

### Why FastAPI (not Flask)
- **What:** FastAPI is a modern Python web framework for building APIs
- **Why over Flask:** FastAPI is faster, has built-in data validation, auto-generates API documentation, and is the current industry standard for new Python APIs
- **In plain English:** Flask is older and simpler. FastAPI is what most teams are choosing today for new projects

### Why Next.js (not plain React)
- **What:** Next.js is a React framework with extra features like server-side rendering and file-based routing
- **Why it matters:** Easier deployment (Vercel), better performance, industry standard
- **In plain English:** React is the engine. Next.js is the car built around it — adds features that make real apps easier to build

### Why Supabase (not a simpler database)
- **What:** Supabase is a hosted PostgreSQL database with a clean dashboard and free tier
- **Why it matters:** Uses real SQL, which is the most transferable database skill. The dashboard means you can inspect your data visually
- **In plain English:** A real database you can actually see and manage, without needing to run your own server

### Why Beehiiv (not Substack)
- **What:** Beehiiv is a newsletter platform with better analytics and a real API
- **Why over Substack:** Substack has no API (can't automate anything). Beehiiv does. Better analytics, more control, free up to 2,500 subscribers
- **In plain English:** Substack is for writers. Beehiiv is for builders who also write

---

## Data & Football Analytics

### Why StatsBomb Open Data for Stage 1
- **What:** StatsBomb publishes free event-level football data for specific competitions
- **Why it matters:** Event-level data means every single pass, press, carry, and shot is recorded with x/y coordinates on the pitch — this is what powers real heat maps and passing networks
- **In plain English:** Most free data tells you the score. StatsBomb tells you every touch

### The Saudi Pro League Data Gap
- **What:** Professional event-level data for the Saudi Pro League doesn't exist at affordable prices yet
- **Why it matters:** We can get basic stats (scores, possession %) but not deep visualizations for Saudi games
- **Opportunity:** Almost no analysts are covering the Saudi league with tactical depth — even basic analysis stands out
- **Plan:** Design for it now, upgrade data when it becomes available or budget allows

### Combined Data Source Strategy
- **What:** Using multiple data sources together rather than relying on one
- **Sources:** StatsBomb (event data), API-Football (broad coverage), FBref (advanced stats), Understat (xG)
- **Why it matters:** No single affordable source covers everything we need. Combining them gives broader coverage at lower cost
- **In plain English:** Use the best tool for each job

---

## Content & Voice

### Why Claude API for Content Generation
- **What:** Using Anthropic's Claude API to generate newsletter drafts and Twitter threads
- **Why Claude over others:** Best model currently available for nuanced, natural-sounding writing
- **Key challenge:** Getting AI to write in Nahid's voice, not in generic AI-speak — this requires careful prompt engineering
- **In plain English:** The AI writes a draft. Nahid edits it to sound like himself

### Prompt Engineering (Coming in Stage 3)
- **What:** The craft of writing instructions to an AI model that produce the output you actually want
- **Why it matters:** A vague prompt gets generic output. A specific, well-structured prompt gets output that sounds like you wrote it
- **In plain English:** How you ask determines what you get

### fig.text() vs ax.text() — Figure Level vs Axes Level
- **What:** Two different coordinate systems for placing text in matplotlib
- **`ax.text(x, y)`** — places text using the pitch's own coordinates (e.g. StatsBomb's 0–120 x-axis). Text sits inside the pitch and can overlap pitch lines
- **`fig.text(x, y)`** — places text using normalised figure coordinates (0 to 1). Text sits outside the pitch, relative to the whole image
- **Why it matters:** Putting a legend inside the pitch (`ax.text`) means it competes with pitch markings. Using `fig.text` places it cleanly below or beside the pitch, always uninterrupted
- **In plain English:** `ax` is inside the football pitch. `fig` is the whole poster. Use `fig` when you want something that never overlaps the pitch

### Fix Problems at the Source, Not at the Display Layer
- **What:** When filtering or transforming data, do it early in the pipeline — not just before drawing
- **Why it matters:** If you only hide something visually at the end, the hidden data still affects calculations upstream. E.g. hiding the GK's dot at draw time still lets their passes skew other players' average positions
- **In plain English:** Don't put a sticker over a mistake. Fix the mistake before it affects anything else
- **Real example from this project:** We removed the GK from the pass filter (Step 4), not from the drawing loop (Step 8). This meant the GK's passes couldn't distort anyone else's average position on the pitch

### Deriving Active Players from Data
- **What:** Instead of manually listing who should appear, let the data tell you
- **Why it matters:** Manual lists go stale and require human knowledge. Deriving from data is automatic and always correct
- **In plain English:** Don't hardcode who shows up. Ask the data who earned a spot
- **Real example from this project:** `active_players = set(pass_combinations['player'] + pass_combinations['pass_recipient'])` — only players with connections above the threshold appear. No list needed, no manual decisions

### KDE — Kernel Density Estimation (How Heat Maps Work)
- **What:** A mathematical technique that takes a scattered set of points (e.g. a player's touch locations) and smooths them into a continuous "heat" surface — brighter areas mean more activity
- **Why it matters:** Raw dots on a pitch are hard to read at a glance. KDE converts those dots into a colour gradient, making patterns (e.g. "this player lived in the left half-space") immediately visible
- **In plain English:** Imagine dropping a warm glowing disc on every single touch a player made. Each disc spreads its heat outward slightly. Wherever the discs overlap, the heat stacks up and the colour gets brighter. KDE is just the maths that does this automatically
- **What "kernel" means:** The shape of that glowing disc — how far each point's influence spreads. A wider kernel = more blurry/smooth. A narrower kernel = more precise but spiky
- **What "density" means:** How many events are concentrated in a given area. High density = lots of touches = hot colour
- **How mplsoccer uses it:** The `pitch.kdeplot()` method handles all the maths. You give it x/y coordinates and it draws the heat map — no manual maths needed
- **Real example (coming next):** We'll pass in every touch location for one player and `pitch.kdeplot()` will show where they spent most of their time on the pitch

### pyenv — Python Version Manager
- **What:** A tool that lets you install and switch between multiple Python versions on one machine
- **Why it matters:** Different projects need different Python versions. Without a manager, they conflict or you're stuck on one version forever
- **Commands that matter:**
  - `brew install pyenv` — install pyenv
  - `pyenv install 3.11.9` — install a specific Python version
  - `pyenv global 3.11.9` — set default Python for your whole machine
  - `pyenv local 3.11.9` — pin a specific version to one project folder only
- **In plain English:** A shoe rack for Python versions. Pick which pair you're wearing per project

### StatsBomb Compound Name Quirks
- **What:** StatsBomb stores player names in full legal form, which often doesn't match how fans know them
- **Why it matters:** Taking the "last word" of a name doesn't always give the surname — some players have 3-4 word names, hyphens, or embedded nicknames with quote characters
- **Solution:** A `DISPLAY_NAME_OVERRIDES` dictionary maps exact StatsBomb names to display names, with a smart fallback for everything else
- **Known examples from Arsenal 2003/04:**
  - `"Sulzeer Jeremiah ''Sol' Campbell"` → Campbell (has literal quote characters)
  - `'Laureano Bisan-Etame Mayer'` → Lauren (hyphenated compound surname)
  - `'Kolo Habib Touré'` → Touré (middle name trips up the fallback logic)
  - `'Gilberto Aparecido da Silva'` → Gilberto (4-word name, first name is correct)
- **Lesson:** Always print `repr(player_name)` to see the exact string before writing overrides

---
### How the Press Intensity Map Works
- **What:** A heat map showing where a team applied defensive pressure throughout a match
- **Data source:** StatsBomb records a `Pressure` event every time a player actively closes down an opponent, including the x/y location of where that happened
- **Why KDE and not dots:** Pressing is a team zone behaviour — you want to see *which areas of the pitch* the team hunted in, not track individual moments. KDE smooths all the pressure events into a density map that makes the pattern immediately readable
- **Why full pitch:** The whole point of a press map is understanding *where on the pitch* a team defends. A high press shows up as density in the opponent's half; a mid-block shows up in the team's own half. Cutting to half the pitch would hide that story
- **Important detail — what the location actually represents:** StatsBomb records the location of the Arsenal player doing the pressing, not the ball. In practice these are very close (if Cole is pressing a Liverpool winger, he's right next to them), but it's not exact. Think of it as "where Arsenal players were when they decided to press" rather than "where the ball was when they pressed." For understanding defensive shape and press zones, it's accurate enough to be meaningful

### The Code Reviewer Agent — When and How to Use It
- **What it is:** A specialized Claude agent that reads your code cold — with no memory of the decisions made during the build — and gives an independent assessment
- **Why that matters:** When you've been deep in building something, you rationalize decisions as you go. The reviewer hasn't done that. It sees the code as a stranger would, which means it catches things you've become blind to
- **When to use it:** At natural checkpoints — end of a stage, before wrapping a UI around scripts, before sharing code with anyone. Not after every small change — that's overkill
- **How to write a good brief for it:** The agent has zero context from your conversation, so the prompt needs to be self-contained. Include: what the scripts do, what files to look at, and any specific questions you already have (e.g. "is this filter correct?"). The more specific the question, the more useful the answer
- **How to handle its findings:** It will find things of varying importance. Not everything it flags needs to be fixed immediately — use judgment to prioritize. Critical bugs first, then consistency issues, then minor neatness
- **Real example from this project:** We used it at the end of Stage 1. It confirmed the press map filter was correct, caught a legend mismatch in the shot map, flagged duplicated `CLUB_COLORS` across 4 files, and found a silent bug where the heat map could show a Liverpool player in Arsenal red. All caught before Stage 2

*Last updated: Stage 1 complete and reviewed — all 4 scripts built, reviewed, and fixed*
