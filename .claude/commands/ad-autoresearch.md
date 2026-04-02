---
name: ad-autoresearch
description: Daily auto-research that compares yesterday's changes against your swipe file, spots new competitor moves, identifies gaps, and suggests specific improvements to your active ads. Run after /ad-poller.
---

# Ad Auto-Research

You are a daily research analyst. You compare what changed in the market yesterday against your current ads and swipe file, then produce specific, actionable suggestions for improvement.

**What you produce:** A daily brief with competitor moves, gap analysis, and improvement suggestions tied to specific Pipeline records.

---

## Config

Read from CLAUDE.md:
```
Airtable Base ID: YOUR_AIRTABLE_BASE_ID
Ad Swipe File Table: YOUR_SWIPE_FILE_TABLE_ID
Ad Pipeline Table: YOUR_PIPELINE_TABLE_ID
Competitors Table: YOUR_COMPETITORS_TABLE_ID
```

---

## Step 1: What Changed Yesterday

Pull ads added or updated in the last 24 hours:
```
Use Airtable MCP: list_records
  table_id: {Swipe File table ID}
  filter: IS_AFTER({Scrape Date}, DATEADD(TODAY(), -1, 'days'))
  fields: Ad Archive ID, Competitor, Angle Category, Ad Format Type, Display Format, Hook Copy, Body Text, Days Active, Longevity Tier, Is Active
```

Categorise:
- **New launches:** Scrape Date = yesterday, Start Date = recent
- **Newly killed:** Was active last scrape, now inactive
- **Crossed a tier threshold:** Moved from Testing -> Solid, Solid -> Performer, or Performer -> Long-Runner since last check

---

## Step 2: What Are You Running

Pull your active Pipeline ads:
```
Use Airtable MCP: list_records
  table_id: {Pipeline table ID}
  filter: OR({Status}='Active', {Status}='Launched')
  fields: Name, Angle, Format, Hook, Status, Launch Date, Spend, Leads, CPL, Verdict
```

---

## Step 3: Compare and Analyse

### 3a. Competitor Moves
For each new competitor ad launched yesterday:
- What angle are they testing?
- What format?
- Is this a new direction for them or more of the same?
- Are they copying something that's already working for someone else?

### 3b. Gap Analysis
Compare competitor angles and formats against YOUR active ads:
- **Angles they're using that you're not** -- potential gap
- **Formats they're testing that you haven't tried** -- potential opportunity
- **Hooks that are working for them (Long-Runners) that you haven't adapted** -- low-hanging fruit

### 3c. Your Ads vs Market
For each of your active Pipeline ads:
- Is anyone else running a similar angle? How long has theirs been running?
- Is your hook pattern represented in the Proven Hooks table? If not, you're testing unproven territory.
- If your ad has been running 14+ days with poor metrics, check if competitors with similar angles have better hooks you could swap to.

---

## Step 4: Generate Suggestions

Produce 3-5 specific suggestions. Each must reference:
- A specific data point (competitor ad, Days Active, angle)
- A specific action (test this hook, try this format, kill this ad)
- Why (what the data says)

Format:
```
## Daily Research Brief -- {today's date}

### What Changed
- {Competitor} launched {N} new ads ({angles}, {formats})
- {Competitor} killed {N} ads after {avg days} (failed test)
- {N} ads crossed into Long-Runner territory (60d+)

### Your Active Ads
- {N} ads running across {angles}
- Oldest: {name} at {days}d
- Best performer: {name} ({metrics})

### Suggestions

1. **Test a {angle} hook from {competitor}'s Long-Runner**
   Their ad "{hook}" has been running {days}d. Your {pipeline ad name} uses a similar angle but a weaker hook. Consider testing their hook pattern adapted to your offer.

2. **Nobody is running {angle} in your niche**
   {N} competitors, zero ads using {angle}. This is either a gap or a graveyard. Worth one test to find out.

3. **Kill {pipeline ad name}**
   Running {days}d with {CPL}. Competitors with similar angles are averaging {X} days before killing. This one isn't working.

4. **{Competitor} just launched {format} ads for the first time**
   They've been video-only until now. Watch if these survive 14d. If so, test {format} yourself.

5. **Your top hook is stale**
   "{hook}" has been your primary hook for {days}d. Competitors have {N} newer Long-Runner hooks in the same angle. Swap to: "{suggested hook from Proven Hooks table}".
```

---

## Step 5: Save

Save the brief to `reports/{date}-daily-research.md`.

Present to the user. If Slack is configured, offer to send a summary to Slack.

---

## When to Run

- **After /ad-poller** -- the poller gets fresh data, then autoresearch analyses it
- **Daily via n8n** -- add a step after the poller workflow that triggers this
- **On demand** -- user runs it manually anytime

---

## CRITICAL RULES

1. **Every suggestion must reference specific data.** Not "consider testing new hooks." Instead: "{Competitor}'s hook ran 87 days. Yours ran 4. Test theirs."
2. **Max 5 suggestions per day.** More than that is noise. Pick the highest-impact ones.
3. **Don't suggest changes to Long-Runners.** If your ad is running 30d+ and performing, leave it alone.
4. **Kill suggestions need evidence.** Don't suggest killing an ad that's only been running 3 days. Minimum 7 days of data before a kill recommendation.
5. **Gap analysis is not a wishlist.** Just because nobody runs a certain angle doesn't mean you should. Note it as a potential test, not a must-do.
