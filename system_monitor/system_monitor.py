#!/usr/bin/env python3
"""
시스템 프로세스 모니터링 및 관리 도구

기능:
1. 전체 백그라운드 프로세스 상태 모니터링
2. Docker 컨테이너 상태 확인 (PostgreSQL, N8N)
3. Python 백그라운드 프로세스 관리
4. 프로세스 자동 재실행 및 복구
5. 대시보드 형식의 상태 표시
"""

import subprocess
import json
import os
import sys
import time
import signal
from pathlib import Path
from typing import Dict, List, Tuple
from datetime import datetime
from dataclasses import dataclass
from urllib import request, error
import psutil
from dotenv import load_dotenv

# 프로젝트 루트 경로
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.append(str(PROJECT_ROOT))
load_dotenv(PROJECT_ROOT / ".env")


@dataclass
class ProcessInfo:
    """프로세스 정보"""
    name: str
    pid: int = None
    status: str = "unknown"  # running, stopped, error
    type: str = "python"  # python, docker, system
    command: str = ""
    memory_mb: float = 0.0
    cpu_percent: float = 0.0
    uptime_minutes: int = 0
    auto_restart: bool = False


class SystemMonitor:
    """시스템 모니터링 및 관리 클래스"""

    def __init__(self):
        self.processes: Dict[str, ProcessInfo] = {}
        self.config_file = PROJECT_ROOT / "system_monitor" / "processes.json"
        self.log_file = PROJECT_ROOT / "system_monitor" / "monitor.log"
        self.load_config()

    def load_config(self):
        """설정 파일에서 모니터링할 프로세스 목록 로드"""
        if self.config_file.exists():
            try:
                with open(self.config_file, 'r') as f:
                    config = json.load(f)
                    for process_name, settings in config.get('processes', {}).items():
                        self.processes[process_name] = ProcessInfo(
                            name=process_name,
                            auto_restart=settings.get('auto_restart', True),
                            type=settings.get('type', 'python'),
                            command=settings.get('command', '')
                        )
            except Exception as e:
                self.log(f"설정 파일 로드 실패: {e}")

    def log(self, message: str):
        """로그 기록"""
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        log_message = f"[{timestamp}] {message}"
        print(log_message)

        # 파일에도 저장
        try:
            with open(self.log_file, 'a') as f:
                f.write(log_message + '\n')
        except:
            pass

    def check_python_process(self, process_name: str) -> ProcessInfo:
        """Python 백그라운드 프로세스 상태 확인"""
        info = self.processes.get(process_name, ProcessInfo(name=process_name, type="python"))

        try:
            # PID 파일 확인
            pid_file = PROJECT_ROOT / "system_monitor" / f"{process_name}.pid"

            if pid_file.exists():
                try:
                    with open(pid_file, 'r') as f:
                        pid = int(f.read().strip())

                    # 프로세스 존재 확인
                    if psutil.pid_exists(pid):
                        process = psutil.Process(pid)

                        # 프로세스 정보 수집
                        try:
                            info.pid = pid
                            info.status = "running"
                            info.memory_mb = process.memory_info().rss / 1024 / 1024
                            info.cpu_percent = process.cpu_percent(interval=0.1)

                            # 업타임 계산
                            create_time = process.create_time()
                            uptime_seconds = time.time() - create_time
                            info.uptime_minutes = int(uptime_seconds / 60)
                        except (psutil.NoSuchProcess, psutil.AccessDenied):
                            info.status = "error"
                    else:
                        info.status = "stopped"
                        info.pid = None
                except ValueError:
                    info.status = "error"
            else:
                info.status = "stopped"
                info.pid = None

        except Exception as e:
            info.status = "error"
            self.log(f"프로세스 확인 오류 ({process_name}): {e}")

        return info

    def check_docker_container(self, container_name: str) -> ProcessInfo:
        """Docker 컨테이너 상태 확인"""
        info = ProcessInfo(name=container_name, type="docker")

        try:
            result = subprocess.run(
                ["docker", "ps", "-a", "--format", "{{.Names}},{{.Status}}"],
                capture_output=True,
                text=True,
                timeout=5
            )

            for line in result.stdout.strip().split('\n'):
                if not line:
                    continue
                name, status = line.split(',', 1)
                if name == container_name:
                    if "Up" in status:
                        info.status = "running"
                        # uptime 추출
                        if "Up" in status:
                            parts = status.split("Up")[1].strip().split(",")[0]
                            # 간단히 분으로 변환 (정확한 파싱 생략)
                            info.uptime_minutes = 0
                    elif "Exited" in status:
                        info.status = "stopped"
                    else:
                        info.status = "unknown"
                    break

            if info.status == "unknown":
                info.status = "not_found"

        except subprocess.TimeoutExpired:
            info.status = "error"
            self.log("Docker 확인 타임아웃")
        except FileNotFoundError:
            info.status = "error"
            self.log("Docker가 설치되지 않았습니다")
        except Exception as e:
            info.status = "error"
            self.log(f"Docker 확인 오류: {e}")

        return info

    def check_port(self, port: int) -> bool:
        """특정 포트의 서비스 실행 확인"""
        try:
            result = subprocess.run(
                ["lsof", "-i", f":{port}"],
                capture_output=True,
                timeout=3
            )
            return result.returncode == 0
        except:
            return False

    def check_http_endpoint(self, url: str, timeout: int = 5) -> bool:
        """HTTP 엔드포인트 헬스 체크"""
        try:
            with request.urlopen(url, timeout=timeout) as resp:
                return 200 <= resp.status < 400
        except Exception:
            return False

    def get_all_status(self) -> Dict:
        """모든 프로세스의 현재 상태 조회"""
        status = {
            'timestamp': datetime.now().isoformat(),
            'python_processes': {},
            'docker_containers': {},
            'services': {}
        }

        # 설정 파일 로드
        try:
            with open(self.config_file, 'r') as f:
                config = json.load(f)
        except Exception as e:
            self.log(f"설정 파일 로드 실패: {e}")
            config = {'processes': {}, 'docker_containers': {}, 'services': {}}

        # Python 백그라운드 프로세스 (설정 파일에서 동적 로드)
        for proc_key, proc_config in config.get('processes', {}).items():
            info = self.check_python_process(proc_key)
            status['python_processes'][proc_key] = {
                'name': info.name,
                'status': info.status,
                'pid': info.pid,
                'memory_mb': round(info.memory_mb, 2),
                'cpu_percent': round(info.cpu_percent, 2),
                'uptime_minutes': info.uptime_minutes
            }

        # Docker 컨테이너 (설정 파일에서 동적 로드)
        for container_key, container_config in config.get('docker_containers', {}).items():
            info = self.check_docker_container(container_key)
            status['docker_containers'][container_key] = {
                'name': info.name,
                'status': info.status,
                'uptime_minutes': info.uptime_minutes
            }

        # 서비스 포트 확인 (설정 파일에서 동적 로드)
        for service_name, service_config in config.get('services', {}).items():
            port = service_config.get('port')
            base_url = None
            resolved_url = None

            # 우선순위: 환경 변수 → 고정 URL
            url_env = service_config.get('url_env')
            if url_env:
                env_value = os.getenv(url_env)
                if env_value:
                    base_url = env_value.rstrip('/')

            if not base_url and service_config.get('url'):
                base_url = service_config.get('url').rstrip('/')

            health_path = service_config.get('health_path')
            if base_url:
                if health_path:
                    if not health_path.startswith('/'):
                        health_path = f"/{health_path}"
                    resolved_url = f"{base_url}{health_path}"
                else:
                    resolved_url = base_url

            if resolved_url:
                available = self.check_http_endpoint(resolved_url)
            elif port:
                available = self.check_port(port)
            else:
                available = False

            status['services'][service_name] = {
                'port': port,
                'url': resolved_url,
                'available': available
            }

        return status

    def display_dashboard(self):
        """대시보드 형식으로 상태 표시"""
        status = self.get_all_status()

        print("\n" + "="*100)
        print("🖥️  시스템 프로세스 모니터링 대시보드")
        print("="*100)
        print(f"업데이트: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")

        # Python 프로세스
        print("📌 Python 백그라운드 프로세스")
        print("-"*100)

        for proc_key, proc_info in status['python_processes'].items():
            status_icon = self._get_status_icon(proc_info['status'])
            print(f"\n{status_icon} {proc_key.upper()}")
            print(f"   상태:      {proc_info['status'].upper()}")
            if proc_info['pid']:
                print(f"   PID:       {proc_info['pid']}")
                print(f"   메모리:    {proc_info['memory_mb']:.2f} MB")
                print(f"   CPU:       {proc_info['cpu_percent']:.1f}%")
                print(f"   업타임:    {proc_info['uptime_minutes']}분")

        # Docker 컨테이너
        print("\n\n📦 Docker 컨테이너")
        print("-"*100)

        for container_key, container_info in status['docker_containers'].items():
            status_icon = self._get_status_icon(container_info['status'])
            print(f"\n{status_icon} {container_key.upper()}")
            print(f"   상태:      {container_info['status'].upper()}")
            if container_info['status'] == 'running':
                print(f"   업타임:    {container_info['uptime_minutes']}분")

        # 서비스 상태
        print("\n\n🌐 서비스 가용성")
        print("-"*100)

        for service_name, service_info in status['services'].items():
            status_icon = "✅" if service_info['available'] else "❌"
            if service_info.get('url'):
                endpoint = service_info['url']
            elif service_info.get('port'):
                endpoint = f":{service_info['port']}"
            else:
                endpoint = "-"
            print(f"{status_icon} {service_name:15} ({endpoint}) - {'온라인' if service_info['available'] else '오프라인'}")

        print("\n" + "="*100)

    def _get_status_icon(self, status: str) -> str:
        """상태에 따른 아이콘 반환"""
        icons = {
            'running': '🟢',
            'stopped': '🔴',
            'error': '🟠',
            'unknown': '🟡',
            'not_found': '❓'
        }
        return icons.get(status, '❓')

    def start_process(self, process_name: str) -> bool:
        """프로세스 시작"""
        print(f"\n🚀 {process_name} 시작 중...")

        if process_name == 'price_scheduler':
            return self._start_price_scheduler()
        elif process_name == 'dashboard':
            return self._start_dashboard()
        elif process_name == 'trading_crew':
            return self._start_trading_crew()
        else:
            print(f"❌ 알 수 없는 프로세스: {process_name}")
            return False

    def _start_price_scheduler(self) -> bool:
        """Price Scheduler 시작"""
        try:
            script = PROJECT_ROOT / "paper_trading" / "price_scheduler.py"
            pid_file = PROJECT_ROOT / "system_monitor" / "price_scheduler.pid"

            # 기존 프로세스 확인
            if pid_file.exists():
                with open(pid_file, 'r') as f:
                    try:
                        old_pid = int(f.read().strip())
                        if psutil.pid_exists(old_pid):
                            print(f"   기존 프로세스 종료 (PID: {old_pid})")
                            os.kill(old_pid, signal.SIGTERM)
                            time.sleep(1)
                    except:
                        pass

            # 새 프로세스 시작
            process = subprocess.Popen(
                [sys.executable, str(script), "--schedule", "hourly"],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # PID 저장
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))

            print(f"✅ Price Scheduler 시작됨 (PID: {process.pid})")
            self.log(f"Price Scheduler 시작됨 (PID: {process.pid})")
            return True

        except Exception as e:
            print(f"❌ Price Scheduler 시작 실패: {e}")
            self.log(f"Price Scheduler 시작 실패: {e}")
            return False

    def _start_dashboard(self) -> bool:
        """Dashboard 시작"""
        try:
            script = PROJECT_ROOT / "paper_trading" / "dashboard.py"
            pid_file = PROJECT_ROOT / "system_monitor" / "dashboard.pid"

            # 기존 프로세스 확인
            if pid_file.exists():
                with open(pid_file, 'r') as f:
                    try:
                        old_pid = int(f.read().strip())
                        if psutil.pid_exists(old_pid):
                            print(f"   기존 프로세스 종료 (PID: {old_pid})")
                            os.kill(old_pid, signal.SIGTERM)
                            time.sleep(1)
                    except:
                        pass

            # 새 프로세스 시작
            process = subprocess.Popen(
                [sys.executable, str(script)],
                stdout=subprocess.DEVNULL,
                stderr=subprocess.DEVNULL,
                start_new_session=True
            )

            # PID 저장
            with open(pid_file, 'w') as f:
                f.write(str(process.pid))

            print(f"✅ Dashboard 시작됨 (PID: {process.pid})")
            self.log(f"Dashboard 시작됨 (PID: {process.pid})")
            return True

        except Exception as e:
            print(f"❌ Dashboard 시작 실패: {e}")
            self.log(f"Dashboard 시작 실패: {e}")
            return False

    def _start_trading_crew(self) -> bool:
        """Trading Crew 시작"""
        try:
            script = PROJECT_ROOT / "paper_trading" / "trading_crew.py"
            pid_file = PROJECT_ROOT / "system_monitor" / "trading_crew.pid"

            print("   Trading Crew는 일회성 워크플로우입니다.")
            print("   필요시 수동으로 실행하세요:")
            print(f"   python {script} --strategy ai --execute")
            return False

        except Exception as e:
            print(f"❌ Trading Crew 시작 실패: {e}")
            return False

    def stop_process(self, process_name: str) -> bool:
        """프로세스 종료"""
        print(f"\n⛔ {process_name} 종료 중...")

        pid_file = PROJECT_ROOT / "system_monitor" / f"{process_name}.pid"

        if not pid_file.exists():
            print(f"❌ PID 파일을 찾을 수 없습니다: {process_name}")
            return False

        try:
            with open(pid_file, 'r') as f:
                pid = int(f.read().strip())

            if psutil.pid_exists(pid):
                os.kill(pid, signal.SIGTERM)
                time.sleep(1)

                if psutil.pid_exists(pid):
                    os.kill(pid, signal.SIGKILL)

                print(f"✅ {process_name} 종료됨 (PID: {pid})")
                self.log(f"{process_name} 종료됨 (PID: {pid})")

                # PID 파일 삭제
                pid_file.unlink()
                return True
            else:
                print(f"⚠️  프로세스가 이미 종료됨")
                pid_file.unlink()
                return False

        except Exception as e:
            print(f"❌ {process_name} 종료 실패: {e}")
            self.log(f"{process_name} 종료 실패: {e}")
            return False

    def restart_process(self, process_name: str) -> bool:
        """프로세스 재시작"""
        print(f"\n🔄 {process_name} 재시작 중...")
        self.stop_process(process_name)
        time.sleep(2)
        return self.start_process(process_name)

    def start_docker_container(self, container_name: str) -> bool:
        """Docker 컨테이너 시작"""
        print(f"\n🐳 {container_name} 시작 중...")

        try:
            result = subprocess.run(
                ["docker", "start", container_name],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"✅ {container_name} 시작됨")
                self.log(f"{container_name} 시작됨")
                return True
            else:
                print(f"❌ {container_name} 시작 실패: {result.stderr}")
                self.log(f"{container_name} 시작 실패: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ {container_name} 시작 실패: {e}")
            self.log(f"{container_name} 시작 실패: {e}")
            return False

    def stop_docker_container(self, container_name: str) -> bool:
        """Docker 컨테이너 종료"""
        print(f"\n🐳 {container_name} 종료 중...")

        try:
            result = subprocess.run(
                ["docker", "stop", container_name],
                capture_output=True,
                text=True,
                timeout=10
            )

            if result.returncode == 0:
                print(f"✅ {container_name} 종료됨")
                self.log(f"{container_name} 종료됨")
                return True
            else:
                print(f"❌ {container_name} 종료 실패: {result.stderr}")
                self.log(f"{container_name} 종료 실패: {result.stderr}")
                return False

        except Exception as e:
            print(f"❌ {container_name} 종료 실패: {e}")
            self.log(f"{container_name} 종료 실패: {e}")
            return False


