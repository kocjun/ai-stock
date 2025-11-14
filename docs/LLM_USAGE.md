# LLM 사용 가이드

AI 주식 분석 시스템의 LLM 설정 및 사용 방법

---

## 🎯 시스템 개요

본 시스템은 **하이브리드 LLM 전략**을 사용합니다:

- **메인**: Ollama 로컬 LLM (무료, 프라이버시 보장)
- **검증**: OpenAI API (레드팀 검증용, 비용 최소화)

---

## 🔧 LLM 설정

### 환경 변수 (.env 파일)

```bash
# LLM 모드 (main: 로컬, redteam: OpenAI 검증)
LLM_MODE=main

# 로컬 LLM 설정 (메인 - Ollama)
OPENAI_API_BASE=http://127.0.0.1:11434
OPENAI_MODEL_NAME=gpt-oss:120b

# 레드팀 검증용 (OpenAI)
REDTEAM_MODEL=gpt-4o-mini
```

> NAS와 같이 원격 LLM 서버를 사용할 경우 `OPENAI_API_BASE`에 내부망 주소(예: `http://192.168.10.58:11434`)를 지정하면 됩니다. 실행 스크립트/테스트는 해당 값을 자동으로 참조합니다.

### 사용 가능한 모델

#### Ollama 로컬 모델 (무료)
- `gpt-oss:120b` - 65GB, 고성능 (추천)
- `llama3.1:8b` - 4.9GB, 빠른 속도
- `llava:13b` - 8GB, 멀티모달

#### OpenAI API (유료)
- `gpt-4o` - 최고 품질 ($2.5/$10 per 1M tokens)
- `gpt-4o-mini` - 빠르고 저렴 ($0.15/$0.60 per 1M tokens) ⭐
- `gpt-3.5-turbo` - 저렴 ($0.50/$1.50 per 1M tokens)

---

## 📊 모드 전환

### 로컬 LLM 사용 (메인)

```bash
# .env 설정
LLM_MODE=main
OPENAI_MODEL_NAME=gpt-oss:120b
```

### OpenAI 레드팀 검증

```bash
# .env 설정
LLM_MODE=redteam
REDTEAM_MODEL=gpt-4o-mini
```

---

## 🤖 사용 방법

### 1. 일일 Paper Trading (로컬 LLM)

```bash
# 로컬 LLM으로 실행
./paper_trading/run_paper_trading.sh

# 또는 직접 실행
python paper_trading/trading_crew.py --save-log
```

**예상 시간**: 10-20분 (gpt-oss:120b)
**비용**: 무료

### 2. 레드팀 검증 (OpenAI)

```bash
# 레드팀 검증 실행
./paper_trading/run_redteam_validation.sh

# 또는 직접 실행
python paper_trading/redteam_validator.py
```

**예상 시간**: 20-30분 (로컬 + OpenAI)
**비용**: ~$0.02-0.05 (OpenAI만)

### 3. 개별 Crew 실행

```bash
# 데이터 수집 (로컬)
python core/agents/investment_crew.py

# 스크리닝 분석 (로컬)
python core/agents/screening_crew.py

# 리스크 분석 (로컬)
python core/agents/risk_crew.py

# 포트폴리오 구성 (로컬)
python core/agents/portfolio_crew.py

# 통합 워크플로 (로컬)
python core/agents/integrated_crew.py
```

---

## 🗓️ 자동화 스케줄

### Cron 설정

```bash
# crontab -e

# 일일 Paper Trading (로컬 LLM) - 평일 오전 10시
0 10 * * 1-5 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/run_paper_trading.sh

# 주간 레드팀 검증 (OpenAI) - 매주 토요일 오전 6시
0 6 * * 6 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/run_redteam_validation.sh

# 주간 보고서 - 매주 토요일 오전 7시
0 7 * * 6 /Users/yeongchang.jeon/workspace/ai-agent/paper_trading/generate_weekly_report.sh
```

### 스케줄 설명

- **평일 오전 10시**: 시장 개장 후 초기 데이터로 분석
- **토요일 오전 6시**: 레드팀 검증 (주말 시간 활용)
- **토요일 오전 7시**: 주간 보고서 생성 (검증 후)

---

## 📈 레드팀 검증 결과 해석

### 일치율 기준

- **80% 이상**: ✅ 로컬 LLM 결과 신뢰 가능
- **50-80%**: ⚠️ 로컬 결과 참고, 레드팀 검토 필요
- **50% 미만**: ❌ 로컬 품질 낮음, OpenAI 결과 사용 권장

### 결과 확인

