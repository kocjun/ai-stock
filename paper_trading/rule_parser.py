#!/usr/bin/env python3
"""
투자 룰 파서 (Investment Rule Parser)

텍스트 기반 투자 룰을 구조화된 데이터로 변환합니다.
- LLM 기반 자연어 파싱
- 정규식 보완 파싱
- Pydantic 검증

사용 예시:
    parser = InvestmentRuleParser()
    rule_text = "KODEX 200: 월 70만원 정기 매수 (1주차 50%, 2-3주차 30%, 마지막주 20%)"
    rule_dict = parser.parse(rule_text)
"""

import sys
import os
import re
import json
from typing import Dict, List, Optional, Any
from datetime import datetime

# 프로젝트 루트를 Python 경로에 추가
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from pydantic import BaseModel, Field, validator
from core.utils.llm_utils import build_llm


# ============================================================
# Pydantic 모델 정의
# ============================================================

class InvestmentCondition(BaseModel):
    """투자 룰 조건"""
    trigger: str = Field(..., description="트리거 유형 (monthly, price_change, weight_check 등)")
    threshold: Optional[float] = Field(None, description="임계값 (예: -10.0, 15.0)")
    comparison: Optional[str] = Field(None, description="비교 연산자 (<=, >=, ==)")
    reference: Optional[str] = Field(None, description="참조 기준 (avg_price, buy_price, target_weight)")
    always_execute: bool = Field(False, description="무조건 실행 여부 (DCA용)")

    class Config:
        json_schema_extra = {
            "example": {
                "trigger": "price_change",
                "threshold": -10.0,
                "comparison": "<=",
                "reference": "avg_price",
                "always_execute": False
            }
        }


class InvestmentAction(BaseModel):
    """투자 룰 액션"""
    action: str = Field(..., description="액션 유형 (buy, sell)")
    amount_type: str = Field(..., description="금액 유형 (fixed, percentage, ratio)")
    amount_value: float = Field(..., description="금액 또는 비율 값")
    ratio: float = Field(1.0, description="실행 비율 (0.0~1.0)")

    @validator('amount_type')
    def validate_amount_type(cls, v):
        allowed = ['fixed', 'percentage', 'ratio']
        if v not in allowed:
            raise ValueError(f"amount_type must be one of {allowed}")
        return v

    @validator('action')
    def validate_action(cls, v):
        allowed = ['buy', 'sell']
        if v not in allowed:
            raise ValueError(f"action must be one of {allowed}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "action": "buy",
                "amount_type": "fixed",
                "amount_value": 700000,
                "ratio": 1.0
            }
        }


class ScheduleParams(BaseModel):
    """스케줄 파라미터"""
    weeks: Optional[List[int]] = Field(None, description="주차 리스트 (1, 2, 3, 4)")
    ratios: Optional[List[float]] = Field(None, description="비율 리스트 (50, 30, 20)")
    day_of_week: Optional[int] = Field(None, description="요일 (0=월요일, 6=일요일)")
    time: Optional[str] = Field(None, description="실행 시간 (HH:MM)")

    class Config:
        json_schema_extra = {
            "example": {
                "weeks": [1, 2, 3, 4],
                "ratios": [50, 30, 20]
            }
        }


class InvestmentRuleModel(BaseModel):
    """투자 룰 전체 모델"""
    rule_name: str = Field(..., description="룰 이름")
    rule_type: str = Field(..., description="룰 타입 (DCA, SIGNAL, REBALANCE, STOP_LOSS, TAKE_PROFIT)")
    asset_category: str = Field(..., description="자산 카테고리 (CORE, SATELLITE, DEFENSE, CASH)")
    target_code: Optional[str] = Field(None, description="대상 종목 코드")
    target_name: Optional[str] = Field(None, description="대상 종목명")

    conditions: InvestmentCondition
    actions: InvestmentAction

    schedule_type: Optional[str] = Field(None, description="스케줄 타입")
    schedule_params: Optional[ScheduleParams] = Field(None, description="스케줄 파라미터")

    target_weight_min: Optional[float] = Field(None, description="목표 비중 최소값 (%)")
    target_weight_max: Optional[float] = Field(None, description="목표 비중 최대값 (%)")

    priority: int = Field(100, description="실행 우선순위 (낮을수록 먼저 실행)")

    @validator('rule_type')
    def validate_rule_type(cls, v):
        allowed = ['DCA', 'SIGNAL', 'REBALANCE', 'STOP_LOSS', 'TAKE_PROFIT']
        if v not in allowed:
            raise ValueError(f"rule_type must be one of {allowed}")
        return v

    @validator('asset_category')
    def validate_asset_category(cls, v):
        allowed = ['CORE', 'SATELLITE', 'DEFENSE', 'CASH']
        if v not in allowed:
            raise ValueError(f"asset_category must be one of {allowed}")
        return v

    class Config:
        json_schema_extra = {
            "example": {
                "rule_name": "KODEX 200 월 70만원 DCA",
                "rule_type": "DCA",
                "asset_category": "CORE",
                "target_code": "069500",
                "target_name": "KODEX 200",
                "conditions": {
                    "trigger": "monthly",
                    "always_execute": True
                },
                "actions": {
                    "action": "buy",
                    "amount_type": "fixed",
                    "amount_value": 700000,
                    "ratio": 1.0
                },
                "schedule_type": "MONTHLY_SPLIT",
                "schedule_params": {
                    "weeks": [1, 2, 3, 4],
                    "ratios": [50, 30, 20]
                },
                "priority": 10
            }
        }


