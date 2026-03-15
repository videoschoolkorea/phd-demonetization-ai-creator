#!/usr/bin/env python3
"""
YouTube Demonetization 연구 — 통합 데이터 수집기 v2
====================================================
수집 전략:
  1. YouTube Data API (공개 채널 메타데이터) ← 이미 성공
  2. Pushshift/PullPush API (Reddit 넷노그라피) ← 대안
  3. Kaggle/GitHub 공개 데이터셋 활용 안내 생성
  4. YouTube 검색 결과 기반 AI 채널 목록 보강

연구자: 김재환 (중앙대학교 첨단영상대학원)
"""

import requests, json, time, csv, os, random
from datetime import datetime
from pathlib import Path

OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8",
}
DELAY = (1.5, 3.0)

ALL_CHANNELS = [
    {"id": "UCddiUEpeqJcYeBxX1IVBKvQ", "name": "BRIGHT SIDE",        "type": "AI",          "country": "INT"},
    {"id": "UC9-y-6csu5WGm29I7JiwpnA", "name": "Computerphile",       "type": "AI",          "country": "UK"},
    {"id": "UCbmNph6atAoGfqLoCL_duAg", "name": "Kurzgesagt",          "type": "AI",          "country": "DE"},
    {"id": "UC4JX40jDee_tINbkjycV4Sg", "name": "Tech With Tim",       "type": "AI",          "country": "US"},
    {"id": "UCWX3yGbODI3HLNnFCNfQigA", "name": "AI Explained",        "type": "AI",          "country": "US"},
    {"id": "UCnUYZLuoy1rq1aVMwx4aTzw", "name": "두두팝DUDUPOP",       "type": "AI",          "country": "KR"},
    {"id": "UCOLdTjPQIWVyCKmPuHPP4kA", "name": "체리의 과학",         "type": "AI",          "country": "KR"},
    {"id": "UCEBcDOjv-bhAmLavMTrMdZQ", "name": "Joma Tech",           "type": "AI",          "country": "US"},
    {"id": "UCXuqSBlHAE6Xw-yeJA0Tunw", "name": "Linus Tech Tips",     "type": "Traditional", "country": "CA"},
    {"id": "UCBcRF18a7Qf58cCRy5xuWwQ", "name": "MrBeast",             "type": "Traditional", "country": "US"},
    {"id": "UC295-Dw4tzbADgNButmlKiA", "name": "MKBHD",               "type": "Traditional", "country": "US"},
    {"id": "UCupvZG-5ko_eiXAupbDfxWw", "name": "CNN",                 "type": "Traditional", "country": "US"},
    {"id": "UCaXkIU1QidjPwiAYu6GcHjg", "name": "JTBC News",          "type": "Traditional", "country": "KR"},
    {"id": "UCQMBxjbngN7lHIBg_BLBeCg", "name": "KBS News",           "type": "Traditional", "country": "KR"},
    {"id": "UCuVHo2rodCFBMlwNtkfpfzA", "name": "SBS News",           "type": "Traditional", "country": "KR"},
    {"id": "UCgeFcHbdqpOEqTAhgdmB_0g", "name": "조승연의 탐구생활",   "type": "Traditional", "country": "KR"},
]


# ─────────────────────────────────────────
# 1. YouTube 공개 채널 메타데이터
# ─────────────────────────────────────────
def fetch_youtube_public(channel_id: str) -> dict:
    url = f"https://www.youtube.com/channel/{channel_id}"
    try:
        time.sleep(random.uniform(*DELAY))
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        text = resp.text

        marker = "var ytInitialData = "
        start = text.find(marker)
        if start == -1:
            return {"channel_id": channel_id, "status": "no_ytInitialData"}
        start += len(marker)
        depth = end = 0
        for i, ch in enumerate(text[start:], start):
            if ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0: end = i + 1; break

        data = json.loads(text[start:end])
        header = data.get("header", {}).get("c4TabbedHeaderRenderer", {})
        meta   = data.get("metadata", {}).get("channelMetadataRenderer", {})

        # 구독자 수 (헤더 텍스트에서 추출)
        sub_text = ""
        sub_info = header.get("subscriberCountText", {})
        if isinstance(sub_info, dict):
            runs = sub_info.get("runs", sub_info.get("simpleText", ""))
            if isinstance(runs, list) and runs:
                sub_text = runs[0].get("text", "")
            elif isinstance(runs, str):
                sub_text = runs

        return {
            "channel_id":    channel_id,
            "title":         header.get("title", ""),
            "subscribers":   sub_text,
            "description":   meta.get("description", "")[:300],
            "keywords":      meta.get("keywords", "")[:200],
            "canonical_url": meta.get("canonicalUrl", ""),
            "collected_at":  datetime.now().isoformat(),
            "status":        "ok",
        }
    except Exception as e:
        return {"channel_id": channel_id, "status": f"error:{e}"}


