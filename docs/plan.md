변경 계획 (NAS 환경 → 내부망 LLM 연동)

환경 파악

현재 Synology NAS에서 실행 중인 서비스 구성 재확인: Docker/스크립트 기반 여부, 필요한 포트, 의존 서비스 목록.
내부망에서 접근 가능한 LLM 엔드포인트 192.168.10.58의 API 사양(프로토콜, 인증 방식, 요청/응답 포맷) 문서 확보.
네트워크·보안 설정

NAS에서 192.168.10.58로의 통신 경로 및 방화벽 규칙 확인/허용.
필요 시 NAS → LLM 서버 간 SSH 터널링 또는 VPN 등 안전한 채널 검토.
인증 토큰, 키 관리용 .env 또는 Synology 환경 변수 설정 방식 정의.
애플리케이션 수정

기존 외부 LLM 호출 모듈을 추적하고 192.168.10.58 API로 교체(엔드포인트 URL, 헤더, payload 구조 업데이트).
NAS 환경에서 필요한 의존 패키지 설치 및 설정 스크립트 작성.
구성 파일(예: config.yaml, .env)에 LLM 서버 주소/포트를 매개변수로 저장하도록 변경.
배포 및 실행 스크립트 정비

NAS 전용 docker-compose 혹은 스크립트 준비: LLM 연결 정보 포함, 재시작 정책/로그 경로 정의.
모니터링/재시작 스크립트(monitor.sh 등)에서 LLM 상태 체크 루틴 추가.
테스트 및 검증

NAS 내부에서 LLM 서버로 테스트 요청을 보내 연결/성능/응답 지연 확인.
실제 서비스 플로우(핵심 기능, 오류 처리) 점검 후 로그 분석.
롤백 전략과 문제 발생 시 대응 프로세스 문서화.

### 테스트 절차 제안
1. `LLM_URL=${OPENAI_API_BASE:-http://127.0.0.1:11434}; curl "$LLM_URL/api/tags"`로 연결 상태 확인
2. `.venv/bin/python core/utils/llm_utils.py` 실행 후 로드된 모델/모드 확인
3. `python core/agents/integrated_crew.py` 또는 `paper_trading/trading_crew.py --dry-run`으로 워크플로 점검
4. `tests/run_integration_test.sh` 실행 (헬스체크가 자동으로 새 LLM URL을 사용)
5. 문제 발생 시 `.env`의 `OPENAI_API_BASE`를 기존 로컬 주소로 되돌리고 monitor 스크립트 재실행

---

## Docker 기반 개발/실행 전환 계획 (NAS Python 버전 한계 대응)

1. **Docker 베이스 이미지 선정**
   - Python 3.11+이 포함된 공식 이미지(`python:3.11-bullseye`)를 사용해 모든 의존성을 컨테이너에서 설치.
   - 필요 시 `docker/docker-compose.yml`에 새로운 서비스 `ai-stock-app` 추가.

2. **프로젝트 마운트 구조**
   - NAS 워크스페이스(`/volume2/homes/.../ai-stock`)를 컨테이너 `/app`에 마운트해 코드/로그 공유.
   - `.env` 파일은 읽기 전용으로 마운트하거나 Docker env 파일로 전달.

3. **컨테이너 빌드/실행 절차**
   - `Dockerfile` 예시
     ```
     FROM python:3.11-slim
     WORKDIR /app
     COPY requirements.txt .
     RUN pip install --no-cache-dir -r requirements.txt
     CMD ["bash"]
     ```
   - `docker-compose up -d ai-stock-app` 또는 `docker run -it --rm -v $(pwd):/app ai-stock:latest bash`.

4. **스크립트/테스트 실행 방법**
   - 컨테이너 내부에서 `python core/agents/...` 명령 실행.
   - Host 네트워크에서 내부망 LLM과 통신하려면 `--network host` 또는 NAS 내부 네트워크 브리지를 사용.

5. **운영 고려 사항**
   - 모니터링/cron은 Host에서 Docker 명령을 호출하도록 조정.
   - 로그/리포트 경로가 NAS 파일시스템에 그대로 남도록 바인드 마운트 유지.

6. **검증 절차**
   - `docker compose build ai-stock-app` → `docker compose up -d postgres n8n ai-stock-app`
   - `docker compose exec ai-stock-app bash -c "python core/utils/llm_utils.py"`로 LLM 설정 확인
   - 주요 워크플로 (`core/agents/integrated_crew.py`, `paper_trading/trading_crew.py`)를 동일 컨테이너에서 실행
