# 팟노블 — Ads Machine

## Business
| Field | Value |
|-------|-------|
| Business | 팟노블 (스푼라디오) |
| Website | https://www.spooncast.net/kr/pod-novel |
| Niche | AI 낭독 오디오 웹소설 (막장·재벌·복수·사이다 장르) |
| Offer | 코인 충전 → 작품 구매 |
| Price Point | 작품당 1~2스푼 (100~200원) |

## Target Audience
| Field | Value |
|-------|-------|
| Age Range | 40~60대 |
| Gender | 여성 |
| Location | 한국 전체 (신규 타겟: 일본, 대만) |
| Pain Point | 지루한 일상 탈출 / 대중교통에서 자극적 콘텐츠를 프라이빗하게 즐기기 |
| Desired Outcome | 재미 + 즉각적인 감정 자극 (도파민) |

## Ad Research Config
| Field | Value |
|-------|-------|
| Airtable Base ID | appfxyHine1JWPTHA |
| Competitors Table | tblsz0J8E04kzyV1A |
| Ad Swipe File Table | tblpeuUHtNauLbEwo |
| Proven Hooks Table | tbl5YhaQwd4cOHGRJ |
| Ad Pipeline Table | tblIOkzWqLMfM6ir9 |

### Niche Tiers
| Tier | Competitors |
|------|-------------|
| Direct | 자동 탐색 예정 (오디오 웹소설 니치) |
| Adjacent | — |
| Aspirational | Alex Hormozi (116482854782233), Pocket FM |

## Meta Ads Config
| Field | Value |
|-------|-------|
| Ad Account ID | (추후 입력 — .env의 META_AD_ACCOUNT_ID 참고) |
| Page ID | (추후 입력) |
| Pixel ID | (추후 입력) |

## KPI Targets
| KPI | Target |
|-----|--------|
| Target CPL | (추후 입력) |
| Target ROAS | 3.0 |
| Target CPA | (추후 입력) |
| Monthly Budget | (추후 입력) |

## Alerts
| Channel | Config |
|---------|--------|
| Gmail | remi@spoonlabs.com (GMAIL_USER / GMAIL_APP_PASSWORD in .env) |

## Installed Skills
| Command | What It Does |
|---------|-------------|
| `/ads-setup` | 일회성 설치 마법사 |
| `/ad-poller` | Meta Ad Library에서 경쟁사 광고 스크래이핑 |
| `/ad-analyzer` | 광고 전사·분류·점수 분석 |
| `/ad-swipe` | 스와이프 파일 검색 및 탐색 |
| `/ad-ideator` | 우승 광고 1개 → 5개 변형 생성 |
| `/ad-scripter` | 영상 스크립트 및 광고 카피 작성 |
| `/ad-brief` | 촬영 카드 및 샷 리스트 생성 |
| `/ad-launch` | Meta 캠페인 API 론칭 |
| `/ad-monitor` | 성과 추적, 킬/워치/스케일 판정 |

## Connected Tools
| Tool | Status |
|------|--------|
| Airtable MCP | Connected |
| Apify MCP | Connected |
| Meta Ads MCP | Connected (.env에 키 있음) |
| Slack MCP | Not configured |
| Gmail | Connected (remi@spoonlabs.com) |
| n8n MCP | Optional — not connected |

## Campaign Structure
- Post-Andromeda: 1 campaign, 1 ad set, 10-50 ads
- Advantage Plus targeting — algorithm handles audiences
- Budget at ad set level (ABO for testing, CBO for scaling)
- All ads launch PAUSED until explicit confirmation

## Naming Convention
All creatives follow: `[ClientCode]_[CampaignType]_[Angle]_[Format]_[v#]`
Example: `PN_Growth_PainPoint_Video_v1`

## Reference Files
All reference material lives in `reference/` — read before writing copy or making decisions:
- `campaign-setup.md` — Post-Andromeda campaign architecture
- `creative-strategy.md` — Hook rates, script formula, ad formats
- `kpi-benchmarks.md` — Benchmarks and kill/watch/scale decision rules
- `ad-frameworks.md` — PAS, AIDA, Story, Before/After, Controversy
- `hook-swipe-file.md` — Proven ad hooks (grows via the loop)
- `copy-patterns.md` — Primary text, headline, and CTA patterns
- `visual-styles.md` — UGC, talking head, motion graphics specs
- `troubleshooting.md` — Lead gen matrix and CRO checklist
- `pixel-tracking.md` — CAPI setup and event filtering
- `retargeting.md` — Retargeting strategy framework
