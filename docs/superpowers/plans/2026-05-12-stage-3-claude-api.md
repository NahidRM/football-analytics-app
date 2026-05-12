# Stage 3 — Claude API Content Generation Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a "Generate Content" section to the Streamlit app so that after viewing a visualization, Nahid can click a button and get a newsletter draft + Twitter thread in his own voice.

**Architecture:** A new `content_generator.py` module handles all Claude API interactions. Prompt templates are stored as constants (not in a database). The Streamlit app shows two editable text areas — one for newsletter, one for Twitter — after analysis. No auto-posting; copy-paste only at this stage.

**Tech Stack:** anthropic Python SDK, python-dotenv, Streamlit (existing)

**Prerequisite:** Stage 2 (Streamlit prototype) must be complete and working.

---

## File Map

| Status | File | Responsibility |
|--------|------|----------------|
| NEW | `src/content_generator.py` | Claude API calls + prompt templates |
| NEW | `.env` | `ANTHROPIC_API_KEY` (never committed to git) |
| MODIFY | `src/app.py` | Add "Generate Content" section after visualization |
| MODIFY | `requirements.txt` | Add `anthropic`, `python-dotenv` |
| MODIFY | `.gitignore` | Ensure `.env` is ignored |

---

## Task 1: Add dependencies and API key

**Files:**
- Modify: `requirements.txt`
- Create: `.env`
- Modify: `.gitignore`

- [ ] **Step 1: Add anthropic and python-dotenv to requirements.txt**

Add these two lines to `requirements.txt`:
```
anthropic
python-dotenv
```

- [ ] **Step 2: Install new dependencies**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app"
source venv/bin/activate
pip install anthropic python-dotenv
```

Expected: both install without error.

- [ ] **Step 3: Create .env file with your API key**

Create a file called `.env` in the project root (same level as `requirements.txt`):
```
ANTHROPIC_API_KEY=your_actual_key_here
```

Replace `your_actual_key_here` with your real Anthropic API key from https://console.anthropic.com/

- [ ] **Step 4: Verify .env is in .gitignore**

Open `.gitignore` and confirm `.env` appears in it. If it doesn't, add this line:
```
.env
```

This is critical — never commit API keys to git.

- [ ] **Step 5: Commit (requirements only, not .env)**

```bash
git add requirements.txt .gitignore
git commit -m "chore: add anthropic and python-dotenv dependencies"
```

---

## Task 2: Create content_generator.py

**Files:**
- Create: `src/content_generator.py`

- [ ] **Step 1: Create src/content_generator.py**

```python
# content_generator.py
#
# PURPOSE: Generate newsletter and Twitter content using the Claude API.
# All prompt templates live here. The Streamlit app calls generate_content()
# and receives two strings: a newsletter draft and a Twitter thread.
#
# HOW THE CLAUDE API WORKS:
# You send a list of "messages" (like a conversation) and Claude responds.
# The system prompt sets the context and voice. The user message provides
# the specific match data. Claude returns a response you can display or edit.

import os
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()   # reads ANTHROPIC_API_KEY from .env into os.environ

_client = Anthropic()   # reads API key from environment automatically

# The voice briefing tells Claude who is writing and how they sound.
# Adjust this to match how you actually write — the more specific, the better.
VOICE_BRIEF = """
You are writing as Nahid, a football analyst and content creator. 
Writing style:
- Direct and confident, not hedging or over-qualifying
- Uses data to make specific points, not vague praise
- Tactical observations grounded in what the numbers show
- Conversational but informed — like a knowledgeable fan, not a corporate journalist
- Never starts with "In the world of football..." or any generic opener
- No bullet points in newsletter prose — flowing paragraphs
- Twitter threads are punchy, each tweet stands alone, ends the thread with a summary take
"""


