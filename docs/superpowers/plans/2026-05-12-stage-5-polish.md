# Stage 5 — Polish & Expand Roadmap

> **Note:** This is a roadmap, not an executable plan. When ready to build any item here, use `superpowers:writing-plans` to create a full task-level plan for that specific feature.

**Goal:** Expand the app beyond StatsBomb's free data to cover real live matches (including Saudi Pro League), integrate directly with Beehiiv for newsletter publishing, and refine the AI voice quality.

**Prerequisite:** Stage 4 complete — real web app deployed and working.

---

## Feature Backlog

### 1. API-Football Integration (Saudi Pro League + Live Matches)
- Sign up for API-Football Pro plan (~$25/month)
- Add a second data provider alongside StatsBomb
- Map API-Football's data format to the existing visualization functions (passing, shots, press events where available)
- Add Saudi Pro League to the competition selector
- **Honest caveat:** API-Football doesn't have event-level data (no touch locations). Passing networks and heat maps won't be available for Saudi matches at first — only shot maps and basic stats.
- When full event data becomes available for Saudi league, swap in the richer data source

### 2. Beehiiv Newsletter Integration
- Sign up for Beehiiv (free up to 2,500 subscribers)
- Use Beehiiv API to push newsletter drafts directly to a draft post
- Add "Send to Beehiiv" button in the content editor (instead of copy-paste)
- User still reviews and publishes manually from Beehiiv dashboard

### 3. Voice Quality Improvements for Claude
- After publishing 10+ pieces, review: which AI drafts needed the least editing?
- Identify patterns: what does Claude get right vs. what always needs rewriting?
- Update the `VOICE_BRIEF` in `content_generator.py` with specific examples of Nahid's actual published writing
- Consider few-shot prompting: include 2-3 real examples in the prompt

### 4. Twitter/X Direct Posting (Optional)
- Requires a Twitter Developer account (may require paid access)
- Add Twitter API credentials to environment variables
- Add "Post Thread to Twitter" button — posts each tweet in sequence
- Rate limiting: Twitter API has strict rate limits, add a delay between tweets
- **Recommendation:** Start with copy-paste (Stage 3). Only add direct posting if the copy-paste workflow genuinely feels like a bottleneck after real use.

### 5. Analysis History & Search
- Add search/filter to the analysis history page (currently just a list)
- Filter by team, competition, analysis type, date range
- "Re-run" button to regenerate a visualization for a saved analysis

### 6. Multiple Visualizations Per Session
- Currently: one visualization per page load
- Add a "Compare" mode: generate two analyses side by side (e.g. both teams' passing networks)
- Or: generate all four analysis types at once for a match and display as tabs

---

## When to start Stage 5

Don't start Stage 5 until:
- Stage 4 is fully deployed and you've used the app for real (published at least 3 pieces of content through it)
- You know which features are actually missing vs. which ones seemed important but don't matter in practice
- The Saudi Pro League data situation has clarified (richer data may become available)

Real usage will reveal which items in this backlog matter. Don't build features you haven't needed yet.
