#!/usr/bin/env python3
"""
팟노블 Ads Machine — Daily Intelligence Pipeline
Runs: scrape → dedup/insert → tier update → Gmail report
Usage: python3 daily-pipeline.py
"""

import os, sys, json, time, smtplib, traceback
from datetime import date, datetime, timedelta
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from urllib.request import Request, urlopen
from urllib.parse import urlencode, quote
from urllib.error import HTTPError

# ─── Config ──────────────────────────────────────────────────────────────────
AIRTABLE_API_KEY = os.environ["AIRTABLE_API_KEY"]
APIFY_TOKEN      = os.environ["APIFY_TOKEN"]
GMAIL_USER       = os.environ["GMAIL_USER"]
GMAIL_PASSWORD   = os.environ["GMAIL_APP_PASSWORD"]
REPORT_TO        = os.environ.get("REPORT_TO", os.environ["GMAIL_USER"])

BASE_ID           = "appfxyHine1JWPTHA"
COMPETITORS_TABLE = "tblsz0J8E04kzyV1A"
SWIPE_TABLE       = "tblpeuUHtNauLbEwo"
HOOKS_TABLE       = "tbl5YhaQwd4cOHGRJ"

TODAY = date.today()
TODAY_STR = TODAY.strftime("%Y-%m-%d")
TODAY_ISO = TODAY.isoformat()

# ─── Helpers ─────────────────────────────────────────────────────────────────
def airtable_get(table_id, params=None):
    base_url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}"
    records = []
    offset = None
    while True:
        p = dict(params or {})
        if offset:
            p["offset"] = offset
        qs = "&".join(f"{k}={quote(str(v))}" for k, v in p.items()) if p else ""
        url = f"{base_url}?{qs}" if qs else base_url
        req = Request(url, headers={"Authorization": f"Bearer {AIRTABLE_API_KEY}"})
        with urlopen(req, timeout=20) as r:
            data = json.loads(r.read())
        records.extend(data.get("records", []))
        offset = data.get("offset")
        if not offset:
            break
    return records


def airtable_patch_batch(table_id, updates):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}"
    for i in range(0, len(updates), 10):
        chunk = updates[i:i+10]
        payload = json.dumps({"records": chunk}).encode()
        req = Request(url, data=payload, method="PATCH", headers={
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json",
        })
        with urlopen(req, timeout=20) as r:
            r.read()
        if len(updates) > 10:
            time.sleep(0.25)


def airtable_post_batch(table_id, creates):
    url = f"https://api.airtable.com/v0/{BASE_ID}/{table_id}"
    created = 0
    for i in range(0, len(creates), 10):
        chunk = creates[i:i+10]
        payload = json.dumps({"records": chunk}).encode()
        req = Request(url, data=payload, method="POST", headers={
            "Authorization": f"Bearer {AIRTABLE_API_KEY}",
            "Content-Type": "application/json",
        })
        with urlopen(req, timeout=20) as r:
            resp = json.loads(r.read())
        created += len(resp.get("records", []))
        if len(creates) > 10:
            time.sleep(0.25)
    return created


def apify_run_and_wait(page_id, max_wait=300):
    start_url = (
        f"https://api.apify.com/v2/acts/apify~facebook-ads-scraper/runs"
        f"?token={APIFY_TOKEN}"
    )
    body = json.dumps({
        "startUrls": [{"url": (
            "https://www.facebook.com/ads/library/"
            f"?active_status=all&ad_type=all&country=ALL&media_type=all"
            f"&search_type=page&sort_data[direction]=desc"
            f"&sort_data[mode]=total_impressions&view_all_page_id={page_id}"
        )}],
        "resultsLimit": 50,
    }).encode()
    req = Request(start_url, data=body, method="POST",
                  headers={"Content-Type": "application/json"})
    with urlopen(req, timeout=30) as r:
        run = json.loads(r.read())
    run_id = run["data"]["id"]
    print(f"    Apify run {run_id} started …")

    deadline = time.time() + max_wait
    while time.time() < deadline:
        time.sleep(10)
        status_url = (
            f"https://api.apify.com/v2/acts/apify~facebook-ads-scraper"
            f"/runs/{run_id}?token={APIFY_TOKEN}"
        )
        req2 = Request(status_url)
        with urlopen(req2, timeout=15) as r:
            status_data = json.loads(r.read())
        status = status_data["data"]["status"]
        print(f"    … status: {status}")
        if status == "SUCCEEDED":
            dataset_id = status_data["data"]["defaultDatasetId"]
            items_url = (
                f"https://api.apify.com/v2/datasets/{dataset_id}/items"
                f"?token={APIFY_TOKEN}&format=json&clean=true"
            )
            req3 = Request(items_url)
            with urlopen(req3, timeout=30) as r:
                return json.loads(r.read())
        if status in ("FAILED", "ABORTED", "TIMED-OUT"):
            raise RuntimeError(f"Apify run {run_id} ended with status {status}")
    raise TimeoutError(f"Apify run {run_id} timed out after {max_wait}s")


