from PIL import Image, ImageDraw, ImageFont
import math
import random

random.seed(42)

W, H = 1800, 1100
img = Image.new("RGB", (W, H), "#FAF6EF")
draw = ImageDraw.Draw(img)

def font(size):
    try: return ImageFont.truetype("arial.ttf", size)
    except: return ImageFont.load_default()

def font_bold(size):
    try: return ImageFont.truetype("arialbd.ttf", size)
    except: return font(size)

# Sketchy rounded rectangle
def sketch_rect(x, y, w, h, fill, outline, lw=2):
    r = 12
    draw.rounded_rectangle([x, y, x+w, y+h], radius=r, fill=fill, outline=outline, width=lw)

# Arrow
def arrow(x1, y1, x2, y2, color="#495057", lw=2):
    draw.line([(x1,y1),(x2,y2)], fill=color, width=lw)
    angle = math.atan2(y2-y1, x2-x1)
    al = 10
    draw.polygon([
        (x2, y2),
        (x2 - al*math.cos(angle-0.4), y2 - al*math.sin(angle-0.4)),
        (x2 - al*math.cos(angle+0.4), y2 - al*math.sin(angle+0.4))
    ], fill=color)

# L-shaped arrow
def arrow_L(x1, y1, mx, my, x2, y2, color="#495057", lw=2):
    draw.line([(x1,y1),(mx,my)], fill=color, width=lw)
    draw.line([(mx,my),(x2,y2)], fill=color, width=lw)
    angle = math.atan2(y2-my, x2-mx)
    al = 10
    draw.polygon([
        (x2, y2),
        (x2 - al*math.cos(angle-0.4), y2 - al*math.sin(angle-0.4)),
        (x2 - al*math.cos(angle+0.4), y2 - al*math.sin(angle+0.4))
    ], fill=color)

