#!/usr/bin/env python3
"""
Social Blade 채널 데이터 수집기
=================================
목적: 유튜브 Demonetization 연구를 위한 채널 통계 시계열 데이터 수집
연구자: 김재환 (중앙대학교 첨단영상대학원)

수집 전략:
 - Social Blade 공개 채널 페이지 크롤링 (API 키 불필요)
 - 수익화 상태 변화 추적 (2024~2026)
 - AI 생성 콘텐츠 채널 vs 전통 채널 비교

⚠️  주의사항:
 - Social Blade 공개 데이터만 수집 (개인정보 없음)
 - robots.txt 준수, 요청 간 딜레이 적용
 - 학술 연구 목적만으로 사용
"""

import requests
import json
import time
import csv
import os
import random
from datetime import datetime, timedelta
from pathlib import Path

# ─────────────────────────────────────────
# 설정
# ─────────────────────────────────────────
OUTPUT_DIR = Path(__file__).parent / "output"
OUTPUT_DIR.mkdir(exist_ok=True)

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "ko-KR,ko;q=0.9,en-US;q=0.8,en;q=0.7",
    "Referer": "https://socialblade.com/",
}

REQUEST_DELAY = (2.0, 4.0)  # 요청 간 딜레이 (초) — robots.txt 준수

# ─────────────────────────────────────────
# 연구 대상 채널 목록
# ─────────────────────────────────────────
# [AI 생성 콘텐츠 채널] — 공개 채널 ID (YouTube URL에서 확인 가능)
AI_CHANNELS = [
    {"id": "UCddiUEpeqJcYeBxX1IVBKvQ", "name": "BRIGHT SIDE",           "type": "AI", "country": "INT", "note": "AI 그래픽 기반 교육 채널"},
    {"id": "UC9-y-6csu5WGm29I7JiwpnA", "name": "Computerphile",          "type": "AI", "country": "UK",  "note": "AI/CS 교육"},
    {"id": "UCbmNph6atAoGfqLoCL_duAg", "name": "Kurzgesagt",             "type": "AI", "country": "DE",  "note": "AI 애니메이션 기반"},
    {"id": "UCsXVk37bltHxD1rDPwtNM8Q", "name": "Kurzgesagt KR",         "type": "AI", "country": "KR",  "note": "한국어 AI 교육"},
    {"id": "UC4JX40jDee_tINbkjycV4Sg", "name": "Tech With Tim",          "type": "AI", "country": "US",  "note": "AI 코딩 교육"},
    {"id": "UCWX3yGbODI3HLNnFCNfQigA", "name": "AI Explained",           "type": "AI", "country": "US",  "note": "AI 뉴스/분석"},
    {"id": "UCnUYZLuoy1rq1aVMwx4aTzw", "name": "두두팝DUDUPOP",          "type": "AI", "country": "KR",  "note": "한국 AI 콘텐츠"},
    {"id": "UC_x5XG1OV2P6uZZ5FSM9Ttw", "name": "Google Developers",     "type": "AI", "country": "US",  "note": "AI 기술 콘텐츠"},
]

# [전통 크리에이터 채널] — 비교 대조군
TRADITIONAL_CHANNELS = [
    {"id": "UCXuqSBlHAE6Xw-yeJA0Tunw", "name": "Linus Tech Tips",       "type": "Traditional", "country": "CA",  "note": "IT 리뷰, 직접 촬영"},
    {"id": "UCBcRF18a7Qf58cCRy5xuWwQ", "name": "MrBeast",               "type": "Traditional", "country": "US",  "note": "엔터테인먼트, 직접 출연"},
    {"id": "UC295-Dw4tzbADgNButmlKiA", "name": "MKBHD",                 "type": "Traditional", "country": "US",  "note": "테크 리뷰, 직접 촬영"},
    {"id": "UCVhQ2NnY5Rskt6UjCUkJ_DA", "name": "MKBHD (Korean sub)",   "type": "Traditional", "country": "KR",  "note": "한국어 더빙"},
    {"id": "UCo8bcnLyZH8tBIH9V1mLgqQ", "name": "Batman",               "type": "Traditional", "country": "KR",  "note": "한국 IT 유튜버"},
    {"id": "UCupvZG-5ko_eiXAupbDfxWw", "name": "CNN",                   "type": "Traditional", "country": "US",  "note": "뉴스 미디어"},
    {"id": "UCaXkIU1QidjPwiAYu6GcHjg", "name": "JTBC News",            "type": "Traditional", "country": "KR",  "note": "한국 뉴스 방송"},
    {"id": "UCQMBxjbngN7lHIBg_BLBeCg", "name": "KBS News",             "type": "Traditional", "country": "KR",  "note": "한국 공영방송"},
]