# ─── Longevity Tier logic ─────────────────────────────────────────────────────
def days_active(start_str, end_str=None):
    try:
        start = date.fromisoformat(start_str[:10])
    except Exception:
        return 0
    end = TODAY
    if end_str:
        try:
            end = date.fromisoformat(end_str[:10])
        except Exception:
            pass
    return max(0, (end - start).days)


def longevity_tier(days):
    if days >= 60:  return "Long-Runner"
    if days >= 30:  return "Performer"
    if days >= 14:  return "Solid"
    if days >= 7:   return "Testing"
    return "Killed"


def fmt_display(raw):
    mapping = {"VIDEO": "Video", "IMAGE": "Image", "CAROUSEL": "Carousel", "DCO": "DCO"}
    return mapping.get(str(raw).upper(), raw or "Unknown")


# ─── STEP 1: Load active competitors ─────────────────────────────────────────
def step1_load_competitors():
    print("\n[STEP 1] Loading active competitors …")
    records = airtable_get(COMPETITORS_TABLE, {
        "filterByFormula": "{Status}='Active'",
        "fields[]": ["Name", "Facebook Page ID"],
    })
    competitors = []
    for r in records:
        fields = r.get("fields", {})
        name = fields.get("Name", "Unknown")
        page_id = fields.get("Facebook Page ID", "").strip()
        if page_id:
            competitors.append({"name": name, "page_id": page_id})
            print(f"  ✓ {name} (Page ID: {page_id})")
        else:
            print(f"  ⚠ {name} — no Facebook Page ID, skipping")
    print(f"  → {len(competitors)} competitor(s) to scrape")
    return competitors


# ─── STEP 2: Scrape each competitor ──────────────────────────────────────────
def step2_scrape(competitors):
    print("\n[STEP 2] Scraping competitor ads …")
    results = {}
    errors = []
    for comp in competitors:
        name, page_id = comp["name"], comp["page_id"]
        print(f"\n  → {name} ({page_id})")
        for attempt in range(1, 3):
            try:
                ads = apify_run_and_wait(page_id)
                print(f"    ✓ Got {len(ads)} ads")
                results[name] = ads
                break
            except Exception as e:
                print(f"    Attempt {attempt} failed: {e}")
                if attempt == 2:
                    msg = f"{name}: {e}"
                    errors.append(msg)
                    print(f"    ✗ Skipping {name} after 2 failures")
                else:
                    time.sleep(5)
    return results, errors


