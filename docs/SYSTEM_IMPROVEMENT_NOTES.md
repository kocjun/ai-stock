# 시스템 개선 제안

현재 Synology NAS 상에서 Docker( Postgres / ai-stock-app / n8n )와 내부망 LLM(192.168.10.58)으로 전체 파이프라인이 동작하고 있다. 통합 테스트까지 완료했지만 안정성과 운영 편의성 측면에서 개선 가능한 항목을 정리한다.

## 1. 데이터 파이프라인 안정화
- **초기 데이터 시딩 자동화**  
  - `scripts/bootstrap_data.py`를 추가해 주식/가격 수집이 부족하거나 오래된 경우 `investment_crew`를 자동 실행하도록 했다.  
  - README의 초기 설정 절차에 Docker 컨테이너에서 해당 스크립트를 실행하는 방법을 추가했다.
- **가상 계좌/포트폴리오 기본값**  
  - 같은 스크립트에서 `paper_trading/schema.sql`을 적용하고 `virtual_accounts` 테이블에 기본 계좌를 생성해 통합 테스트가 즉시 통과하도록 했다.
- **DB 헬스체크 스크립트**  
  - (추가 예정) `system_monitor`에 Postgres 전용 헬스체크 및 자동 재시작 옵션 추가. 현재는 포트만 확인하므로 연결까지 확인하도록 개선한다.

## 2. LLM 연동 신뢰성
- **응답 타임아웃/재시도**  
  - CrewAI 레이어에서 `ValueError: Invalid response ... None or empty`는 LLM 응답 지연 때문. `core/utils/llm_utils.py`에서 사용자 정의 LLM 래퍼를 둬 재시도 또는 graceful fallback(모델 교체)을 구현한다.
- **모델/자원 모니터링**  
  - 내부망 LLM 서버 상태(메모리, 모델 로드)를 Prometheus/간단한 쉘 스크립트로 주기적 확인 후 NAS에 알림 전송. 현재는 수동 `curl`로만 확인 가능.
- **여러 모델 지원**  
  - `.env`에 `OPENAI_MODEL_NAME_FALLBACK` 등을 추가해 메인 모델 이상 시 자동으로 8B 모델로 스위칭하도록 개선.

## 3. Docker / 인프라 구조
- **host network 의존 최소화**  
  - `ai-stock-app`과 `n8n`이 `network_mode: host`에 의존 중이다. 가능하다면 브리지 네트워크 사용 + Postgres 서비스 이름(hostname)으로 접근하도록 NAS 방화벽 설정을 조정해 분리도를 높인다.
- **볼륨 권한 관리**  
  - n8n 데이터(`/data/.n8n`) 권한 문제를 해결하기 위해 컨테이너에서 root로 실행 중이다. NAS 파일 권한을 맞추고 비루트 계정으로 돌아가면 보안 위험을 낮출 수 있다.
- **환경변수 전달 통일**  
  - `.env`를 여러 스크립트에서 직접 `source`하고 있어 파편화 가능. `scripts/load_env.sh` 같은 공통 로더를 두면 유지보수가 쉬워진다.

## 4. 테스트 및 관측성
- **컨테이너 내부 테스트 공식화**  
  - README/plan.md에 “모든 테스트는 `docker compose exec ai-stock-app` 안에서 실행한다”는 지침을 명시해 혼선을 줄인다.
- **테스트 결과 요약 자동화**  
  - `tests/run_integration_test.sh` 실행 후 n8n 또는 Slack으로 로그 요약을 전송하는 훅을 넣으면 수동 확인 부담이 줄어든다.
- **로그 관리**  
  - `./logs`와 `tests/logs`가 무한 성장할 수 있으므로 logrotate 또는 일정 기간 이후 삭제 스크립트를 준비한다.

## 5. 문서화 및 운영
- **n8n 워크플로 백업**  
  - `n8n_workflows/`에 수동으로 내보낸 JSON을 커밋했지만, 주기적으로 n8n export > repo 반영 프로세스를 문서화한다.  
- **운영 시나리오**  
  - plan.md에 NAS 재부팅/스냅샷 후 재기동 절차(Docker compose up, LLM 상태 확인)를 추가하면 운영자가 쉽게 대응 가능.
- **보안**  
  - n8n이 HTTP로 열려 있으므로 Synology Reverse Proxy + HTTPS 적용 계획을 문서화하고, `N8N_SECURE_COOKIE=true`를 사용할 수 있도록 준비한다.

위 개선 사항을 우선순위별로 도입하면 NAS 환경에서도 안정적이고 재현 가능한 배포가 가능해진다.
