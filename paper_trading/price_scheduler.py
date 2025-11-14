"""
가격 업데이트 스케줄러

APScheduler를 이용하여 정기적으로 가격 데이터를 수집합니다.
매일 장 마감 후(15:40) 자동으로 가격을 업데이트합니다.
"""

import sys
from pathlib import Path
from datetime import datetime
import logging
import time

# 프로젝트 루트 경로 추가
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger

# 같은 디렉토리의 모듈들 import
sys.path.insert(0, str(Path(__file__).parent))

import price_updater

# 로깅 설정
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('/Users/yeongchang.jeon/workspace/ai-agent/paper_trading/logs/price_scheduler.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class PriceUpdateScheduler:
    """가격 업데이트 스케줄러"""

    def __init__(self):
        self.scheduler = BackgroundScheduler(daemon=True)
        logger.info("가격 업데이트 스케줄러 초기화 완료")

    def schedule_daily_update(self):
        """
        매일 장 마감 후(15:40) 가격 업데이트 작업 스케줄링

        스케줄:
        - 월~금 15:40 (한국 거래소 장 마감 후)
        """
        self.scheduler.add_job(
            func=self._run_price_update,
            trigger=CronTrigger(hour=15, minute=40, day_of_week='mon-fri'),
            id='daily_price_update',
            name='Daily Price Update (weekdays at 15:40)',
            replace_existing=True,
            misfire_grace_time=300  # 300초(5분) 내에 실행되지 않았으면 건너뜀
        )
        logger.info("일일 가격 업데이트 작업 스케줄 등록 (평일 15:40)")

    def schedule_hourly_update(self):
        """
        매 시간 가격 업데이트 (테스트/개발용)
        """
        self.scheduler.add_job(
            func=self._run_price_update,
            trigger=CronTrigger(minute=0),  # 매 시간 정각
            id='hourly_price_update',
            name='Hourly Price Update',
            replace_existing=True,
            misfire_grace_time=60
        )
        logger.info("시간별 가격 업데이트 작업 스케줄 등록 (매 시간 정각)")

    def schedule_market_hours_update(self):
        """
        장 운영 시간 동안 30분마다 업데이트 (09:00 ~ 16:00)
        """
        self.scheduler.add_job(
            func=self._run_price_update,
            trigger=CronTrigger(hour='9-16', minute='*/30'),
            id='market_hours_update',
            name='Market Hours Update (every 30min)',
            replace_existing=True,
            misfire_grace_time=60
        )
        logger.info("장 운영 시간 가격 업데이트 작업 스케줄 등록 (09:00~16:00, 30분 간격)")

    def _run_price_update(self):
        """가격 업데이트 실행"""
        try:
            logger.info("=" * 60)
            logger.info("가격 업데이트 작업 시작")
            logger.info("=" * 60)

            result = price_updater.run_price_update(account_id=1)

            if result.get('status') == 'success':
                logger.info(f"✓ 가격 업데이트 성공")
                logger.info(f"  - 업데이트 종목: {result.get('updated_count', 0)}개")
                logger.info(f"  - 포트폴리오 가치: ₩{result.get('stock_value', 0):,.0f}")
                logger.info(f"  - 평가 손익: ₩{result.get('total_profit_loss', 0):,.0f}")
            else:
                logger.warning(f"⚠️  가격 업데이트 부분 완료 또는 실패")
                logger.warning(f"  상태: {result.get('status', 'unknown')}")

            logger.info("=" * 60)

        except Exception as e:
            logger.error(f"❌ 가격 업데이트 작업 실패: {e}", exc_info=True)

    def start(self):
        """스케줄러 시작"""
        if self.scheduler.running:
            logger.warning("스케줄러가 이미 실행 중입니다")
            return

        self.scheduler.start()
        logger.info("스케줄러 시작 완료")
        logger.info(f"예약된 작업:")
        for job in self.scheduler.get_jobs():
            logger.info(f"  - {job.id}: {job.name}")

    def stop(self):
        """스케줄러 종료"""
        if not self.scheduler.running:
            logger.warning("스케줄러가 실행 중이 아닙니다")
            return

        self.scheduler.shutdown(wait=True)
        logger.info("스케줄러 종료 완료")

    def get_jobs(self):
        """예약된 작업 목록 조회"""
        return self.scheduler.get_jobs()

    def is_running(self):
        """스케줄러 실행 상태 조회"""
        return self.scheduler.running


def run_scheduler(schedule_type='daily'):
    """
    스케줄러 실행 (메인 함수)

    Args:
        schedule_type: 스케줄 타입
            - 'daily': 일일 (평일 15:40) - 기본값
            - 'hourly': 시간별 (매 시간 정각) - 테스트용
            - 'market': 장 운영 시간 (09:00~16:00, 30분 간격) - 개발용
    """
    scheduler = PriceUpdateScheduler()

    # 스케줄 타입별 설정
    if schedule_type == 'daily':
        scheduler.schedule_daily_update()
    elif schedule_type == 'hourly':
        scheduler.schedule_hourly_update()
    elif schedule_type == 'market':
        scheduler.schedule_market_hours_update()
    else:
        logger.warning(f"알 수 없는 스케줄 타입: {schedule_type}, 기본 일일 스케줄 사용")
        scheduler.schedule_daily_update()

    # 스케줄러 시작
    scheduler.start()

    logger.info("=" * 60)
    logger.info("가격 업데이트 스케줄러 시작")
    logger.info("=" * 60)
    logger.info(f"스케줄 타입: {schedule_type}")
    logger.info(f"시작 시간: {datetime.now()}")
    logger.info("스케줄러가 백그라운드에서 실행 중입니다...")
    logger.info("프로세스를 종료하려면 Ctrl+C를 누르세요")
    logger.info("=" * 60)

    try:
        # 스케줄러 유지
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("스케줄러 중지 요청")
        scheduler.stop()
        logger.info("스케줄러 종료 완료")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description='가격 업데이트 스케줄러')
    parser.add_argument(
        '--schedule',
        type=str,
        choices=['daily', 'hourly', 'market'],
        default='daily',
        help='스케줄 타입 (기본: daily)'
    )

    args = parser.parse_args()

    run_scheduler(schedule_type=args.schedule)