# ─── STEP 3: Dedup and insert new ads ────────────────────────────────────────
def step3_insert_new_ads(scrape_results):
    print("\n[STEP 3] Deduplicating and inserting new ads …")

    existing_records = airtable_get(SWIPE_TABLE, {"fields[]": ["Ad Archive ID"]})
    existing_ids = set()
    for r in existing_records:
        aid = r.get("fields", {}).get("Ad Archive ID", "")
        if aid:
            existing_ids.add(str(aid))
    print(f"  Existing archive IDs in Swipe File: {len(existing_ids)}")

    new_ads_inserted = 0
    new_ads_by_competitor = {}
    all_new_ads = []

    for comp_name, ads in scrape_results.items():
        inserts = []
        for ad in ads:
            archive_id = str(ad.get("adArchiveId", "") or "")
            if not archive_id or archive_id in existing_ids:
                continue

            existing_ids.add(archive_id)

            snap = ad.get("snapshot", {}) or {}
            body_text = ""
            bodies = snap.get("body", {}) or {}
            if isinstance(bodies, dict):
                body_text = bodies.get("text", "") or ""
            elif isinstance(bodies, list) and bodies:
                body_text = bodies[0].get("text", "") or ""

            videos = snap.get("videos", []) or []
            images = snap.get("images", []) or []
            video_url = videos[0].get("videoHdUrl", "") if videos else ""
            image_url = images[0].get("originalImageUrl", "") if images else ""

            start_str = ad.get("startDateFormatted", "") or ""
            end_str   = ad.get("endDateFormatted", "") or ""
            d_active  = days_active(start_str, end_str)
            tier      = longevity_tier(d_active)
            display   = fmt_display(snap.get("displayFormat", ""))

            is_active = bool(ad.get("isActive", False))
            status    = "Active" if is_active else "Killed"

            fields = {
                "Ad Archive ID":  archive_id,
                "Competitor":     comp_name,
                "Status":         status,
                "Is Active":      is_active,
                "Start Date":     start_str[:10] if start_str else None,
                "Days Active":    d_active,
                "Longevity Tier": tier,
                "Display Format": display,
                "Body Copy":      body_text[:5000] if body_text else "",
            }
            if end_str:
                fields["End Date"] = end_str[:10]
            if video_url:
                fields["Video URL"] = video_url
            if image_url:
                fields["Image URL"] = image_url

            fields = {k: v for k, v in fields.items() if v is not None}
            inserts.append({"fields": fields})
            all_new_ads.append(fields)

        if inserts:
            count = airtable_post_batch(SWIPE_TABLE, inserts)
            new_ads_inserted += count
            new_ads_by_competitor[comp_name] = count
            print(f"  ✓ {comp_name}: inserted {count} new ads")
        else:
            new_ads_by_competitor[comp_name] = 0
            print(f"  — {comp_name}: no new ads")

    print(f"\n  Total new ads inserted: {new_ads_inserted}")
    return new_ads_inserted, new_ads_by_competitor, all_new_ads


# ─── STEP 4: Update longevity tiers ──────────────────────────────────────────
def step4_update_tiers():
    print("\n[STEP 4] Updating longevity tiers for existing active ads …")
    records = airtable_get(SWIPE_TABLE, {
        "filterByFormula": "{Status}='Active'",
        "fields[]": ["Ad Archive ID", "Start Date", "End Date", "Days Active", "Longevity Tier"],
    })
    updates = []
    for r in records:
        f = r.get("fields", {})
        start_str = f.get("Start Date", "")
        end_str   = f.get("End Date", "")
        d_active  = days_active(start_str, end_str)
        tier      = longevity_tier(d_active)
        if f.get("Days Active") != d_active or f.get("Longevity Tier") != tier:
            updates.append({
                "id": r["id"],
                "fields": {"Days Active": d_active, "Longevity Tier": tier},
            })
    if updates:
        airtable_patch_batch(SWIPE_TABLE, updates)
        print(f"  ✓ Updated {len(updates)} records")
    else:
        print("  — No tier changes needed")
    return len(updates)