```bash
# 최신 검증 레포트 확인
cat paper_trading/logs/redteam/validation_*.json | python -m json.tool

# 레포트 요약 보기
ls -lth paper_trading/logs/redteam/
```

---

## 💰 비용 분석

### 월간 예상 비용

#### 로컬 LLM만 사용
- **일일 운영** (평일 5일): 무료
- **월 비용**: $0

#### 로컬 + 주간 검증
- **일일 운영** (평일 5일): 무료
- **주간 검증** (주 1회): ~$0.02-0.05
- **월 비용**: ~$0.08-0.20

**추천 전략**: 로컬 LLM 메인 + 주간 레드팀 검증

---

## 🔍 모델 비교

| 모델 | 크기 | 속도 | 품질 | 비용 | 추천 |
|------|------|------|------|------|------|
| gpt-oss:120b | 65GB | 느림 | 높음 | 무료 | ⭐ 메인 |
| llama3.1:8b | 4.9GB | 빠름 | 중간 | 무료 | 테스트용 |
| gpt-4o-mini | - | 매우 빠름 | 높음 | 저렴 | ⭐ 검증 |
| gpt-4o | - | 빠름 | 최고 | 중간 | 중요 분석 |

---

## 🧪 테스트 및 디버깅

### LLM 설정 확인

```bash
# LLM 유틸리티 테스트
.venv/bin/python core/utils/llm_utils.py

# 출력 예시:
# 모드: main
# 프로바이더: Ollama
# 모델: gpt-oss:120b
# 비용: 무료 (로컬)
```

### Ollama 서버 확인

```bash
# Ollama 버전 확인
curl http://127.0.0.1:11434/api/version

# 모델 리스트 확인
ollama list

# 모델 다운로드
ollama pull gpt-oss:120b
```

### OpenAI API 키 확인

```bash
# 환경변수 확인 (처음 20자만)
echo $OPENAI_API_KEY | head -c 20

# API 테스트
curl https://api.openai.com/v1/models \
  -H "Authorization: Bearer $OPENAI_API_KEY"
```

---

## ⚠️ 주의사항

### Ollama 로컬 모델

1. **메모리 요구사항**
   - gpt-oss:120b: 최소 65GB RAM
   - llama3.1:8b: 최소 8GB RAM

2. **성능**
   - GPU 가속 권장 (Apple Silicon M1/M2/M3 최적화)
   - CPU만 사용 시 추론 속도 매우 느림

3. **디스크 공간**
   - 모델 저장 공간 확보 필요
   - ~/.ollama/models에 저장됨

### OpenAI API

1. **비용 모니터링**
   - https://platform.openai.com/usage에서 확인
   - 사용량 알림 설정 권장

2. **API 키 보안**
   - .env 파일 .gitignore에 추가 (이미 설정됨)
   - 공개 저장소에 절대 커밋하지 말 것

3. **Rate Limiting**
   - 무료 tier: 제한적 사용
   - 유료 tier: 높은 한도

---

## 🛠️ 트러블슈팅

### 문제: Ollama 연결 실패

```bash
# Ollama 서비스 시작
ollama serve

# 또는 백그라운드 실행
nohup ollama serve > /dev/null 2>&1 &
```

### 문제: OpenAI API 키 인식 안 됨

```bash
# ~/.zshrc 확인
cat ~/.zshrc | grep OPENAI_API_KEY

# 셸 재시작
source ~/.zshrc

# 또는 .env 파일에 직접 추가
echo "OPENAI_API_KEY=your-key-here" >> .env
```

### 문제: 모델 로드 실패

```bash
# 모델 다시 다운로드
ollama pull gpt-oss:120b

# 모델 캐시 정리
rm -rf ~/.ollama/models/manifests/*
ollama pull gpt-oss:120b
```

### 문제: 메모리 부족

```bash
# 더 작은 모델 사용
# .env 파일 수정:
OPENAI_MODEL_NAME=llama3.1:8b

# 또는 OpenAI 사용
LLM_MODE=redteam
```

---

## 📚 추가 리소스

- **Ollama 문서**: https://ollama.ai/docs
- **OpenAI API 문서**: https://platform.openai.com/docs
- **CrewAI 문서**: https://docs.crewai.com
- **LiteLLM 문서**: https://docs.litellm.ai

---

## 🔄 업데이트 이력

- **2025-10-23**: 초기 버전 작성
  - 하이브리드 LLM 전략 구현
  - 로컬 Ollama + OpenAI 레드팀 검증
  - 자동화 스케줄 설정

---

**작성일**: 2025-10-23
**버전**: 1.0
