# 데이터 수집 모니터링 가이드

## 📊 실시간 모니터링

### 1. 로그 파일 모니터링
```bash
# 실시간 로그 보기
tail -f logs/collection_*.log

# 에러만 필터링
tail -f logs/collection_*.log | grep -i "error\|실패\|✗"

# 최근 10개 로그 파일
ls -lt logs/ | head -10
```

### 2. 데이터베이스 현황

#### 전체 통계
```bash
docker exec investment_postgres psql -U invest_user -d investment_db << EOF
-- 전체 데이터 현황
SELECT
    '종목 수' as metric,
    COUNT(*)::text as value
FROM stocks
UNION ALL
SELECT
    '가격 데이터 건수',
    COUNT(*)::text
FROM prices
UNION ALL
SELECT
    '재무 데이터 건수',
    COUNT(*)::text
FROM financials
UNION ALL
SELECT
    '최근 수집 일자',
    MAX(date)::text
FROM prices;
EOF
```

#### 종목별 데이터 상태
```bash
docker exec investment_postgres psql -U invest_user -d investment_db << EOF
-- 종목별 가격 데이터 현황 (상위 20개)
SELECT
    s.code,
    s.name,
    COUNT(p.date) as price_days,
    MIN(p.date) as start_date,
    MAX(p.date) as end_date,
    MAX(p.close) as latest_price
FROM stocks s
LEFT JOIN prices p ON s.code = p.code
GROUP BY s.code, s.name
ORDER BY price_days DESC
LIMIT 20;
EOF
```

#### 일별 수집량 추이
```bash
docker exec investment_postgres psql -U invest_user -d investment_db << EOF
-- 최근 7일간 수집 추이
SELECT
    date,
    COUNT(DISTINCT code) as stock_count,
    COUNT(*) as price_records
FROM prices
WHERE date >= CURRENT_DATE - INTERVAL '7 days'
GROUP BY date
ORDER BY date DESC;
EOF
```

### 3. Docker 서비스 상태
```bash
# 컨테이너 상태
docker ps --filter "name=investment"

# PostgreSQL 헬스 체크
docker exec investment_postgres pg_isready -U invest_user

# n8n 상태
curl -s http://localhost:5678 > /dev/null && echo "✓ n8n 정상" || echo "✗ n8n 오류"

# Ollama 상태
curl -s http://localhost:11434/api/tags > /dev/null && echo "✓ Ollama 정상" || echo "✗ Ollama 오류"
```

---

## 🚨 알림 설정

### Slack 알림 (옵션)

n8n 워크플로에 Slack 연동을 추가하려면:

1. **Slack Webhook URL 생성**
   - https://api.slack.com/messaging/webhooks
   - Incoming Webhooks 앱 설치
   - 채널 선택 및 URL 복사

2. **.env 파일에 추가**
```bash
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL
```

3. **n8n 워크플로 활성화**
   - [n8n_workflows/data_collection_workflow.json](n8n_workflows/data_collection_workflow.json)
   - Slack 노드 설정

### 이메일 알림 (옵션)

간단한 이메일 알림 스크립트:
```bash
#!/bin/bash
# send_notification.sh

RECIPIENT="your-email@example.com"
SUBJECT="AI Agent Data Collection Report"
BODY="$(tail -20 logs/collection_*.log | tail -1)"

echo "$BODY" | mail -s "$SUBJECT" "$RECIPIENT"
```

---

## 🔧 문제 해결

### 자주 발생하는 문제

#### 1. PostgreSQL 연결 실패
```bash
# 컨테이너 재시작
docker-compose restart postgres

# 연결 테스트
docker exec investment_postgres psql -U invest_user -d investment_db -c "SELECT 1;"
```

#### 2. Ollama 서버 응답 없음
```bash
# Ollama 서비스 확인
ps aux | grep ollama

# Ollama 재시작 (macOS)
pkill ollama
ollama serve &

# 모델 확인
ollama list
```

#### 3. 데이터 수집 실패
```bash
# 로그 확인
tail -50 logs/collection_*.log

# 환경 변수 확인
cat .env | grep -v "PASSWORD\|SECRET"

# 수동 테스트
source .venv/bin/activate
python test_fdr.py
```

#### 4. cron job 실행 안됨
```bash
# cron 서비스 상태 (macOS)
sudo launchctl list | grep cron

# cron job 확인
crontab -l

# 권한 확인
ls -l run_daily_collection.sh

# 절대 경로로 다시 설정
pwd  # 현재 경로 확인
crontab -e  # 경로 수정
```

---

## 📈 성능 최적화

### 데이터베이스 최적화
```sql
-- 인덱스 생성 (아직 없다면)
CREATE INDEX IF NOT EXISTS idx_prices_code_date ON prices(code, date);
CREATE INDEX IF NOT EXISTS idx_financials_code_year_quarter ON financials(code, year, quarter);

-- 통계 업데이트
ANALYZE stocks;
ANALYZE prices;
ANALYZE financials;

-- 디스크 사용량 확인
SELECT
    tablename,
    pg_size_pretty(pg_total_relation_size(schemaname||'.'||tablename)) AS size
FROM pg_tables
WHERE schemaname = 'public'
ORDER BY pg_total_relation_size(schemaname||'.'||tablename) DESC;
```

### 로그 파일 정리
```bash
# 30일 이상 된 로그 삭제
find logs/ -name "*.log" -mtime +30 -delete

# 로그 파일 압축 (월별)
tar -czf logs_archive_$(date +%Y%m).tar.gz logs/*.log
```

---

## 📊 대시보드 (향후 계획)

### Grafana + Prometheus (고급)
- PostgreSQL Exporter 설치
- Grafana 대시보드 구성
- 실시간 메트릭 시각화

### Jupyter Notebook (간단)
```python
# notebooks/monitoring_dashboard.ipynb
import psycopg2
import pandas as pd
import matplotlib.pyplot as plt

# 데이터 조회 및 시각화
conn = get_db_connection()
df = pd.read_sql("SELECT date, COUNT(*) as count FROM prices GROUP BY date ORDER BY date", conn)
df.plot(x='date', y='count', figsize=(12, 6))
plt.title('일별 가격 데이터 수집량')
plt.show()
```

---

## 🎯 주간 체크리스트

매주 확인할 사항:

- [ ] 데이터 수집이 정상적으로 실행되었는가?
- [ ] 로그 파일에 에러가 없는가?
- [ ] 데이터베이스 용량이 적절한가?
- [ ] 모든 Docker 컨테이너가 실행 중인가?
- [ ] 백테스팅 리포트가 생성되었는가?

```bash
# 자동 체크 스크립트
./run_weekly_analysis.sh
```

---

## 📞 지원

문제가 발생하면:
1. 로그 파일 확인: `logs/collection_*.log`
2. 데이터베이스 상태 확인: `docker exec investment_postgres psql ...`
3. 환경 체크: `./run_daily_collection.sh` (수동 실행)
4. 이슈 리포트: README.md 참조

---

**마지막 업데이트**: 2025-10-18
**버전**: 1.0