# ============================================================
# 투자 룰 파서 클래스
# ============================================================

class InvestmentRuleParser:
    """투자 룰 파서"""

    def __init__(self, use_llm: bool = True):
        """
        Args:
            use_llm: LLM 사용 여부 (False면 정규식만 사용)
        """
        self.use_llm = use_llm
        if use_llm:
            try:
                self.llm = build_llm()
            except Exception as e:
                print(f"⚠️  LLM 초기화 실패, 정규식 모드로 전환: {e}")
                self.use_llm = False

    def parse(self, rule_text: str) -> Dict[str, Any]:
        """
        투자 룰 텍스트를 파싱하여 구조화된 딕셔너리로 변환

        Args:
            rule_text: 투자 룰 텍스트

        Returns:
            검증된 투자 룰 딕셔너리

        Example:
            >>> parser = InvestmentRuleParser()
            >>> rule = parser.parse("KODEX 200: 월 70만원 DCA (1주차 50%, 2-3주차 30%, 마지막주 20%)")
            >>> print(rule['rule_type'])
            'DCA'
        """
        # Step 1: 정규식 기반 파싱 (기본 정보 추출)
        regex_result = self._parse_with_regex(rule_text)

        # Step 2: LLM 기반 파싱 (자연어 이해)
        if self.use_llm:
            try:
                llm_result = self._parse_with_llm(rule_text, regex_result)
                # LLM 결과와 정규식 결과 병합
                final_result = {**regex_result, **llm_result}
            except Exception as e:
                print(f"⚠️  LLM 파싱 실패, 정규식 결과 사용: {e}")
                final_result = regex_result
        else:
            final_result = regex_result

        # Step 3: Pydantic 검증
        validated_rule = self._validate_rule(final_result)

        return validated_rule

    def _parse_with_regex(self, rule_text: str) -> Dict[str, Any]:
        """정규식 기반 파싱"""
        result = {}

        # 1. 종목명 추출 (콜론 앞)
        name_match = re.search(r'^([^:：]+)', rule_text)
        if name_match:
            result['target_name'] = name_match.group(1).strip()

        # 2. 금액 추출 (예: "월 70만원", "700000원")
        amount_patterns = [
            r'월\s*(\d+)만원',  # 월 70만원
            r'(\d+)만원',       # 70만원
            r'(\d{5,})원',      # 700000원
            r'(\d+,\d+)원',     # 700,000원
        ]
        for pattern in amount_patterns:
            match = re.search(pattern, rule_text)
            if match:
                amount_str = match.group(1).replace(',', '')
                if '만원' in match.group(0):
                    result['amount_value'] = int(amount_str) * 10000
                else:
                    result['amount_value'] = int(amount_str)
                break

        # 3. 변동률 추출 (예: "-10%", "+15%")
        change_patterns = r'([\+\-]?\d+(?:\.\d+)?)%'
        changes = re.findall(change_patterns, rule_text)
        if changes:
            result['price_changes'] = [float(c) for c in changes]

        # 4. 주차 및 비율 추출 (예: "1주차 50%, 2-3주차 30%, 마지막주 20%")
        week_ratio_pattern = r'(\d+)(?:-\d+)?주차\s*(\d+)%'
        week_ratios = re.findall(week_ratio_pattern, rule_text)
        if week_ratios:
            weeks = []
            ratios = []
            for week, ratio in week_ratios:
                weeks.append(int(week))
                ratios.append(float(ratio))
            result['schedule_weeks'] = weeks
            result['schedule_ratios'] = ratios

        # 마지막주 처리
        if '마지막주' in rule_text:
            last_week_match = re.search(r'마지막주\s*(\d+)%', rule_text)
            if last_week_match:
                if 'schedule_weeks' not in result:
                    result['schedule_weeks'] = []
                    result['schedule_ratios'] = []
                result['schedule_weeks'].append(4)  # 마지막주 = 4주차
                result['schedule_ratios'].append(float(last_week_match.group(1)))

        # 5. 키워드 기반 룰 타입 추정
        rule_text_lower = rule_text.lower()

        if any(kw in rule_text_lower for kw in ['dca', '정기', '월', '매수', '분할']):
            result['rule_type_hint'] = 'DCA'
            result['asset_category_hint'] = 'CORE'

        if any(kw in rule_text_lower for kw in ['하락', '급락', '-', '매수 신호']):
            result['rule_type_hint'] = 'SIGNAL'
            result['asset_category_hint'] = 'SATELLITE'

        if any(kw in rule_text_lower for kw in ['익절', '상승', '+', '매도']):
            result['rule_type_hint'] = 'TAKE_PROFIT'

        if any(kw in rule_text_lower for kw in ['손절', '하락', '청산']):
            result['rule_type_hint'] = 'STOP_LOSS'

        # 6. 자산 카테고리 힌트
        if any(kw in rule_text for kw in ['KODEX 200', 'TIGER S&P', '고배당']):
            result['asset_category_hint'] = 'CORE'
        if any(kw in rule_text for kw in ['코스닥', '반도체', '테마']):
            result['asset_category_hint'] = 'SATELLITE'
        if any(kw in rule_text for kw in ['단기채', '현금', 'MMF', 'CMA']):
            result['asset_category_hint'] = 'DEFENSE'

        return result

    def _parse_with_llm(self, rule_text: str, regex_result: Dict) -> Dict[str, Any]:
        """LLM 기반 자연어 파싱"""
        from langchain.prompts import PromptTemplate

        prompt_template = PromptTemplate(
            input_variables=["rule_text", "regex_hints"],
            template="""다음 투자 룰을 분석하여 JSON 형식으로 변환하세요.

투자 룰: {rule_text}

정규식 분석 결과 (참고용): {regex_hints}

출력 형식 (JSON만 출력, 다른 텍스트 없이):
{{
  "rule_name": "룰의 간결한 이름",
  "rule_type": "DCA | SIGNAL | REBALANCE | STOP_LOSS | TAKE_PROFIT",
  "asset_category": "CORE | SATELLITE | DEFENSE | CASH",
  "target_name": "종목명 또는 ETF명",
  "condition_trigger": "조건 트리거 (monthly, price_change, weight_check 등)",
  "condition_threshold": 숫자 (변동률 등, 없으면 null),
  "condition_comparison": "비교 연산자 (<=, >=, ==, 없으면 null)",
  "condition_reference": "참조 기준 (avg_price, buy_price, target_weight 등)",
  "condition_always_execute": true/false,
  "action": "buy | sell",
  "amount_type": "fixed | percentage | ratio",
  "amount_value": 금액 또는 비율 값,
  "schedule_type": "MONTHLY_SPLIT | FIXED_DATE | REALTIME | DAILY | null",
  "priority": 우선순위 숫자 (10-100, DCA는 10, 신호형은 30-50)
}}

규칙:
1. DCA 룰이면 condition_always_execute = true
2. 신호형 룰이면 condition_threshold에 변동률 입력
3. amount_type: 고정 금액이면 "fixed", 비율이면 "percentage"
4. 월 분할 매수면 schedule_type = "MONTHLY_SPLIT"
5. 실시간 모니터링이면 schedule_type = "REALTIME"
"""
        )

        # LLM 호출
        chain = prompt_template | self.llm
        response = chain.invoke({
            "rule_text": rule_text,
            "regex_hints": json.dumps(regex_result, ensure_ascii=False, indent=2)
        })

        # JSON 추출
        content = response.content if hasattr(response, 'content') else str(response)

        # JSON 블록 추출
        json_match = re.search(r'\{[\s\S]*\}', content)
        if not json_match:
            raise ValueError("LLM 응답에서 JSON을 찾을 수 없습니다")

        llm_result = json.loads(json_match.group(0))

        # LLM 결과를 내부 구조에 맞게 변환
        converted = {}

        if 'rule_name' in llm_result:
            converted['rule_name'] = llm_result['rule_name']
        if 'rule_type' in llm_result:
            converted['rule_type'] = llm_result['rule_type']
        if 'asset_category' in llm_result:
            converted['asset_category'] = llm_result['asset_category']
        if 'target_name' in llm_result:
            converted['target_name'] = llm_result['target_name']
        if 'priority' in llm_result:
            converted['priority'] = int(llm_result['priority'])

        # 조건 변환
        converted['conditions'] = {
            'trigger': llm_result.get('condition_trigger', 'monthly'),
            'threshold': llm_result.get('condition_threshold'),
            'comparison': llm_result.get('condition_comparison'),
            'reference': llm_result.get('condition_reference'),
            'always_execute': llm_result.get('condition_always_execute', False)
        }

        # 액션 변환
        converted['actions'] = {
            'action': llm_result.get('action', 'buy'),
            'amount_type': llm_result.get('amount_type', 'fixed'),
            'amount_value': regex_result.get('amount_value', llm_result.get('amount_value', 0)),
            'ratio': 1.0
        }

        # 스케줄 변환
        if llm_result.get('schedule_type'):
            converted['schedule_type'] = llm_result['schedule_type']

            if 'schedule_weeks' in regex_result and 'schedule_ratios' in regex_result:
                converted['schedule_params'] = {
                    'weeks': regex_result['schedule_weeks'],
                    'ratios': regex_result['schedule_ratios']
                }

        return converted

    def _validate_rule(self, rule_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Pydantic를 사용한 룰 검증"""
        # 기본값 설정
        if 'rule_name' not in rule_dict and 'target_name' in rule_dict:
            rule_name = rule_dict['target_name']
            if rule_dict.get('rule_type') == 'DCA':
                amount = rule_dict.get('actions', {}).get('amount_value', 0)
                rule_name = f"{rule_name} 월 {amount//10000}만원 DCA"
            rule_dict['rule_name'] = rule_name

        if 'rule_type' not in rule_dict:
            rule_dict['rule_type'] = rule_dict.get('rule_type_hint', 'DCA')

        if 'asset_category' not in rule_dict:
            rule_dict['asset_category'] = rule_dict.get('asset_category_hint', 'CORE')

        if 'conditions' not in rule_dict:
            rule_dict['conditions'] = {
                'trigger': 'monthly',
                'always_execute': True
            }

        if 'actions' not in rule_dict:
            rule_dict['actions'] = {
                'action': 'buy',
                'amount_type': 'fixed',
                'amount_value': rule_dict.get('amount_value', 0),
                'ratio': 1.0
            }

        # Pydantic 검증
        try:
            validated_model = InvestmentRuleModel(**rule_dict)
            return validated_model.dict()
        except Exception as e:
            print(f"❌ 룰 검증 실패: {e}")
            print(f"입력 데이터: {json.dumps(rule_dict, ensure_ascii=False, indent=2)}")
            raise


# ============================================================
# 헬퍼 함수
# ============================================================

def parse_rule_file(file_path: str) -> List[Dict[str, Any]]:
    """
    룰 파일에서 여러 개의 투자 룰 파싱

    Args:
        file_path: 룰 텍스트 파일 경로

    Returns:
        파싱된 룰 리스트
    """
    parser = InvestmentRuleParser()
    rules = []

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    current_rule = ""
    for line in lines:
        line = line.strip()
        if not line or line.startswith('#'):
            continue

        # 새로운 룰 시작 (숫자. 또는 - 로 시작)
        if re.match(r'^\d+\.|^-\s', line):
            if current_rule:
                try:
                    rule = parser.parse(current_rule)
                    rules.append(rule)
                except Exception as e:
                    print(f"⚠️  룰 파싱 실패: {current_rule[:50]}... - {e}")
            current_rule = re.sub(r'^\d+\.\s*|-\s*', '', line)
        else:
            current_rule += " " + line

    # 마지막 룰 처리
    if current_rule:
        try:
            rule = parser.parse(current_rule)
            rules.append(rule)
        except Exception as e:
            print(f"⚠️  룰 파싱 실패: {current_rule[:50]}... - {e}")

    return rules


# ============================================================
# 메인 실행 (테스트용)
# ============================================================

if __name__ == "__main__":
    print("=" * 70)
    print("투자 룰 파서 테스트")
    print("=" * 70)

    # 테스트 케이스
    test_rules = [
        "KODEX 200: 월 70만원 정기 매수 (1주차 50%, 2-3주차 30%, 마지막주 20%)",
        "TIGER 미국 S&P500: 월 60만원 DCA (1주차 50%, 2-3주차 30%, 마지막주 20%)",
        "KODEX 코스닥150: -10% 하락 시 1차 매수",
        "TIGER 반도체TOP10: +10% 익절",
        "한화에어로스페이스: +10% 시 20% 익절",
    ]

    parser = InvestmentRuleParser(use_llm=True)

    for i, rule_text in enumerate(test_rules, 1):
        print(f"\n[테스트 {i}] {rule_text}")
        print("-" * 70)
        try:
            result = parser.parse(rule_text)
            print("✅ 파싱 성공:")
            print(json.dumps(result, ensure_ascii=False, indent=2))
        except Exception as e:
            print(f"❌ 파싱 실패: {e}")

    print("\n" + "=" * 70)
    print("테스트 완료")
    print("=" * 70)