# ─── STEP 5: Send Gmail report ────────────────────────────────────────────────
def step5_send_report(competitors, scrape_errors, new_count, new_by_comp, new_ads_list, tier_updates):
    print("\n[STEP 5] Building and sending Gmail report …")

    try:
        all_records = airtable_get(SWIPE_TABLE, {
            "fields[]": ["Longevity Tier", "Body Copy", "Ad Archive ID", "Competitor", "Start Date"],
        })
    except Exception as e:
        all_records = []
        print(f"  ⚠ Could not fetch Swipe File for summary: {e}")

    tier_counts = {}
    long_runners = []
    for r in all_records:
        f = r.get("fields", {})
        tier = f.get("Longevity Tier", "Unknown")
        tier_counts[tier] = tier_counts.get(tier, 0) + 1
        if tier == "Long-Runner":
            long_runners.append(f)

    comp_rows = ""
    for comp in competitors:
        n = new_by_comp.get(comp["name"], 0)
        comp_rows += f"<tr><td>{comp['name']}</td><td style='text-align:center'>{n}</td></tr>\n"
    if not comp_rows:
        comp_rows = "<tr><td colspan='2' style='text-align:center'>경쟁사 없음</td></tr>"

    lr_rows = ""
    for ad in long_runners[:20]:
        archive_id = ad.get("Ad Archive ID", "")
        hook = (ad.get("Body Copy", "") or "")[:120].replace("<","&lt;").replace(">","&gt;")
        comp = ad.get("Competitor", "")
        lib_url = f"https://www.facebook.com/ads/library/?id={archive_id}" if archive_id else "#"
        lr_rows += (
            f"<tr>"
            f"<td>{comp}</td>"
            f"<td style='max-width:400px'>{hook}{'…' if len(ad.get('Body Copy',''))>120 else ''}</td>"
            f"<td><a href='{lib_url}' target='_blank'>보기↗</a></td>"
            f"</tr>\n"
        )
    if not lr_rows:
        lr_rows = "<tr><td colspan='3' style='text-align:center'>Long-Runner 광고 없음</td></tr>"

    new5_rows = ""
    for ad in new_ads_list[:5]:
        hook = (ad.get("Body Copy", "") or "")[:150].replace("<","&lt;").replace(">","&gt;")
        comp = ad.get("Competitor", "")
        tier = ad.get("Longevity Tier", "")
        new5_rows += (
            f"<tr>"
            f"<td>{comp}</td>"
            f"<td style='max-width:420px'>{hook}{'…' if len(ad.get('Body Copy',''))>150 else ''}</td>"
            f"<td>{tier}</td>"
            f"</tr>\n"
        )
    if not new5_rows:
        new5_rows = "<tr><td colspan='3' style='text-align:center'>신규 광고 없음</td></tr>"

    tier_order = ["Long-Runner","Performer","Solid","Testing","Killed","Unknown"]
    tier_rows = ""
    for t in tier_order:
        c = tier_counts.get(t, 0)
        if c:
            bar_w = min(200, c * 4)
            tier_rows += (
                f"<tr><td>{t}</td><td>{c}</td>"
                f"<td><div style='background:#4A90D9;height:14px;width:{bar_w}px;border-radius:3px'></div></td></tr>\n"
            )

    error_section = ""
    if scrape_errors:
        errs = "".join(f"<li>{e}</li>" for e in scrape_errors)
        error_section = f"""
        <h3 style='color:#c0392b'>⚠️ 수집 오류</h3>
        <ul style='color:#c0392b'>{errs}</ul>"""

    html = f"""
<!DOCTYPE html>
<html lang="ko">
<head><meta charset="UTF-8">
<style>
  body {{ font-family: 'Apple SD Gothic Neo', 'Malgun Gothic', sans-serif; background:#f9f9f9; padding:20px; color:#333; }}
  .card {{ background:#fff; border-radius:8px; padding:20px 24px; margin-bottom:20px; box-shadow:0 1px 4px rgba(0,0,0,.08); }}
  h2 {{ color:#1a1a2e; border-bottom:2px solid #4A90D9; padding-bottom:8px; }}
  h3 {{ color:#2c3e50; margin-top:0; }}
  table {{ border-collapse:collapse; width:100%; font-size:14px; }}
  th {{ background:#4A90D9; color:#fff; padding:8px 12px; text-align:left; }}
  td {{ border-bottom:1px solid #eee; padding:8px 12px; vertical-align:top; }}
  tr:last-child td {{ border-bottom:none; }}
  .stat-box {{ display:inline-block; background:#f0f4ff; border-radius:6px; padding:14px 20px; margin:6px; text-align:center; }}
  .stat-num {{ font-size:28px; font-weight:700; color:#4A90D9; }}
  .stat-lbl {{ font-size:12px; color:#666; }}
  .footer {{ font-size:12px; color:#999; text-align:center; margin-top:20px; }}
</style>
</head>
<body>
<div class="card">
  <h2>팟노블 Ads Machine 일일 리포트</h2>
  <p style='color:#666;margin-top:-8px'>{TODAY_STR} · 자동 생성</p>
  <div>
    <div class="stat-box"><div class="stat-num">{new_count}</div><div class="stat-lbl">신규 광고</div></div>
    <div class="stat-box"><div class="stat-num">{len(long_runners)}</div><div class="stat-lbl">Long-Runner (60d+)</div></div>
    <div class="stat-box"><div class="stat-num">{len(all_records)}</div><div class="stat-lbl">총 스와이프 파일</div></div>
    <div class="stat-box"><div class="stat-num">{tier_updates}</div><div class="stat-lbl">티어 업데이트</div></div>
  </div>
  {error_section}
</div>
<div class="card">
  <h3>경쟁사별 신규 광고</h3>
  <table><tr><th>경쟁사</th><th>신규 광고 수</th></tr>{comp_rows}</table>
</div>
<div class="card">
  <h3>🏆 Long-Runner 광고 목록 (60일+)</h3>
  <table><tr><th>경쟁사</th><th>후크 카피</th><th>링크</th></tr>{lr_rows}</table>
</div>
<div class="card">
  <h3>✨ 오늘 새로 발견된 광고 TOP 5</h3>
  <table><tr><th>경쟁사</th><th>광고 카피</th><th>Longevity 티어</th></tr>{new5_rows}</table>
</div>
<div class="card">
  <h3>Longevity 티어 분포</h3>
  <table><tr><th>티어</th><th>광고 수</th><th>분포</th></tr>{tier_rows if tier_rows else "<tr><td colspan='3'>데이터 없음</td></tr>"}</table>
</div>
<div class="footer">
  분석 더 보려면 /ad-analyzer를 실행하세요 | 팟노블 Ads Machine · {TODAY_STR}
</div>
</body></html>
"""

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"팟노블 광고 인텔리전스 리포트 — {TODAY_STR}"
    msg["From"]    = GMAIL_USER
    msg["To"]      = REPORT_TO
    msg.attach(MIMEText(html, "html"))

    with smtplib.SMTP_SSL("smtp.gmail.com", 465, timeout=30) as server:
        server.login(GMAIL_USER, GMAIL_PASSWORD)
        server.sendmail(GMAIL_USER, REPORT_TO, msg.as_string())

    print(f"  ✓ 이메일 발송 완료 → {REPORT_TO}")


