import logging
import re

from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()

_client = Anthropic()

VOICE_BRIEF = """
You are writing as Nahid, a football analyst and content creator.

Writing style:
- Direct and confident, not hedging or over-qualifying
- Notices tactical patterns and explains the WHY behind them, not just the what
- Conversational but informed — like a knowledgeable fan explaining to a smart friend
- Willing to say something is "obvious but genius" — gives credit where it's due
- Connects on-pitch observations to coaching decisions (e.g. pre-planned pressing triggers)
- Never starts with "In the world of football..." or any generic opener
- No bullet points in newsletter prose — flowing paragraphs
- Twitter threads are punchy, each tweet stands alone, ends with a clear take

Here is a real example of Nahid's writing voice (use this to match tone and rhythm):

"I watched the 2nd leg of PSG vs Bayern in the semi-final of the Champions League, and I was
pretty surprised at how ineffective Bayern were despite being on their home ground in the Allianz
Arena. During the live game, I could not understand why Olise kept fumbling and making mistakes.
I later saw a Reddit post about how PSG were directing their goal kicks and throw ins towards
Olise's side of the field just so that the team had an opportunity to regroup and press Olise's
side of the field. This told me that Luis Enrique had a clear plan — obviously they probably have
a few — but one of their plans on the field was to focus on Olise and neutralize his role in
Bayern's attack. Obvious, but genius play from Enrique, and kudos to the players for following
through on their coach's plan."
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
    newsletter_draft, twitter_thread = _parse_response(full_text)
    return newsletter_draft, twitter_thread


def _build_prompt(
    analysis_type: str,
    team: str,
    match_label: str,
    stats_summary: str
) -> str:
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
    newsletter = ''
    twitter    = ''

    if 'NEWSLETTER DRAFT' in text and 'TWITTER THREAD' in text:
        parts = text.split('TWITTER THREAD')

        # Strip section headers, separator lines, and any preamble before the newsletter
        raw_newsletter = re.sub(r'^---\s*$', '', parts[0], flags=re.MULTILINE)
        raw_newsletter = re.sub(r'^.*?NEWSLETTER DRAFT.*$', '', raw_newsletter, flags=re.MULTILINE)
        newsletter = raw_newsletter.strip()

        # Strip separator lines, then start from the first "Tweet" to remove any preamble
        raw_twitter = re.sub(r'^---\s*$', '', parts[1], flags=re.MULTILINE)
        tweet_match = re.search(r'Tweet \d+/', raw_twitter)
        twitter = raw_twitter[tweet_match.start():].strip() if tweet_match else raw_twitter.strip()
    else:
        logging.warning('content_generator: failed to parse sections from Claude response')
        newsletter = text
        twitter    = ''

    return newsletter, twitter