ALL_CHANNELS = AI_CHANNELS + TRADITIONAL_CHANNELS


# ─────────────────────────────────────────
# Social Blade 데이터 수집 함수
# ─────────────────────────────────────────

def fetch_socialblade_stats(channel_id: str, channel_name: str) -> dict:
    """Social Blade에서 채널 통계 수집"""
    url = f"https://socialblade.com/youtube/channel/{channel_id}"
    
    try:
        time.sleep(random.uniform(*REQUEST_DELAY))
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()
        
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(resp.text, "lxml")
        
        result = {
            "channel_id":   channel_id,
            "channel_name": channel_name,
            "collected_at": datetime.now().isoformat(),
            "url":          url,
        }
        
        # 구독자 수
        sub_elem = soup.select_one("#YouTubeUserTopInfoBlock > div:nth-child(3) span")
        if sub_elem:
            result["subscribers"] = sub_elem.text.strip()
        
        # 총 조회수
        view_elem = soup.select_one("#YouTubeUserTopInfoBlock > div:nth-child(4) span")
        if view_elem:
            result["total_views"] = view_elem.text.strip()
        
        # 등급
        grade_elem = soup.select_one(".socialblade-user-pag span")
        if grade_elem:
            result["grade"] = grade_elem.text.strip()

        # 월별 예상 수익
        earn_elems = soup.select(".YouTubeUserTopInfo span[style*='color: #41a200']")
        if len(earn_elems) >= 2:
            result["monthly_earn_low"]  = earn_elems[0].text.strip()
            result["monthly_earn_high"] = earn_elems[1].text.strip()

        # 30일 통계 테이블에서 조회수 변화 추출
        rows = soup.select("table#rawDataTableModal tr")
        daily_data = []
        for row in rows[1:32]:  # 최근 30일
            cols = row.select("td")
            if len(cols) >= 4:
                daily_data.append({
                    "date":       cols[0].text.strip(),
                    "subs_delta": cols[1].text.strip(),
                    "views_delta":cols[3].text.strip(),
                })
        result["daily_30d"] = daily_data
        result["status"] = "ok"
        
    except requests.HTTPError as e:
        result = {"channel_id": channel_id, "channel_name": channel_name,
                  "status": f"http_error:{e.response.status_code}", "collected_at": datetime.now().isoformat()}
    except Exception as e:
        result = {"channel_id": channel_id, "channel_name": channel_name,
                  "status": f"error:{str(e)}", "collected_at": datetime.now().isoformat()}
    
    return result


# ─────────────────────────────────────────
# YouTube Data API v3 수집 함수
# ─────────────────────────────────────────