def generate_content(
    analysis_type: str,
    team: str,
    match_label: str,
    stats_summary: str
) -> tuple[str, str]:
    """
    Generate a newsletter draft and Twitter thread for a completed analysis.

    Args:
        analysis_type: 'Passing Network', 'Heat Map', 'Shot Map', or 'Press Map'
        team:          Team name (e.g. 'Arsenal')
        match_label:   Match description (e.g. 'Arsenal 4-2 Liverpool | PL 2003/04')
        stats_summary: Key stats as a plain-text string (e.g. 'Total xG: 2.4, Shots: 12')

    Returns:
        Tuple of (newsletter_draft, twitter_thread) — both plain strings.
    """
    prompt = _build_prompt(analysis_type, team, match_label, stats_summary)

    response = _client.messages.create(
        model='claude-sonnet-4-6',
        max_tokens=1500,
        system=VOICE_BRIEF,
        messages=[{'role': 'user', 'content': prompt}]
    )

    full_text = response.content[0].text

    # The response is structured with clear section headers — split on them
    newsletter_draft, twitter_thread = _parse_response(full_text)
    return newsletter_draft, twitter_thread


def _build_prompt(
    analysis_type: str,
    team: str,
    match_label: str,
    stats_summary: str
) -> str:
    """Build the user-facing prompt for content generation."""

    analysis_context = {
        'Passing Network': (
            'a passing network showing how the team connected in possession, '
            'including average player positions and pass volume between pairs'
        ),
        'Heat Map': (
            'a touch heat map showing where the featured player spent most of '
            'their time on the pitch throughout the match'
        ),
        'Shot Map': (
            'a shot map showing every attempt at goal, sized by xG (expected goals), '
            'with goals highlighted'
        ),
        'Press Map': (
            'a press intensity map showing where the team applied defensive pressure, '
            'broken down by pitch third'
        ),
    }.get(analysis_type, f'a {analysis_type} analysis')

    return f"""
I've just generated {analysis_context} for {team} in {match_label}.

Key stats from this analysis:
{stats_summary}

Please write two pieces of content based on this analysis:

---
NEWSLETTER DRAFT
---
Write 2-3 paragraphs for a football newsletter. Focus on what the data reveals tactically.
Make one specific, interesting observation that a casual fan might not have noticed.

---
TWITTER THREAD
---
Write a 4-tweet thread. Format each tweet as:
Tweet 1/4: [content]
Tweet 2/4: [content]
Tweet 3/4: [content]
Tweet 4/4: [content]

Each tweet must be under 280 characters. The thread should tell a mini story about the analysis.
"""


def _parse_response(text: str) -> tuple[str, str]:
    """Split the Claude response into newsletter and Twitter sections."""
    newsletter = ''
    twitter    = ''

    if 'NEWSLETTER DRAFT' in text and 'TWITTER THREAD' in text:
        parts      = text.split('TWITTER THREAD')
        newsletter = parts[0].replace('NEWSLETTER DRAFT', '').strip().strip('---').strip()
        twitter    = parts[1].strip().strip('---').strip()
    else:
        # Fallback: return the full text as newsletter if parsing fails
        newsletter = text
        twitter    = ''

    return newsletter, twitter
