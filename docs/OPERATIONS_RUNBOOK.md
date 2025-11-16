# 운영 Runbook

서비스 재기동, 검증, 백업 절차를 요약한 문서입니다. NAS/Synology 환경에서 장애나 재부팅 이후 참고하세요.

## 1. 서비스 재시작
```bash
cd /volume2/homes/kocjunnas/workspace/ai-stock/docker
docker compose --env-file ../.env down
docker compose --env-file ../.env up -d
```

### 필수 확인
1. `docker compose --env-file ../.env ps`로 postgres/n8n/ai-stock-app 상태 확인  
2. `curl http://192.168.10.58:11434/api/tags`로 LLM 응답 확인  
3. 컨테이너 내부에서 LLM 셋업 확인
   ```bash
   docker compose --env-file ../.env exec ai-stock-app \
     bash -lc "python core/utils/llm_utils.py"
   ```

## 2. 데이터/테스트 검증
1. 초기 데이터/가상계좌 시딩  
   ```bash
   docker compose --env-file ../.env exec ai-stock-app \
     bash -lc "python scripts/bootstrap_data.py"
   ```
2. 통합 테스트  
   ```bash
   ./scripts/run_tests_in_container.sh
   ```
3. 필요한 경우 paper trading / integrated crew 직접 실행:
   ```bash
   docker compose --env-file ../.env exec ai-stock-app \
     bash -lc "python core/agents/integrated_crew.py"
   ```

## 3. n8n 워크플로 백업
1. UI에서 Export (별도 파일 저장) → 저장 후 `n8n_workflows/`에 추가 커밋  
2. CLI로 백업 (`n8n export:workflow --all --output=/data/backup`)  
3. 백업 파일은 NAS에 주기적으로 복사/스냅샷

## 4. 보안/HTTPS
- n8n이 HTTP 포트(5678)로 노출되어 있으므로 Synology Reverse Proxy + HTTPS 인증서를 설정하는 것이 권장됩니다.  
- 설정 후 `.env`의 `N8N_SECURE_COOKIE=true`로 변경 가능합니다.

## 5. 로그/모니터링
- `monitor.sh status`로 system_monitor 상태 확인.  
- Docker 로그: `docker compose logs -f <service>`  
- 필요 시 logrotate 또는 n8n/system_monitor에 Slack/메일 알림 연동을 추가하세요.
