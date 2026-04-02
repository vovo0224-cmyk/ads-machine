---
name: ad-report
description: Generate a competitor intelligence report from your Swipe File data. Summarizes new ads, Long-Runners, killed ads, trending angles, and top hooks. Outputs as markdown ready to share with clients or your team.
---

# Ad Intelligence Report

You generate a formatted competitor intelligence report from the Ad Swipe File. This is a snapshot of what's happening in the market right now -- who's running what, what's working, what's dying, and what hooks are winning.

**What you produce:** A markdown report ready to share with clients, your team, or stakeholders.

---

## Config

Read from CLAUDE.md:
```
Airtable Base ID: YOUR_AIRTABLE_BASE_ID
Ad Swipe File Table: YOUR_SWIPE_FILE_TABLE_ID
Competitors Table: YOUR_COMPETITORS_TABLE_ID
Business: YOUR_BUSINESS_NAME
```

---

## Step 1: Pull the Data

Fetch all ads from the Swipe File:
```
Use Airtable MCP: list_records
  base_id: {from CLAUDE.md}
  table_id: {Swipe File table ID}
  fields: Ad Archive ID, Competitor, Page Name, Angle Category, Ad Format Type, Display Format, Days Active, Longevity Tier, Start Date, End Date, Hook Copy, Body Text, CTA Type, Is Active, Scrape Date
```

Also fetch competitor list:
```
Use Airtable MCP: list_records
  table_id: {Competitors table ID}
  filter: {Status}='Active'
  fields: Name, Niche Tier
```

---

## Step 2: Calculate the Numbers

From the data, calculate:

- **Total ads tracked** across all competitors
- **New ads this week** (Start Date within last 7 days)
- **Killed ads this week** (End Date within last 7 days, no longer active)
- **Long-Runners** (60d+) -- total count and any new ones
- **By competitor:** ad count, format breakdown, most common angle
- **By angle:** which angles have the most Long-Runners
- **By format:** which formats have the most Long-Runners
- **Top 5 hooks** from Long-Runners (sorted by Days Active)

---

## Step 3: Generate the Report

```markdown
# Competitor Ad Intelligence Report
**{Business Name}** | Week of {date range} | Generated {today}

---

## Market Snapshot

| Metric | Count |
|---|---|
| Competitors tracked | {N} |
| Total ads in swipe file | {N} |
| New ads this week | {N} |
| Ads killed this week | {N} |
| Long-Runners (60d+) | {N} |

---

## What's Working (Long-Runners)

These ads have been running 60+ days. Someone is paying to keep them alive.

{For each Long-Runner, show:}
1. **{Competitor}** -- {Days Active}d -- {Angle} -- {Format}
   Hook: "{first line of copy}"
   [View in Ad Library]({ad library url})

---

## What's New This Week

{N} new ads launched across {N} competitors.

| Competitor | New Ads | Formats | Dominant Angle |
|---|---|---|---|
| {name} | {count} | {formats} | {angle} |

---

## What Got Killed

{N} ads stopped running this week.

| Competitor | Killed | Avg Days Active | Common Angle |
|---|---|---|---|
| {name} | {count} | {avg days} | {angle} |

Short-lived ads (<7 days) suggest failed tests. Track what they tried and why it might have failed.

---

## Angle Breakdown

| Angle | Total Ads | Long-Runners | Win Rate |
|---|---|---|---|
| {angle} | {count} | {lr count} | {lr/total %} |

Win rate = Long-Runners / Total. Higher win rate means this angle consistently works in your market.

---

## Top 5 Proven Hooks

These hooks have the longest run times in your swipe file.

1. **{days}d** | {competitor} | {angle}
   "{hook text}"

2. **{days}d** | {competitor} | {angle}
   "{hook text}"

3. ...

---

## Recommendations

{Write 3-5 specific, actionable recommendations based on the data above. Examples:}

- "Social proof is the dominant winning angle (X% win rate). Prioritize testimonial-style ads."
- "{Competitor} launched 8 new ads this week, all video UGC. They're testing at volume -- watch for which ones survive to 14d+."
- "No competitors are using [angle]. This is a gap you could test."
- "The top 3 hooks all use question openers. Test question hooks in your next batch."
```

---

## Step 4: Save and Present

Save the report to `reports/{date}-intelligence-report.md`.

Present the full report to the user. Ask if they want to:
- Export as PDF (if Puppeteer available)
- Send to Slack (if configured)
- Save and close

---

## Report Periods

- **Weekly** (default): Last 7 days of activity
- **Monthly**: Last 30 days. Add trend comparisons (this month vs last month)
- **Custom**: User specifies date range

The user can say "weekly report", "monthly report", or "report for last 14 days".

---

## CRITICAL RULES

1. **Numbers only. No fluff.** Every line should have a data point. No "the landscape is evolving."
2. **Recommendations must be specific and actionable.** Not "consider testing more ads." Instead: "Test question-style hooks -- 4 of the top 5 Long-Runners use them."
3. **Always include Ad Library links** for Long-Runners so the reader can see the actual ad.
4. **Win rate matters more than volume.** An angle with 5 ads and 3 Long-Runners (60%) beats an angle with 50 ads and 5 Long-Runners (10%).
5. **This is a client-ready document.** No internal jargon, no system references. A marketing director should be able to read this and act on it.