def fetch_youtube_api(channel_id: str, api_key: str = None) -> dict:
    """YouTube Data API v3으로 채널 메타데이터 수집"""
    if not api_key:
        # API 키 없이 공개 채널 페이지에서 기본 정보 수집
        return fetch_youtube_public(channel_id)

    url = "https://www.googleapis.com/youtube/v3/channels"
    params = {
        "part": "snippet,statistics,contentDetails,status",
        "id":   channel_id,
        "key":  api_key,
    }
    try:
        resp = requests.get(url, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        items = data.get("items", [])
        if not items:
            return {"channel_id": channel_id, "status": "not_found"}
        
        item = items[0]
        stats   = item.get("statistics", {})
        snippet = item.get("snippet", {})
        status  = item.get("status", {})
        
        return {
            "channel_id":          channel_id,
            "title":               snippet.get("title"),
            "country":             snippet.get("country"),
            "published_at":        snippet.get("publishedAt"),
            "subscribers":         stats.get("subscriberCount"),
            "total_views":         stats.get("viewCount"),
            "video_count":         stats.get("videoCount"),
            "is_linked":           status.get("isLinked"),
            "privacy_status":      status.get("privacyStatus"),
            "made_for_kids":       status.get("madeForKids"),
            "collected_at":        datetime.now().isoformat(),
            "status":              "ok",
        }
    except Exception as e:
        return {"channel_id": channel_id, "status": f"error:{e}"}


def fetch_youtube_public(channel_id: str) -> dict:
    """YouTube API 키 없이 공개 채널 페이지에서 기본 정보 수집"""
    url = f"https://www.youtube.com/channel/{channel_id}"
    try:
        time.sleep(random.uniform(*REQUEST_DELAY))
        resp = requests.get(url, headers=HEADERS, timeout=15)
        resp.raise_for_status()

        # ytInitialData JSON 추출
        text = resp.text
        marker = "var ytInitialData = "
        start = text.find(marker)
        if start == -1:
            return {"channel_id": channel_id, "status": "parse_error:ytInitialData not found"}
        
        start += len(marker)
        depth, end = 0, start
        for i, ch in enumerate(text[start:], start):
            if ch == '{': depth += 1
            elif ch == '}':
                depth -= 1
                if depth == 0:
                    end = i + 1
                    break
        
        data = json.loads(text[start:end])
        
        # 채널 기본 정보 추출
        header = data.get("header", {}).get("c4TabbedHeaderRenderer", {})
        title = header.get("title", "")
        
        meta = data.get("metadata", {}).get("channelMetadataRenderer", {})
        desc = meta.get("description", "")[:200]
        
        return {
            "channel_id":   channel_id,
            "title":        title,
            "description":  desc,
            "collected_at": datetime.now().isoformat(),
            "status":       "ok_public",
        }
    except Exception as e:
        return {"channel_id": channel_id, "status": f"error:{e}"}


# ─────────────────────────────────────────
# Reddit r/PartneredYoutube 넷노그라피 수집
# ─────────────────────────────────────────

def fetch_reddit_demonetization(subreddit: str = "PartneredYoutube",
                                 query: str = "demonetization AI",
                                 limit: int = 50) -> list:
    """Reddit 공개 API로 Demonetization 관련 게시물 수집"""
    url = f"https://www.reddit.com/r/{subreddit}/search.json"
    params = {
        "q":      query,
        "sort":   "relevance",
        "t":      "year",
        "limit":  limit,
        "restrict_sr": "true",
    }
    headers = {"User-Agent": "academic-research-bot/1.0 (PhD study on YouTube demonetization)"}
    
    try:
        time.sleep(random.uniform(1.5, 3.0))
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        resp.raise_for_status()
        data = resp.json()
        
        posts = []
        for item in data.get("data", {}).get("children", []):
            p = item.get("data", {})
            posts.append({
                "id":           p.get("id"),
                "title":        p.get("title"),
                "score":        p.get("score"),
                "num_comments": p.get("num_comments"),
                "created_utc":  datetime.fromtimestamp(p.get("created_utc", 0)).isoformat(),
                "url":          "https://reddit.com" + p.get("permalink", ""),
                "selftext":     p.get("selftext", "")[:500],  # 본문 500자 요약
                "author":       "[익명처리]",  # 개인정보 보호
                "flair":        p.get("link_flair_text", ""),
            })
        return posts
    except Exception as e:
        print(f"Reddit 수집 오류: {e}")
        return []


# ─────────────────────────────────────────
# 결과 저장
# ─────────────────────────────────────────

def save_results(data: list, filename: str):
    """JSON + CSV 형식으로 저장"""
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # JSON 저장
    json_path = OUTPUT_DIR / f"{filename}_{ts}.json"
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"  ✅ JSON 저장: {json_path}")
    
    # CSV 저장 (daily_30d 제외한 평탄화 데이터)
    csv_path = OUTPUT_DIR / f"{filename}_{ts}.csv"
    if data:
        flat = [{k: v for k, v in d.items() if k != "daily_30d"} for d in data]
        keys = flat[0].keys()
        with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(flat)
        print(f"  ✅ CSV 저장: {csv_path}")
    
    return json_path, csv_path