# ─── Main ─────────────────────────────────────────────────────────────────────
def main():
    print("=" * 60)
    print(f"팟노블 Ads Machine — Daily Pipeline  [{TODAY_STR}]")
    print("=" * 60)

    scrape_errors = []
    new_count = 0
    new_by_comp = {}
    new_ads_list = []
    tier_updates = 0
    competitors = []

    try:
        competitors = step1_load_competitors()
    except Exception as e:
        print(f"[STEP 1 ERROR] {e}")
        traceback.print_exc()
        scrape_errors.append(f"Step 1 (경쟁사 로드): {e}")

    scrape_results = {}
    if competitors:
        try:
            scrape_results, step2_errors = step2_scrape(competitors)
            scrape_errors.extend(step2_errors)
        except Exception as e:
            print(f"[STEP 2 ERROR] {e}")
            traceback.print_exc()
            scrape_errors.append(f"Step 2 (스크래핑): {e}")

    if scrape_results:
        try:
            new_count, new_by_comp, new_ads_list = step3_insert_new_ads(scrape_results)
        except Exception as e:
            print(f"[STEP 3 ERROR] {e}")
            traceback.print_exc()
            scrape_errors.append(f"Step 3 (신규 광고 삽입): {e}")

    try:
        tier_updates = step4_update_tiers()
    except Exception as e:
        print(f"[STEP 4 ERROR] {e}")
        traceback.print_exc()
        scrape_errors.append(f"Step 4 (티어 업데이트): {e}")

    try:
        step5_send_report(competitors, scrape_errors, new_count, new_by_comp, new_ads_list, tier_updates)
    except Exception as e:
        print(f"[STEP 5 ERROR] 이메일 발송 실패: {e}")
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("Pipeline complete.")
    print("=" * 60)


if __name__ == "__main__":
    main()