def main():
    """메인 함수"""
    import argparse

    monitor = SystemMonitor()

    parser = argparse.ArgumentParser(
        description="시스템 프로세스 모니터링 및 관리 도구",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
예시:
  python system_monitor.py status              # 상태 확인
  python system_monitor.py start price_scheduler  # 프로세스 시작
  python system_monitor.py restart dashboard      # 프로세스 재시작
  python system_monitor.py docker-start investment_db  # Docker 시작
        """
    )

    parser.add_argument(
        'command',
        choices=['status', 'start', 'stop', 'restart', 'docker-start', 'docker-stop', 'health'],
        help='실행할 명령어'
    )

    parser.add_argument(
        'process',
        nargs='?',
        help='프로세스/컨테이너 이름 (status는 불필요)'
    )

    args = parser.parse_args()

    if args.command == 'status':
        monitor.display_dashboard()

    elif args.command == 'start':
        if not args.process:
            print("❌ 프로세스 이름을 지정하세요")
            sys.exit(1)
        monitor.start_process(args.process)

    elif args.command == 'stop':
        if not args.process:
            print("❌ 프로세스 이름을 지정하세요")
            sys.exit(1)
        monitor.stop_process(args.process)

    elif args.command == 'restart':
        if not args.process:
            print("❌ 프로세스 이름을 지정하세요")
            sys.exit(1)
        monitor.restart_process(args.process)

    elif args.command == 'docker-start':
        if not args.process:
            print("❌ 컨테이너 이름을 지정하세요")
            sys.exit(1)
        monitor.start_docker_container(args.process)

    elif args.command == 'docker-stop':
        if not args.process:
            print("❌ 컨테이너 이름을 지정하세요")
            sys.exit(1)
        monitor.stop_docker_container(args.process)

    elif args.command == 'health':
        print("🏥 시스템 상태 점검 중...")
        status = monitor.get_all_status()

        # 문제가 있는 항목 표시
        issues = []

        for proc_key, proc_info in status['python_processes'].items():
            if proc_info['status'] != 'running':
                issues.append((proc_key, "Python 프로세스", proc_info['status']))

        for container_key, container_info in status['docker_containers'].items():
            if container_info['status'] != 'running':
                issues.append((container_key, "Docker", container_info['status']))

        for service_name, service_info in status['services'].items():
            if not service_info['available']:
                issues.append((service_name, "서비스", "unavailable"))

        if issues:
            print(f"\n⚠️  {len(issues)}개의 문제 발견:\n")
            for name, type_, status_ in issues:
                print(f"  • {name:20} ({type_:10}): {status_}")
            sys.exit(1)
        else:
            print("\n✅ 모든 시스템이 정상입니다!")
            sys.exit(0)


if __name__ == "__main__":
    main()