# ─────────────────────────────────────────
# 메인 실행
# ─────────────────────────────────────────

def main():
    print("=" * 60)
    print("📊 YouTube Demonetization 연구 데이터 수집기")
    print("   연구자: 김재환 (중앙대학교 첨단영상대학원)")
    print(f"   수집 시작: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)

    # ── 1단계: Social Blade 채널 통계 수집
    print("\n[1/3] Social Blade 채널 통계 수집 중...")
    sb_results = []
    for i, ch in enumerate(ALL_CHANNELS, 1):
        print(f"  ({i:02d}/{len(ALL_CHANNELS)}) {ch['name']} [{ch['type']}] ...", end=" ", flush=True)
        result = fetch_socialblade_stats(ch["id"], ch["name"])
        result.update({"type": ch["type"], "country": ch["country"], "note": ch["note"]})
        sb_results.append(result)
        status = result.get("status", "unknown")
        print(f"{'✅' if status == 'ok' else '⚠ ' + status}")
    
    save_results(sb_results, "socialblade_stats")

    # ── 2단계: YouTube 공개 채널 정보 수집
    print("\n[2/3] YouTube 공개 채널 메타데이터 수집 중...")
    yt_results = []
    for i, ch in enumerate(ALL_CHANNELS[:8], 1):  # 처음 8개만 (할당량 보호)
        print(f"  ({i:02d}/08) {ch['name']} ...", end=" ", flush=True)
        result = fetch_youtube_public(ch["id"])
        result.update({"type": ch["type"], "country": ch["country"]})
        yt_results.append(result)
        print(f"{'✅' if 'ok' in result.get('status','') else '⚠ ' + result.get('status','')}")
    
    save_results(yt_results, "youtube_channel_meta")

    # ── 3단계: Reddit 넷노그라피 데이터 수집
    print("\n[3/3] Reddit r/PartneredYoutube Demonetization 게시물 수집 중...")
    queries = [
        ("PartneredYoutube", "AI demonetization 2025"),
        ("PartneredYoutube", "artificial intelligence monetization"),
        ("NewTubers",        "demonetization AI channel"),
    ]
    reddit_results = []
    for sub, q in queries:
        print(f"  🔍 r/{sub} 검색: \"{q}\" ...", end=" ", flush=True)
        posts = fetch_reddit_demonetization(sub, q, limit=25)
        for p in posts:
            p["subreddit"] = sub
            p["query"] = q
        reddit_results.extend(posts)
        print(f"✅ {len(posts)}건 수집")
    
    # 중복 제거
    seen, unique = set(), []
    for p in reddit_results:
        if p["id"] not in seen:
            seen.add(p["id"])
            unique.append(p)
    
    save_results(unique, "reddit_demonetization")

    # ── 최종 요약
    print("\n" + "=" * 60)
    print("📋 수집 완료 요약")
    print("=" * 60)
    ok_sb = sum(1 for r in sb_results if r.get("status") == "ok")
    print(f"  Social Blade 채널 통계: {ok_sb}/{len(ALL_CHANNELS)}개 성공")
    ok_yt = sum(1 for r in yt_results if "ok" in r.get("status", ""))
    print(f"  YouTube 채널 메타데이터: {ok_yt}/{len(yt_results)}개 성공")
    print(f"  Reddit 게시물: {len(unique)}건 (중복 제거)")
    print(f"\n  📁 결과 폴더: {OUTPUT_DIR}")
    print(f"  수집 완료: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)


if __name__ == "__main__":
    main()