# ─────────────────────────────────────────
# 2. PullPush API (Reddit 대안)
# ─────────────────────────────────────────
def fetch_reddit_pullpush(queries: list, size: int = 30) -> list:
    """PullPush.io API로 Reddit 게시물 수집 (공개 API, 인증 불필요)"""
    base = "https://api.pullpush.io/reddit/search/submission/"
    headers = {"User-Agent": "academic-research/1.0 PhD YouTube demonetization study"}
    
    results = []
    seen = set()
    
    for subreddit, query in queries:
        params = {
            "subreddit": subreddit,
            "q":         query,
            "size":      size,
            "sort":      "desc",
        }
        try:
            time.sleep(random.uniform(1.0, 2.0))
            resp = requests.get(base, params=params, headers=headers, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            posts = data.get("data", [])
            
            for p in posts:
                pid = p.get("id", "")
                if pid in seen: continue
                seen.add(pid)
                
                # 개인정보 보호: author 익명처리
                results.append({
                    "id":           pid,
                    "subreddit":    subreddit,
                    "query":        query,
                    "title":        p.get("title", ""),
                    "score":        p.get("score", 0),
                    "num_comments": p.get("num_comments", 0),
                    "created_utc":  datetime.fromtimestamp(p.get("created_utc", 0)).isoformat(),
                    "url":          f"https://reddit.com{p.get('permalink', '')}",
                    "selftext":     p.get("selftext", "")[:600],
                    "flair":        p.get("link_flair_text", ""),
                    "author":       "[익명처리]",  # 개인정보 보호
                })
            print(f"    r/{subreddit} '{query}': {len(posts)}건")
        except Exception as e:
            print(f"    r/{subreddit} '{query}': 오류 — {e}")
    
    return results


# ─────────────────────────────────────────
# 3. YouTube 검색 API로 AI 채널 추가 수집
# ─────────────────────────────────────────
def fetch_youtube_search_meta(keywords: list) -> list:
    """YouTube 검색 결과 페이지에서 채널 정보 파악"""
    results = []
    for kw in keywords:
        url = f"https://www.youtube.com/results"
        params = {"search_query": kw, "sp": "EgIQAg=="}  # 채널 필터
        try:
            time.sleep(random.uniform(*DELAY))
            resp = requests.get(url, params=params, headers=HEADERS, timeout=15)
            text = resp.text
            # ytInitialData에서 채널 검색 결과 추출
            marker = "var ytInitialData = "
            start = text.find(marker)
            if start == -1: continue
            start += len(marker)
            depth = end = 0
            for i, ch in enumerate(text[start:], start):
                if ch == '{': depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0: end = i + 1; break
            data = json.loads(text[start:end])
            
            # 채널 카드 추출
            contents = data.get("contents", {})
            section = contents.get("twoColumnSearchResultsRenderer", {})
            primary = section.get("primaryContents", {})
            renders = primary.get("sectionListRenderer", {}).get("contents", [])
            
            for sec in renders:
                items = sec.get("itemSectionRenderer", {}).get("contents", [])
                for item in items:
                    ch_data = item.get("channelRenderer", {})
                    if not ch_data: continue
                    ch_id = ch_data.get("channelId", "")
                    ch_title = ch_data.get("title", {}).get("simpleText", "")
                    sub_count = ch_data.get("videoCountText", {}).get("runs", [{}])
                    sub_count = sub_count[0].get("text", "") if sub_count else ""
                    
                    results.append({
                        "keyword":      kw,
                        "channel_id":   ch_id,
                        "channel_name": ch_title,
                        "sub_count":    sub_count,
                        "collected_at": datetime.now().isoformat(),
                    })
        except Exception as e:
            print(f"    검색 '{kw}': 오류 — {e}")
    return results


# ─────────────────────────────────────────
# 저장
# ─────────────────────────────────────────
def save_json_csv(data: list, name: str):
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    jp = OUTPUT_DIR / f"{name}_{ts}.json"
    cp = OUTPUT_DIR / f"{name}_{ts}.csv"
    with open(jp, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    if data:
        with open(cp, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=data[0].keys())
            writer.writeheader(); writer.writerows(data)
    return jp, cp


# ─────────────────────────────────────────
# 메인
# ─────────────────────────────────────────
def main():
    print("=" * 65)
    print("📊 YouTube Demonetization 연구 — 통합 데이터 수집기 v2")
    print(f"   시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)

    # ── 1. YouTube 채널 메타데이터
    print(f"\n[1/3] YouTube 공개 채널 메타데이터 수집 ({len(ALL_CHANNELS)}개 채널)...")
    yt_results = []
    for i, ch in enumerate(ALL_CHANNELS, 1):
        print(f"  ({i:02d}/{len(ALL_CHANNELS)}) {ch['name']:<25} [{ch['type']:^11}] ...", end=" ", flush=True)
        r = fetch_youtube_public(ch["id"])
        r.update({"type": ch["type"], "country": ch["country"]})
        yt_results.append(r)
        ok = "✅" if r.get("status") == "ok" else f"⚠  {r.get('status','')}"
        subs = r.get("subscribers", "")
        print(f"{ok}  구독자: {subs}")
    
    jp, cp = save_json_csv(yt_results, "yt_channel_meta_v2")
    ok_cnt = sum(1 for r in yt_results if r.get("status") == "ok")
    print(f"  → {ok_cnt}/{len(ALL_CHANNELS)}개 성공 | {jp.name}")

    # ── 2. Reddit PullPush 넷노그라피
    print("\n[2/3] Reddit Demonetization 게시물 수집 (PullPush API)...")
    reddit_queries = [
        ("PartneredYoutube", "demonetization AI"),
        ("PartneredYoutube", "AI channel demonetized"),
        ("PartneredYoutube", "artificial intelligence monetization"),
        ("NewTubers",        "AI demonetization"),
        ("youtube",          "AI generated demonetized 2025"),
        ("youtubers",        "demonetization AI content"),
    ]
    reddit_posts = fetch_reddit_pullpush(reddit_queries, size=25)
    jp2, cp2 = save_json_csv(reddit_posts, "reddit_demonetization_v2")
    print(f"  → 총 {len(reddit_posts)}건 (중복 제거) | {jp2.name}")

    # ── 3. YouTube에서 AI 채널 추가 탐색
    print("\n[3/3] YouTube 검색으로 AI 크리에이터 채널 탐색...")
    search_keywords = [
        "AI generated YouTube channel Korea",
        "인공지능 유튜브 채널 한국",
        "AI avatar YouTube channel",
        "AI 아바타 유튜브",
    ]
    search_results = fetch_youtube_search_meta(search_keywords)
    if search_results:
        jp3, cp3 = save_json_csv(search_results, "youtube_ai_channel_search")
        print(f"  → {len(search_results)}개 채널 발견 | {jp3.name}")
    else:
        print("  → 검색 결과 없음 (파싱 구조 변경 가능)")

    # ── 최종 요약 + 데이터 수집 전략 가이드 저장
    guide = {
        "title": "YouTube Demonetization 연구 데이터 수집 전략 가이드",
        "researcher": "김재환 (중앙대학교 첨단영상대학원)",
        "date": datetime.now().isoformat(),
        "sources": {
            "youtube_api": {
                "status": f"{ok_cnt}/{len(ALL_CHANNELS)}개 성공",
                "method": "YouTube 공개 채널 페이지 크롤링",
                "next_step": "YouTube Data API v3 키 발급 후 statistics/status 파트 추가 수집 권장",
                "api_quota_note": "기본 할당량 10,000 units/day. 채널당 약 5 units 소비."
            },
            "socialblade": {
                "status": "403 차단 (서버 측 봇 방어)",
                "alternatives": [
                    "Apify Social Blade Actor 사용 (유료, 월 $5~): https://apify.com/radeance/socialblade-api",
                    "Social Blade 수동 수집 + 스크린샷 (소규모 연구용)",
                    "YouTube Data API statistics로 대체 (조회수·구독자 직접 수집)"
                ]
            },
            "reddit": {
                "status": f"{len(reddit_posts)}건 수집 (PullPush API)",
                "method": "PullPush.io 무료 공개 API",
                "next_step": "NVivo/Atlas.ti 또는 Python nltk로 텍스트 코딩 분석"
            },
            "academic_datasets": {
                "kaggle": "https://www.kaggle.com/datasets/mihikaajayjadhav/youtube-tech-channels-statistics-2025",
                "researchgate": "https://www.researchgate.net/publication/397007139",
                "acm_dunna2022": "ACM 논문 저자(dunna@cs.umn.edu)에게 354,000개 영상 데이터셋 공유 요청"
            },
            "korean_specific": {
                "방통위": "방송통신위원회 플랫폼 이용자 조사 (https://kcc.go.kr)",
                "KISDI": "https://www.kisdi.re.kr",
                "KMCNA": "한국 MCN 협회 공개 데이터"
            }
        },
        "triangulation_design": {
            "phase1_quantitative": "YouTube Data API + Social Blade(Apify) → 시계열 통계",
            "phase2_qualitative": "Reddit PullPush 넷노그라피 + 심층 인터뷰 50명",
            "phase3_policy": "유튜브 정책 문서 분석 (2020~2026) + 한/미/유럽 비교",
            "cutoff_date": "2025-07 (YouTube 비진정성 AI 콘텐츠 정책 변경 기준점)"
        }
    }
    guide_path = OUTPUT_DIR / "data_collection_strategy.json"
    with open(guide_path, "w", encoding="utf-8") as f:
        json.dump(guide, f, ensure_ascii=False, indent=2)

    print("\n" + "=" * 65)
    print("📋 수집 완료 요약")
    print("=" * 65)
    print(f"  ✅ YouTube 채널 메타데이터: {ok_cnt}/{len(ALL_CHANNELS)}개")
    print(f"  ✅ Reddit Demonetization 게시물: {len(reddit_posts)}건")
    print(f"  ✅ 데이터 수집 전략 가이드: {guide_path.name}")
    print(f"\n  📁 결과 폴더: {OUTPUT_DIR}")
    print(f"  완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 65)


if __name__ == "__main__":
    main()