```

- [ ] **Step 2: Write a quick manual test**

```bash
cd "/Users/nahidmuzammil/Documents/Claude/Projects/Analysis app"
source venv/bin/activate
python3 -c "
import sys; sys.path.insert(0, 'src')
from content_generator import generate_content
newsletter, twitter = generate_content(
    'Shot Map', 'Arsenal',
    'Arsenal 4-2 Liverpool | Premier League 2003/04',
    'Shots: 12, Goals: 4, Total xG: 2.41'
)
print('=== NEWSLETTER ===')
print(newsletter[:300])
print()
print('=== TWITTER ===')
print(twitter[:300])
"
```

Expected: prints two blocks of text, neither empty. (This makes a real API call — costs ~$0.01.)

- [ ] **Step 3: Commit**

```bash
git add src/content_generator.py
git commit -m "feat: add content_generator with Claude API integration"
```

---

## Task 3: Add content section to app.py

**Files:**
- Modify: `src/app.py`

Add the content generation section after the visualization display. Only appears after a visualization has been generated.

- [ ] **Step 1: Add import at the top of app.py**

After the existing imports, add:
```python
from content_generator import generate_content
```

- [ ] **Step 2: Add stats_summary builder inside the `if run:` block**

After `st.pyplot(fig)` and the download button, add:

```python
            # Build a stats summary string for the content generator
            # Each analysis type pulls different stats from the events DataFrame
            if selected_analysis == 'Shot Map':
                shots = events[(events['type'] == 'Shot') & (events['team'] == selected_team)]
                goals = shots[shots['shot_outcome'] == 'Goal']
                total_xg = shots['shot_statsbomb_xg'].fillna(0).sum()
                stats_summary = (
                    f"Shots: {len(shots)}, Goals: {len(goals)}, "
                    f"Total xG: {total_xg:.2f}, xG per shot: {total_xg/max(len(shots),1):.2f}"
                )
            elif selected_analysis == 'Press Map':
                pressure = events[
                    (events['type'] == 'Pressure') & (events['team'] == selected_team)
                ]
                def_presses = len(pressure[pressure['x'] < 40]) if 'x' in pressure.columns else 0
                stats_summary = f"Total pressures: {len(pressure)}"
            elif selected_analysis == 'Passing Network':
                passes = events[
                    (events['type'] == 'Pass') & (events['team'] == selected_team) &
                    (events['pass_outcome'].isna())
                ]
                stats_summary = f"Successful passes: {len(passes)}"
            elif selected_analysis == 'Heat Map':
                player_events = events[
                    (events['team'] == selected_team) &
                    (events['player'] == selected_player) &
                    (events['location'].notna())
                ]
                stats_summary = (
                    f"Player: {selected_player}, "
                    f"Total touch events: {len(player_events)}, "
                    f"Event types: {', '.join(player_events['type'].value_counts().head(3).index.tolist())}"
                )
            else:
                stats_summary = 'No stats available'

            # Content generation section
            st.divider()
            st.subheader('Generate Content')
            st.caption('AI-drafted content in your voice. Edit before publishing.')

            if st.button('Generate Newsletter Draft + Twitter Thread'):
                with st.spinner('Writing content...'):
                    try:
                        newsletter, twitter = generate_content(
                            selected_analysis, selected_team,
                            match_label, stats_summary
                        )

                        col1, col2 = st.columns(2)

                        with col1:
                            st.markdown('**Newsletter Draft**')
                            st.text_area(
                                label='newsletter',
                                value=newsletter,
                                height=300,
                                label_visibility='collapsed'
                            )

                        with col2:
                            st.markdown('**Twitter Thread**')
                            st.text_area(
                                label='twitter',
                                value=twitter,
                                height=300,
                                label_visibility='collapsed'
                            )

                    except Exception as e:
                        st.error(f'Content generation failed: {e}')
```

- [ ] **Step 3: Run the app and test the full flow**

```bash
streamlit run src/app.py
```

1. Generate a Shot Map for Arsenal
2. Click "Generate Newsletter Draft + Twitter Thread"
3. Verify two text areas appear with readable content
4. Edit the newsletter text — verify it's editable
5. Repeat with Passing Network

- [ ] **Step 4: Commit**

```bash
git add src/app.py
git commit -m "feat: add AI content generation to Streamlit app"
```

---

## Stage 3 Complete ✓

**What you now have:**
- After any visualization, click one button to get a newsletter draft + Twitter thread
- Both text areas are editable — you edit, then copy-paste to Beehiiv or Twitter
- Content is generated in your voice via the Claude API

**Next:** Stage 4 — migrate to a real web app (Next.js + FastAPI + Supabase).
See `docs/superpowers/plans/2026-05-12-stage-4-web-app.md`
