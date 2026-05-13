#!/usr/bin/env python3
"""
팟노블 Daily Ad Pipeline
경쟁사 광고 수집 → Airtable 저장 → Gmail 리포트 발송
"""
import os, json, time, smtplib, urllib.request, urllib.error
from datetime import datetime, date
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

# === CONFIG ===
AIRTABLE_KEY = os.environ["AIRTABLE_API_KEY"]
APIFY_TOKEN  = os.environ["APIFY_TOKEN"]
GMAIL_USER   = os.environ["GMAIL_USER"]
GMAIL_PASS   = os.environ["GMAIL_APP_PASSWORD"]
BASE_ID      = "appfxyHine1JWPTHA"
COMPETITORS_TABLE = "tblsz0J8E04kzyV1A"
SWIPE_TABLE  = "tblpeuUHtNauLbEwo"
TODAY        = date.today().isoformat()

FORMAT_MAP = {"VIDEO": "Video", "IMAGE": "Image", "CAROUSEL": "Carousel", "DCO": "DCO"}

COUNTRY_MAP = {
    "PLING": "🇰🇷 한국",
    "달보이스": "🇰🇷 한국",
    "오디오코믹스": "🇰🇷 한국",
    "윌라 스토리": "🇰🇷 한국",
    "밀리의서재": "🇰🇷 한국",
    "audiobook.jp": "🇯🇵 일본",
    "朗読少女": "🇯🇵 일본",
    "Readmoo": "🇹🇼 대만",
    "Dreame": "🌏 글로벌",
    "GoodNovel": "🌏 글로벌",
    "Alex Hormozi": "🌏 글로벌 (프레임워크)",
    "Pocket FM": "🌏 글로벌",
    "My Vampire System By Pocket FM": "🌏 글로벌",
}

def airtable_get(table, params=""):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table}?{params}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {AIRTABLE_KEY}"})
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def airtable_post(table, records):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table}"
    payload = json.dumps({"records": records}).encode()
    req = urllib.request.Request(url, data=payload,
          headers={"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"},
          method="POST")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def airtable_patch(table, records):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table}"
    payload = json.dumps({"records": records}).encode()
    req = urllib.request.Request(url, data=payload,
          headers={"Authorization": f"Bearer {AIRTABLE_KEY}", "Content-Type": "application/json"},
          method="PATCH")
    with urllib.request.urlopen(req) as r:
        return json.loads(r.read())

def apify_run(page_id):
    url = f"https://api.apify.com/v2/acts/apify~facebook-ads-scraper/runs?token={APIFY_TOKEN}"
    payload = json.dumps({"startUrls": [{"url": f"https://www.facebook.com/ads/library/?active_status=all&ad_type=all&country=ALL&media_type=all&search_type=page&sort_data[direction]=desc&sort_data[mode]=total_impressions&view_all_page_id={page_id}"}], "resultsLimit": 50}).encode()
    req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"}, method="POST")
    with urllib.request.urlopen(req) as r:
        run_id = json.loads(r.read())["data"]["id"]

    for _ in range(40):
        time.sleep(10)
        with urllib.request.urlopen(f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}") as r:
            status = json.loads(r.read())["data"]["status"]
        if status == "SUCCEEDED":
            break
        if status in ("FAILED", "ABORTED"):
            return []

    ds = json.loads(urllib.request.urlopen(f"https://api.apify.com/v2/actor-runs/{run_id}?token={APIFY_TOKEN}").read())["data"]["defaultDatasetId"]
    with urllib.request.urlopen(f"https://api.apify.com/v2/datasets/{ds}/items?token={APIFY_TOKEN}&limit=50") as r:
        return json.loads(r.read())

def parse_date(val):
    if not val: return None
    try:
        if isinstance(val, (int, float)):
            return datetime.utcfromtimestamp(val).strftime("%Y-%m-%d")
        return datetime.fromisoformat(str(val).replace("Z", "+00:00")).strftime("%Y-%m-%d")
    except: return None

def longevity_tier(days):
    if days is None: return "Testing"
    if days >= 60: return "Long-Runner"
    if days >= 30: return "Performer"
    if days >= 14: return "Solid"
    if days >= 7: return "Testing"
    return "Killed"

def calc_days(start, end):
    try:
        s = datetime.strptime(start, "%Y-%m-%d").date()
        e = datetime.strptime(end or TODAY, "%Y-%m-%d").date()
        return (e - s).days
    except: return None