# ── TITLE ──
draw.text((W//2, 35), "THE ADS MACHINE", fill="#1e1e1e", font=font_bold(42), anchor="mt")
draw.text((W//2, 80), "Closed-Loop Ad Intelligence System  —  Built in Claude Code", fill="#868e96", font=font(16), anchor="mt")

# ── ROW 1: COMPETITORS ──
sketch_rect(60, 130, 280, 130, "#d0ebff", "#1971c2")
draw.text((200, 142), "YOUR COMPETITORS", fill="#1971c2", font=font_bold(17), anchor="mt")
draw.text((80, 170), "Direct competitors", fill="#495057", font=font(14))
draw.text((80, 190), "Aspirational (Hormozi etc)", fill="#495057", font=font(14))
draw.text((80, 210), "Auto Page ID resolve", fill="#495057", font=font(14))
draw.text((80, 230), "Meta Ad Library", fill="#495057", font=font(14))

# ── ROW 2: POLLER → ANALYZER → SWIPE ──
# Poller
sketch_rect(60, 310, 280, 140, "#fff3bf", "#e67700")
draw.text((200, 322), "DAILY AD POLLER", fill="#e67700", font=font_bold(17), anchor="mt")
draw.text((80, 350), "Apify + Ad Library", fill="#495057", font=font(14))
draw.text((80, 370), "Active + inactive ads", fill="#495057", font=font(14))
draw.text((80, 390), "Dedup against existing", fill="#495057", font=font(14))
draw.text((80, 410), "Days Active grading", fill="#495057", font=font(14))
draw.text((80, 430), "n8n daily cron", fill="#868e96", font=font(12))

# Analyzer
sketch_rect(420, 310, 280, 140, "#f3d9fa", "#862e9c")
draw.text((560, 322), "ANALYSIS ENGINE", fill="#862e9c", font=font_bold(17), anchor="mt")
draw.text((440, 350), "Whisper transcribe", fill="#495057", font=font(14))
draw.text((440, 370), "Claude extract hooks", fill="#495057", font=font(14))
draw.text((440, 390), "Classify angle + format", fill="#495057", font=font(14))
draw.text((440, 410), "Gemini visual analysis", fill="#495057", font=font(14))
draw.text((440, 430), "Feed proven hooks DB", fill="#495057", font=font(14))

# Swipe File (bigger)
sketch_rect(780, 280, 300, 200, "#d8f5a2", "#2f9e44", lw=3)
draw.text((930, 292), "AD SWIPE FILE", fill="#2f9e44", font=font_bold(20), anchor="mt")
draw.text((800, 320), "Winning ad hooks", fill="#495057", font=font(14))
draw.text((800, 340), "Angles and frameworks", fill="#495057", font=font(14))
draw.text((800, 360), "CTAs and copy patterns", fill="#495057", font=font(14))
draw.text((800, 380), "Visual styles and formats", fill="#495057", font=font(14))
draw.text((800, 400), "Proven Hooks database", fill="#495057", font=font(14))
draw.text((800, 420), "Days Active grading", fill="#495057", font=font(14))
draw.text((800, 450), "Grows every single day", fill="#c92a2a", font=font_bold(14))

# Tags
draw.text((200, 460), "Apify", fill="#862e9c", font=font(12), anchor="mt")
draw.text((560, 460), "Whisper + Claude + Gemini", fill="#862e9c", font=font(12), anchor="mt")
draw.text((930, 488), "Airtable", fill="#2f9e44", font=font(12), anchor="mt")

# ── ROW 3: IDEATOR → SCRIPTER → BRIEF → LAUNCH ──
bw, bh = 200, 120
row3_y = 550

sketch_rect(60, row3_y, bw, bh, "#ffe3e3", "#c92a2a")
draw.text((160, row3_y+12), "AD IDEATOR", fill="#c92a2a", font=font_bold(16), anchor="mt")
draw.text((75, row3_y+38), "1 winner = 5 variations", fill="#495057", font=font(13))
draw.text((75, row3_y+58), "Batch: 10h x 3b x 2c", fill="#495057", font=font(13))
draw.text((75, row3_y+78), "= 60 ads from 5 clips", fill="#495057", font=font(13))

sketch_rect(310, row3_y, bw, bh, "#d0ebff", "#1971c2")
draw.text((410, row3_y+12), "AD SCRIPTER", fill="#1971c2", font=font_bold(16), anchor="mt")
draw.text((325, row3_y+38), "Video script + ad copy", fill="#495057", font=font(13))
draw.text((325, row3_y+58), "PAS / AIDA / Story", fill="#495057", font=font(13))
draw.text((325, row3_y+78), "Proven hook frameworks", fill="#495057", font=font(13))

sketch_rect(560, row3_y, bw, bh, "#fff3bf", "#e67700")
draw.text((660, row3_y+12), "CREATIVE BRIEF", fill="#e67700", font=font_bold(16), anchor="mt")
draw.text((575, row3_y+38), "Shot list + filming card", fill="#495057", font=font(13))
draw.text((575, row3_y+58), "Image generation", fill="#495057", font=font(13))
draw.text((575, row3_y+78), "Text overlay specs", fill="#495057", font=font(13))

sketch_rect(810, row3_y, bw, bh, "#ffe3e3", "#c92a2a")
draw.text((910, row3_y+12), "LAUNCH", fill="#c92a2a", font=font_bold(16), anchor="mt")
draw.text((825, row3_y+38), "Meta API via MCP", fill="#495057", font=font(13))
draw.text((825, row3_y+58), "Campaign + Ad Set", fill="#495057", font=font(13))
draw.text((825, row3_y+78), "Creative + Ad", fill="#495057", font=font(13))
draw.text((910, row3_y+105), "Meta Graph API", fill="#c92a2a", font=font(11), anchor="mt")

# ── ROW 4: MONITOR + LOOP ──
sketch_rect(400, 740, 300, 130, "#d8f5a2", "#2f9e44")
draw.text((550, 752), "PERFORMANCE MONITOR", fill="#2f9e44", font=font_bold(16), anchor="mt")
draw.text((420, 780), "KILL  /  WATCH  /  SCALE", fill="#1e1e1e", font=font_bold(14))
draw.text((420, 805), "CPL, CTR, CPM, ROAS", fill="#495057", font=font(13))
draw.text((420, 825), "Weekly performance insights", fill="#495057", font=font(13))
draw.text((420, 845), "Winners feed back to swipe file", fill="#495057", font=font(13))

sketch_rect(780, 760, 220, 90, "#c3fae8", "#0c8599", lw=3)
draw.text((890, 780), "THE LOOP", fill="#0c8599", font=font_bold(22), anchor="mt")
draw.text((890, 815), "Winners feed back in", fill="#0c8599", font=font(14), anchor="mt")

# ── HORMOZI CALLOUT ──
sketch_rect(1150, 130, 280, 110, "#fff5f5", "#c92a2a")
draw.text((1290, 148), "HORMOZI", fill="#c92a2a", font=font_bold(18), anchor="mt")
draw.text((1290, 180), "his $100M ads are in", fill="#495057", font=font(14), anchor="mt")
draw.text((1290, 200), "your swipe file now", fill="#c92a2a", font=font_bold(14), anchor="mt")

# ── GRADING BOX ──
sketch_rect(1150, 300, 280, 160, "#f8f9fa", "#868e96")
draw.text((1290, 312), "GRADING", fill="#1e1e1e", font=font_bold(16), anchor="mt")
draw.text((1170, 340), "60d+  Long-Runner", fill="#2f9e44", font=font_bold(14))
draw.text((1170, 362), "30d+  Performer", fill="#1971c2", font=font_bold(14))
draw.text((1170, 384), "14d+  Solid", fill="#0c8599", font=font(14))
draw.text((1170, 406), "7d+   Testing", fill="#e67700", font=font(14))
draw.text((1170, 428), "<7d   Killed", fill="#c92a2a", font=font(14))

# ── ARROWS ──
# Competitors -> Poller
arrow(200, 260, 200, 305)
# Poller -> Analyzer
arrow(345, 380, 415, 380)
# Analyzer -> Swipe
arrow(705, 380, 775, 380)
# Swipe -> Ideator (down and left)
arrow_L(780, 480, 160, 480, 160, 545)
# Ideator -> Scripter
arrow(265, 610, 305, 610)
# Scripter -> Brief
arrow(515, 610, 555, 610)
# Brief -> Launch
arrow(765, 610, 805, 610)
# Launch -> Monitor
arrow_L(910, 675, 910, 800, 705, 800)
# Monitor -> Loop
arrow(705, 800, 775, 800)

# Loop -> Swipe (dashed feedback loop)
for i in range(0, 200, 8):
    x = 1005
    y1 = 800 - i*2
    if y1 < 380:
        break
    draw.line([(x, y1), (x, y1-4)], fill="#0c8599", width=2)

# Final arrow from loop line to swipe
arrow(1005, 380, 1085, 380)
draw.text((1040, 500), "THE", fill="#0c8599", font=font_bold(12), anchor="mt")
draw.text((1040, 516), "LOOP", fill="#0c8599", font=font_bold(12), anchor="mt")

# ── 11 SKILLS BADGE ──
sketch_rect(1150, 510, 280, 60, "#d0ebff", "#1971c2")
draw.text((1290, 528), "11 Skills  ·  13 References", fill="#1971c2", font=font_bold(14), anchor="mt")
draw.text((1290, 550), "n8n Automation  ·  4 Airtable Tables", fill="#1971c2", font=font(12), anchor="mt")

# ── SAVE ──
out = "C:/Users/me/amber-ai/ads-machine/docs/blueprint.png"
img.save(out, "PNG", quality=95)
print(f"Saved to {out}")
print(f"Size: {W}x{H}")
