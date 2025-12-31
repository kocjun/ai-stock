#!/usr/bin/env python3
"""
투자 룰 관리자 (Investment Rule Manager)

투자 룰 CRUD 및 관리 기능 제공
- 룰 추가, 조회, 수정, 삭제
- 룰 활성화/비활성화
- 룰 검증 및 테스트

사용 예시:
    # 텍스트로 룰 추가
    python rule_manager.py add "KODEX 200: 월 70만원 DCA"

    # 룰 목록 조회
    python rule_manager.py list

    # 룰 활성화/비활성화
    python rule_manager.py toggle 1

    # 룰 삭제
    python rule_manager.py delete 1
"""

import sys
import os
import argparse
import json
from typing import List, Dict, Optional, Any
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.utils.db_utils import get_db_connection
from paper_trading.rule_parser import InvestmentRuleParser


class InvestmentRuleManager:
    """투자 룰 관리자"""

    def __init__(self):
        self.parser = InvestmentRuleParser(use_llm=False)  # 정규식 모드로 시작

    def add_rule(self, rule_text: str, account_id: int = 1) -> int:
        """
        투자 룰 추가

        Args:
            rule_text: 투자 룰 텍스트
            account_id: 적용할 계좌 ID (기본값: 1)

        Returns:
            생성된 rule_id
        """
        print(f"\n📝 투자 룰 추가")
        print(f"입력: {rule_text}")
        print("-" * 70)

        # 1. 파싱
        try:
            rule_dict = self.parser.parse(rule_text)
            print(f"✅ 파싱 성공")
            print(json.dumps(rule_dict, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ 파싱 실패: {e}")
            raise

        # 2. DB에 저장
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                # 종목 코드 확인 (있으면)
                if rule_dict.get('target_code'):
                    cur.execute(
                        "SELECT code FROM stocks WHERE code = %s",
                        (rule_dict['target_code'],)
                    )
                    if not cur.fetchone():
                        print(f"⚠️  종목 코드 {rule_dict['target_code']}가 stocks 테이블에 없습니다. NULL로 저장합니다.")
                        rule_dict['target_code'] = None

                # INSERT
                cur.execute("""
                    INSERT INTO investment_rules (
                        rule_name, rule_type, asset_category,
                        target_code, target_name,
                        conditions, actions,
                        schedule_type, schedule_params,
                        target_weight_min, target_weight_max,
                        priority, is_active
                    ) VALUES (
                        %(rule_name)s, %(rule_type)s, %(asset_category)s,
                        %(target_code)s, %(target_name)s,
                        %(conditions)s::jsonb, %(actions)s::jsonb,
                        %(schedule_type)s, %(schedule_params)s::jsonb,
                        %(target_weight_min)s, %(target_weight_max)s,
                        %(priority)s, true
                    )
                    RETURNING rule_id
                """, {
                    'rule_name': rule_dict['rule_name'],
                    'rule_type': rule_dict['rule_type'],
                    'asset_category': rule_dict['asset_category'],
                    'target_code': rule_dict.get('target_code'),
                    'target_name': rule_dict.get('target_name'),
                    'conditions': json.dumps(rule_dict['conditions']),
                    'actions': json.dumps(rule_dict['actions']),
                    'schedule_type': rule_dict.get('schedule_type'),
                    'schedule_params': json.dumps(rule_dict.get('schedule_params') or {}),
                    'target_weight_min': rule_dict.get('target_weight_min'),
                    'target_weight_max': rule_dict.get('target_weight_max'),
                    'priority': rule_dict.get('priority', 100)
                })

                rule_id = cur.fetchone()[0]
                conn.commit()

        print(f"\n✅ 룰 추가 완료 (ID: {rule_id})")
        return rule_id

    def list_rules(self, active_only: bool = True) -> List[Dict[str, Any]]:
        """
        투자 룰 목록 조회

        Args:
            active_only: 활성화된 룰만 조회 (기본값: True)

        Returns:
            룰 목록
        """
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                if active_only:
                    cur.execute("""
                        SELECT
                            rule_id, rule_name, rule_type, asset_category,
                            target_code, target_name,
                            conditions, actions, schedule_type, priority, is_active,
                            created_at
                        FROM investment_rules
                        WHERE is_active = true
                        ORDER BY priority, rule_id
                    """)
                else:
                    cur.execute("""
                        SELECT
                            rule_id, rule_name, rule_type, asset_category,
                            target_code, target_name,
                            conditions, actions, schedule_type, priority, is_active,
                            created_at
                        FROM investment_rules
                        ORDER BY priority, rule_id
                    """)

                rows = cur.fetchall()

        rules = []
        for row in rows:
            rules.append({
                'rule_id': row[0],
                'rule_name': row[1],
                'rule_type': row[2],
                'asset_category': row[3],
                'target_code': row[4],
                'target_name': row[5],
                'conditions': row[6],
                'actions': row[7],
                'schedule_type': row[8],
                'priority': row[9],
                'is_active': row[10],
                'created_at': row[11]
            })

        return rules

    def get_rule(self, rule_id: int) -> Optional[Dict[str, Any]]:
        """특정 룰 조회"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT
                        rule_id, rule_name, rule_type, asset_category,
                        target_code, target_name,
                        conditions, actions, schedule_type, schedule_params,
                        target_weight_min, target_weight_max,
                        priority, is_active, created_at, updated_at
                    FROM investment_rules
                    WHERE rule_id = %s
                """, (rule_id,))

                row = cur.fetchone()
                if not row:
                    return None

                return {
                    'rule_id': row[0],
                    'rule_name': row[1],
                    'rule_type': row[2],
                    'asset_category': row[3],
                    'target_code': row[4],
                    'target_name': row[5],
                    'conditions': row[6],
                    'actions': row[7],
                    'schedule_type': row[8],
                    'schedule_params': row[9],
                    'target_weight_min': row[10],
                    'target_weight_max': row[11],
                    'priority': row[12],
                    'is_active': row[13],
                    'created_at': row[14],
                    'updated_at': row[15]
                }

    def toggle_rule(self, rule_id: int) -> bool:
        """룰 활성화/비활성화 토글"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    UPDATE investment_rules
                    SET is_active = NOT is_active
                    WHERE rule_id = %s
                    RETURNING is_active
                """, (rule_id,))

                result = cur.fetchone()
                if not result:
                    return False

                new_status = result[0]
                conn.commit()

                status_text = "활성화" if new_status else "비활성화"
                print(f"✅ 룰 {rule_id} {status_text} 완료")
                return True

    def delete_rule(self, rule_id: int) -> bool:
        """룰 삭제"""
        with get_db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    DELETE FROM investment_rules
                    WHERE rule_id = %s
                    RETURNING rule_id
                """, (rule_id,))

                result = cur.fetchone()
                if not result:
                    return False

                conn.commit()
                print(f"✅ 룰 {rule_id} 삭제 완료")
                return True

    def print_rules(self, rules: List[Dict[str, Any]]):
        """룰 목록 출력"""
        if not rules:
            print("📭 등록된 룰이 없습니다.")
            return

        print(f"\n📋 투자 룰 목록 ({len(rules)}개)")
        print("=" * 120)

        for rule in rules:
            status = "🟢" if rule['is_active'] else "⚫"
            print(f"{status} [{rule['rule_id']}] {rule['rule_name']}")
            print(f"   타입: {rule['rule_type']} | 카테고리: {rule['asset_category']} | 우선순위: {rule['priority']}")
            if rule['target_name']:
                print(f"   대상: {rule['target_name']} ({rule.get('target_code', 'N/A')})")

            # 조건
            conditions = rule.get('conditions', {})
            if isinstance(conditions, str):
                conditions = json.loads(conditions)
            print(f"   조건: {json.dumps(conditions, ensure_ascii=False)}")

            # 액션
            actions = rule.get('actions', {})
            if isinstance(actions, str):
                actions = json.loads(actions)
            print(f"   액션: {json.dumps(actions, ensure_ascii=False)}")

            # 스케줄
            if rule.get('schedule_type'):
                print(f"   스케줄: {rule['schedule_type']}")

            print(f"   생성일: {rule['created_at']}")
            print("-" * 120)


# ============================================================
# CLI 인터페이스
# ============================================================

def main():
    parser = argparse.ArgumentParser(
        description="투자 룰 관리자",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
사용 예시:
  # 텍스트로 룰 추가
  python rule_manager.py add "KODEX 200: 월 70만원 DCA (1주차 50%, 2-3주차 30%, 마지막주 20%)"

  # 룰 목록 조회
  python rule_manager.py list

  # 특정 룰 상세 조회
  python rule_manager.py show 1

  # 룰 활성화/비활성화
  python rule_manager.py toggle 1

  # 룰 삭제
  python rule_manager.py delete 1

  # 파일에서 룰 일괄 추가
  python rule_manager.py import rules.txt
        """
    )

    subparsers = parser.add_subparsers(dest='command', help='명령어')

    # add 명령어
    add_parser = subparsers.add_parser('add', help='룰 추가')
    add_parser.add_argument('rule_text', type=str, help='투자 룰 텍스트')

    # list 명령어
    list_parser = subparsers.add_parser('list', help='룰 목록 조회')
    list_parser.add_argument('--all', action='store_true', help='비활성화된 룰도 포함')

    # show 명령어
    show_parser = subparsers.add_parser('show', help='룰 상세 조회')
    show_parser.add_argument('rule_id', type=int, help='룰 ID')

    # toggle 명령어
    toggle_parser = subparsers.add_parser('toggle', help='룰 활성화/비활성화')
    toggle_parser.add_argument('rule_id', type=int, help='룰 ID')

    # delete 명령어
    delete_parser = subparsers.add_parser('delete', help='룰 삭제')
    delete_parser.add_argument('rule_id', type=int, help='룰 ID')

    # import 명령어
    import_parser = subparsers.add_parser('import', help='파일에서 룰 일괄 추가')
    import_parser.add_argument('file_path', type=str, help='룰 파일 경로')

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    # 룰 매니저 초기화
    manager = InvestmentRuleManager()

    # 명령어 실행
    if args.command == 'add':
        try:
            rule_id = manager.add_rule(args.rule_text)
            print(f"\n✅ 성공: 룰 ID {rule_id}")
        except Exception as e:
            print(f"\n❌ 실패: {e}")
            sys.exit(1)

    elif args.command == 'list':
        rules = manager.list_rules(active_only=not args.all)
        manager.print_rules(rules)

    elif args.command == 'show':
        rule = manager.get_rule(args.rule_id)
        if rule:
            print(json.dumps(rule, ensure_ascii=False, indent=2, default=str))
        else:
            print(f"❌ 룰 ID {args.rule_id}를 찾을 수 없습니다.")
            sys.exit(1)

    elif args.command == 'toggle':
        if not manager.toggle_rule(args.rule_id):
            print(f"❌ 룰 ID {args.rule_id}를 찾을 수 없습니다.")
            sys.exit(1)

    elif args.command == 'delete':
        if not manager.delete_rule(args.rule_id):
            print(f"❌ 룰 ID {args.rule_id}를 찾을 수 없습니다.")
            sys.exit(1)

    elif args.command == 'import':
        from paper_trading.rule_parser import parse_rule_file
        try:
            rules = parse_rule_file(args.file_path)
            print(f"📄 파일에서 {len(rules)}개 룰 파싱 완료")

            for i, rule in enumerate(rules, 1):
                print(f"\n[{i}/{len(rules)}] {rule['rule_name']}")
                try:
                    rule_text = f"{rule['target_name']}: {rule['rule_name']}"
                    manager.add_rule(rule_text)
                except Exception as e:
                    print(f"⚠️  실패: {e}")

        except Exception as e:
            print(f"❌ 파일 읽기 실패: {e}")
            sys.exit(1)


if __name__ == "__main__":
    main()