# === STEP 1: 경쟁사 로드 ===
print("Step 1: 경쟁사 로드 중...")
comp_data = airtable_get(COMPETITORS_TABLE, "filterByFormula={Status}='Active'&fields[]=Name&fields[]=Facebook+Page+ID")
competitors = [(r["fields"]["Name"], r["fields"].get("Facebook Page ID")) for r in comp_data.get("records", []) if r["fields"].get("Facebook Page ID")]
print(f"  {len(competitors)}개 경쟁사: {[c[0] for c in competitors]}")

# === STEP 2: 기존 Archive ID 수집 ===
print("Step 2: 기존 광고 ID 로드 중...")
existing = {}
offset = None
while True:
    params = "fields[]=Ad+Archive+ID&fields[]=Longevity+Tier&fields[]=Days+Active&pageSize=100"
    if offset: params += f"&offset={offset}"
    d = airtable_get(SWIPE_TABLE, params)
    for r in d.get("records", []):
        aid = r["fields"].get("Ad Archive ID")
        if aid: existing[aid] = r["id"]
    offset = d.get("offset")
    if not offset: break
print(f"  기존 광고 {len(existing)}개")

# === STEP 3: 스크래이핑 및 신규 삽입 ===
stats = {}
new_ads = []
errors = []

for name, page_id in competitors:
    print(f"Step 3: {name} 스크래이핑 중...")
    try:
        items = apify_run(page_id)
        new_records = []
        for item in items:
            aid = str(item.get("adArchiveId") or item.get("adArchiveID") or "")
            if not aid or aid in existing: continue
            snap = item.get("snapshot") or {}
            start = parse_date(item.get("startDateFormatted") or item.get("startDate"))
            end   = parse_date(item.get("endDateFormatted") or item.get("endDate"))
            days  = calc_days(start, end) if start else None
            body  = (snap.get("body") or {}).get("text", "") or ""
            fmt   = FORMAT_MAP.get((snap.get("displayFormat") or "IMAGE").upper(), "Image")
            videos = snap.get("videos") or []
            images = snap.get("images") or []
            cards  = snap.get("cards") or []
            video_url = (videos[0].get("videoHdUrl") or videos[0].get("videoSdUrl") or "") if videos else ""
            image_url = (images[0].get("originalImageUrl") or "") if images else ((cards[0].get("originalImageUrl") or "") if cards else "")
            fields = {
                "Ad Archive ID": aid,
                "Competitor": name,
                "Page Name": item.get("pageName", name),
                "Ad Library URL": f"https://www.facebook.com/ads/library/?id={aid}",
                "Status": "Active",
                "Ad Active Status": "Active" if item.get("isActive") else "Inactive",
                "Longevity Tier": longevity_tier(days),
                "Display Format": fmt,
                "Is Analyzed": False,
                "Scrape Date": TODAY,
            }
            if start: fields["Start Date"] = start
            if end:   fields["End Date"] = end
            if days is not None: fields["Days Active"] = days
            if body:  fields["Body Text"] = body[:10000]; fields["Hook Copy"] = body.split("\n")[0][:200]; fields["Word Count"] = len(body.split())
            title = snap.get("title", "")
            if title and "{{" not in title: fields["Title"] = title[:255]
            if snap.get("ctaType"): fields["CTA Type"] = snap["ctaType"]
            if snap.get("linkUrl"): fields["Link URL"] = snap["linkUrl"][:255]
            if video_url: fields["Video URL"] = video_url[:255]
            if image_url: fields["Image URL"] = image_url[:255]
            new_records.append({"fields": fields})
            existing[aid] = None

        inserted = 0
        for i in range(0, len(new_records), 10):
            try:
                r = airtable_post(SWIPE_TABLE, new_records[i:i+10])
                inserted += len(r.get("records", []))
                # Track new ads for report
                for rec in new_records[i:i+10]:
                    new_ads.append((name, rec["fields"].get("Hook Copy",""), rec["fields"].get("Ad Library URL","")))
            except Exception as e:
                errors.append(f"{name} 삽입 오류: {e}")
            time.sleep(0.3)

        stats[name] = {"total": len(items), "new": inserted}
        print(f"  {name}: {len(items)}개 수집, {inserted}개 신규 추가")
    except Exception as e:
        errors.append(f"{name} 스크래이핑 실패: {e}")
        stats[name] = {"total": 0, "new": 0}
        print(f"  {name}: 오류 — {e}")

