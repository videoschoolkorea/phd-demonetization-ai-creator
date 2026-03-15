# 데이터 수집 스크립트

## 파일 구성

| 파일 | 설명 |
|------|------|
| `collector_v2.py` | 통합 수집기 v2 (YouTube + Reddit PullPush) |
| `socialblade_collector.py` | Social Blade 수집기 v1 (참고용) |
| `output/yt_channel_meta_v2_*.json` | YouTube 채널 메타데이터 (16개) |
| `output/reddit_demonetization_v2_*.json` | Reddit Demonetization 게시물 (15건) |
| `output/youtube_ai_channel_search_*.json` | AI 채널 탐색 결과 (80개) |
| `output/data_collection_strategy.json` | 데이터 수집 전략 가이드 |

## 수집 결과 요약 (2026-03-15)

| 소스 | 결과 | 방법 |
|------|------|------|
| YouTube 채널 메타 | 16/16개 ✅ | 공개 페이지 크롤링 |
| Reddit 게시물 | 15건 ✅ | PullPush 공개 API |
| AI 채널 탐색 | 80개 ✅ | YouTube 검색 결과 |
| Social Blade | 차단(403) | Apify 유료 API 대안 |

## 실행 방법

```bash
pip install requests beautifulsoup4 lxml
python3 collector_v2.py
```

## YouTube Data API v3 키 추가 시

```python
# collector_v2.py 수정
API_KEY = "YOUR_API_KEY"  # Google Cloud Console에서 발급
result = fetch_youtube_api(channel_id, api_key=API_KEY)
# statistics.viewCount, statistics.subscriberCount, status.isLinked 등 추가 수집 가능
```

## 윤리 고지
- 공개 데이터만 수집 (개인정보 없음)
- Reddit author 필드 익명처리
- robots.txt 준수 (요청 간 2~4초 딜레이)
- 학술 연구 목적 전용