# === STEP 4: Long-Runner 목록 ===
print("Step 4: Long-Runner 광고 수집 중...")
lr_data = airtable_get(SWIPE_TABLE, "filterByFormula={Longevity+Tier}='Long-Runner'&fields[]=Hook+Copy&fields[]=Ad+Library+URL&fields[]=Competitor&fields[]=Days+Active&pageSize=50")
long_runners = [(r["fields"].get("Competitor",""), r["fields"].get("Hook Copy",""), r["fields"].get("Ad Library URL",""), r["fields"].get("Days Active",0)) for r in lr_data.get("records", [])]
print(f"  Long-Runner {len(long_runners)}개")

# === STEP 5: Gmail 리포트 발송 ===
print("Step 5: Gmail 리포트 발송 중...")

total_new = sum(v["new"] for v in stats.values())

err_section = f"<p style='color:red'>⚠️ 오류: {', '.join(errors)}</p>" if errors else ""

# 국가별 섹션 분리
from collections import defaultdict
stats_by_country = defaultdict(dict)
for name, v in stats.items():
    country = COUNTRY_MAP.get(name, "🌏 글로벌")
    stats_by_country[country][name] = v

country_sections = ""
country_order = ["🇰🇷 한국", "🇯🇵 일본", "🇹🇼 대만", "🌏 글로벌", "🌏 글로벌 (프레임워크)"]
for country in country_order:
    if country not in stats_by_country:
        continue
    rows = "".join(f"<tr><td>{n}</td><td>{v['total']}</td><td><b>{v['new']}</b></td></tr>"
                   for n, v in stats_by_country[country].items())
    country_total = sum(v['new'] for v in stats_by_country[country].values())
    country_sections += f"""
<h3>{country}</h3>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%; margin-bottom:16px;">
  <tr style="background:#f0f0f0"><th>경쟁사</th><th>총 광고</th><th>신규 추가</th></tr>
  {rows}
  <tr style="background:#e8f5e9"><td><b>소계</b></td><td></td><td><b>{country_total}개</b></td></tr>
</table>
"""

lr_rows = "".join(
    f"<tr><td>{COUNTRY_MAP.get(c,'?')}</td><td>{c}</td><td>{d}일</td><td><a href='{u}'>{h[:80]}...</a></td></tr>"
    for c,h,u,d in long_runners[:10] if h
) or "<tr><td colspan='4'>없음</td></tr>"

top5 = "".join(
    f"<li><b>{COUNTRY_MAP.get(c,'?')} {c}</b> — <a href='{u}'>{h[:100]}</a></li>"
    for c,h,u in new_ads[:5]
) or "<li>신규 광고 없음</li>"

html = f"""
<html><body style="font-family: sans-serif; max-width: 720px; margin: auto; padding: 20px;">
<h2 style="color:#1a1a2e; border-bottom: 2px solid #e94560; padding-bottom: 8px;">
  📊 팟노블 광고 인텔리전스 리포트 — {TODAY}
</h2>
<p style="background:#f5f5f5; padding:10px; border-radius:6px;">
  총 신규 광고: <b>{total_new}개</b> &nbsp;|&nbsp;
  Long-Runner: <b>{len(long_runners)}개</b> &nbsp;|&nbsp;
  추적 경쟁사: <b>{len(stats)}개</b>
</p>
{err_section}

<h2 style="color:#1a1a2e; margin-top:24px;">📥 국가별 수집 현황</h2>
{country_sections}

<h2 style="color:#1a1a2e; margin-top:24px;">🏆 Long-Runner 광고 (60일+ 검증)</h2>
<table border="1" cellpadding="6" cellspacing="0" style="border-collapse:collapse; width:100%">
  <tr style="background:#f0f0f0"><th>국가</th><th>경쟁사</th><th>기간</th><th>훅 텍스트</th></tr>
  {lr_rows}
</table>

<h2 style="color:#1a1a2e; margin-top:24px;">🆕 오늘 신규 발견 광고 Top 5</h2>
<ol>{top5}</ol>

<hr>
<p style="color:#888; font-size:12px;">
  이 리포트는 팟노블 Ads Machine이 자동 발송했습니다.<br>
  더 자세한 분석은 /ad-analyzer를 실행하세요.
</p>
</body></html>
"""

msg = MIMEMultipart("alternative")
msg["Subject"] = f"📊 팟노블 광고 인텔리전스 — {TODAY} ({total_new}개 신규)"
msg["From"] = GMAIL_USER
msg["To"] = GMAIL_USER
msg.attach(MIMEText(html, "html"))

with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
    server.login(GMAIL_USER, GMAIL_PASS)
    server.sendmail(GMAIL_USER, GMAIL_USER, msg.as_string())

print(f"✅ 완료! 이메일 발송: {GMAIL_USER}")
print(f"   신규 광고: {total_new}개 | Long-Runner: {len(long_runners)}개")
