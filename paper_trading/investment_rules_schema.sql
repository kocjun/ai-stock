-- ============================================================
-- 투자 룰 기반 자동 매매 시스템 DB 스키마
-- 생성일: 2025-12-31
-- 목적: 사용자 정의 투자 룰 저장 및 실행 관리
-- ============================================================

-- ============================================================
-- 1. 투자 룰 정의 테이블
-- ============================================================
CREATE TABLE IF NOT EXISTS investment_rules (
    rule_id SERIAL PRIMARY KEY,
    rule_name VARCHAR(200) NOT NULL,
    rule_type VARCHAR(50) NOT NULL CHECK (rule_type IN ('DCA', 'SIGNAL', 'REBALANCE', 'STOP_LOSS', 'TAKE_PROFIT')),
    asset_category VARCHAR(50) NOT NULL CHECK (asset_category IN ('CORE', 'SATELLITE', 'DEFENSE', 'CASH')),

    -- 대상 종목 (NULL이면 전체 포트폴리오 대상)
    target_code VARCHAR(10),
    target_name VARCHAR(100),

    -- 실행 조건 (JSON 형식)
    -- 예시: {"price_change_pct": -10, "comparison": "<=", "reference": "buy_price"}
    conditions JSONB NOT NULL DEFAULT '{}',

    -- 실행 액션 (JSON 형식)
    -- 예시: {"action": "buy", "amount_type": "fixed", "amount_value": 700000, "ratio": 1.0}
    actions JSONB NOT NULL DEFAULT '{}',

    -- 비중 목표 (리밸런싱용)
    target_weight_min DECIMAL(5,2),  -- 예: 20.00 (20%)
    target_weight_max DECIMAL(5,2),  -- 예: 30.00 (30%)

    -- 스케줄 설정
    schedule_type VARCHAR(50) CHECK (schedule_type IN ('FIXED_DATE', 'MONTHLY_SPLIT', 'WEEKLY', 'REALTIME', 'DAILY')),
    schedule_params JSONB DEFAULT '{}',
    -- 예시: {"week": [1, 2, 3, 4], "ratio": [50, 30, 20]}

    priority INTEGER DEFAULT 100,  -- 실행 우선순위 (낮을수록 먼저 실행)
    is_active BOOLEAN DEFAULT true,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (target_code) REFERENCES stocks(code) ON DELETE SET NULL
);

CREATE INDEX IF NOT EXISTS idx_rules_type ON investment_rules(rule_type);
CREATE INDEX IF NOT EXISTS idx_rules_active ON investment_rules(is_active);
CREATE INDEX IF NOT EXISTS idx_rules_category ON investment_rules(asset_category);
CREATE INDEX IF NOT EXISTS idx_rules_target ON investment_rules(target_code);

COMMENT ON TABLE investment_rules IS '투자 룰 정의 - DCA, 신호형, 리밸런싱, 손절/익절';
COMMENT ON COLUMN investment_rules.rule_type IS 'DCA: 정기매수, SIGNAL: 신호형, REBALANCE: 리밸런싱, STOP_LOSS/TAKE_PROFIT: 손절/익절';
COMMENT ON COLUMN investment_rules.asset_category IS 'CORE: 코어자산, SATELLITE: 위성자산, DEFENSE: 방어자산, CASH: 현금성';
COMMENT ON COLUMN investment_rules.conditions IS 'JSON 형식 조건 (trigger, threshold, comparison, reference)';
COMMENT ON COLUMN investment_rules.actions IS 'JSON 형식 액션 (action, amount_type, amount_value, ratio)';
COMMENT ON COLUMN investment_rules.schedule_params IS 'JSON 형식 스케줄 파라미터';

-- ============================================================
-- 2. 룰 실행 히스토리 테이블
-- ============================================================
CREATE TABLE IF NOT EXISTS rule_executions (
    execution_id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES investment_rules(rule_id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES virtual_accounts(account_id) ON DELETE CASCADE,

    execution_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    execution_status VARCHAR(50) NOT NULL CHECK (execution_status IN ('SUCCESS', 'FAILED', 'SKIPPED', 'PARTIAL')),

    -- 조건 평가 결과
    condition_met BOOLEAN NOT NULL,
    condition_details JSONB DEFAULT '{}',

    -- 실행 결과
    trade_ids INTEGER[],  -- 생성된 거래 ID 배열
    amount_executed DECIMAL(15,2) DEFAULT 0,
    quantity_executed INTEGER DEFAULT 0,

    error_message TEXT,
    execution_log TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rule_executions_rule ON rule_executions(rule_id);
CREATE INDEX IF NOT EXISTS idx_rule_executions_account ON rule_executions(account_id);
CREATE INDEX IF NOT EXISTS idx_rule_executions_date ON rule_executions(execution_date);
CREATE INDEX IF NOT EXISTS idx_rule_executions_status ON rule_executions(execution_status);

COMMENT ON TABLE rule_executions IS '룰 실행 히스토리 - 성공/실패 여부, 거래 내역 연결';
COMMENT ON COLUMN rule_executions.condition_met IS '조건 충족 여부 (true=실행, false=스킵)';
COMMENT ON COLUMN rule_executions.trade_ids IS '생성된 거래 ID 배열 (virtual_trades 참조)';

-- ============================================================
-- 3. DCA 실행 스케줄 테이블
-- ============================================================
CREATE TABLE IF NOT EXISTS dca_schedules (
    schedule_id SERIAL PRIMARY KEY,
    rule_id INTEGER NOT NULL REFERENCES investment_rules(rule_id) ON DELETE CASCADE,
    account_id INTEGER NOT NULL REFERENCES virtual_accounts(account_id) ON DELETE CASCADE,

    year INTEGER NOT NULL,
    month INTEGER NOT NULL CHECK (month BETWEEN 1 AND 12),
    week_number INTEGER NOT NULL CHECK (week_number BETWEEN 1 AND 5),  -- 1주차, 2-3주차(2또는3), 마지막주(4또는5)

    scheduled_date DATE NOT NULL,
    scheduled_amount DECIMAL(15,2) NOT NULL,
    execution_ratio DECIMAL(5,2) NOT NULL,  -- 50.00, 30.00, 20.00

    is_executed BOOLEAN DEFAULT false,
    executed_at TIMESTAMP,
    execution_id INTEGER REFERENCES rule_executions(execution_id),

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(rule_id, account_id, year, month, week_number)
);

CREATE INDEX IF NOT EXISTS idx_dca_schedules_date ON dca_schedules(scheduled_date);
CREATE INDEX IF NOT EXISTS idx_dca_schedules_pending ON dca_schedules(is_executed) WHERE is_executed = false;
CREATE INDEX IF NOT EXISTS idx_dca_schedules_rule ON dca_schedules(rule_id);
CREATE INDEX IF NOT EXISTS idx_dca_schedules_ym ON dca_schedules(year, month);

COMMENT ON TABLE dca_schedules IS 'DCA 월간 스케줄 - 1주차 50%, 2-3주차 30%, 마지막주 20%';
COMMENT ON COLUMN dca_schedules.week_number IS '1=1주차, 2/3=2-3주차, 4/5=마지막주';
COMMENT ON COLUMN dca_schedules.execution_ratio IS '실행 비율 (50%, 30%, 20%)';

-- ============================================================
-- 4. 리밸런싱 히스토리 테이블
-- ============================================================
CREATE TABLE IF NOT EXISTS rebalancing_history (
    rebalance_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES virtual_accounts(account_id) ON DELETE CASCADE,

    rebalance_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    rebalance_type VARCHAR(50) NOT NULL CHECK (rebalance_type IN ('AUTO', 'MANUAL', 'SCHEDULED')),

    -- 리밸런싱 전후 비중
    weights_before JSONB NOT NULL,  -- {"005930": 25.5, "035420": 15.3, ...}
    weights_after JSONB NOT NULL,
    weights_target JSONB NOT NULL,

    -- 실행 거래
    trade_ids INTEGER[],
    total_trades INTEGER DEFAULT 0,
    total_amount DECIMAL(15,2) DEFAULT 0,

    execution_status VARCHAR(50) DEFAULT 'SUCCESS',
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_rebalancing_history_account ON rebalancing_history(account_id);
CREATE INDEX IF NOT EXISTS idx_rebalancing_history_date ON rebalancing_history(rebalance_date);
CREATE INDEX IF NOT EXISTS idx_rebalancing_history_type ON rebalancing_history(rebalance_type);

COMMENT ON TABLE rebalancing_history IS '리밸런싱 실행 히스토리 - 비중 변화 추적';
COMMENT ON COLUMN rebalancing_history.weights_before IS 'JSON 형식 리밸런싱 전 비중 (종목코드: 비율)';
COMMENT ON COLUMN rebalancing_history.weights_after IS 'JSON 형식 리밸런싱 후 비중';
COMMENT ON COLUMN rebalancing_history.weights_target IS 'JSON 형식 목표 비중';

-- ============================================================
-- 5. 실시간 가격 캐시 테이블
-- ============================================================
CREATE TABLE IF NOT EXISTS realtime_price_cache (
    code VARCHAR(10) PRIMARY KEY,
    current_price DECIMAL(10,2) NOT NULL,
    previous_price DECIMAL(10,2),
    price_change DECIMAL(10,2),
    price_change_pct DECIMAL(10,4),

    high_price DECIMAL(10,2),
    low_price DECIMAL(10,2),
    volume BIGINT,
    trade_value BIGINT,

    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE
);

CREATE INDEX IF NOT EXISTS idx_realtime_cache_updated ON realtime_price_cache(last_updated);
CREATE INDEX IF NOT EXISTS idx_realtime_cache_change_pct ON realtime_price_cache(price_change_pct);

COMMENT ON TABLE realtime_price_cache IS '실시간 가격 캐시 - WebSocket 수신 데이터 저장';
COMMENT ON COLUMN realtime_price_cache.price_change_pct IS '변동률 (%) - 신호형 룰 조건 평가용';

-- ============================================================
-- 6. 기존 테이블 수정 (ALTER TABLE)
-- ============================================================

-- virtual_accounts 테이블에 컬럼 추가
ALTER TABLE virtual_accounts
    ADD COLUMN IF NOT EXISTS rule_set_id INTEGER,
    ADD COLUMN IF NOT EXISTS auto_trading_enabled BOOLEAN DEFAULT false;

COMMENT ON COLUMN virtual_accounts.rule_set_id IS '적용 중인 룰셋 ID (향후 확장용)';
COMMENT ON COLUMN virtual_accounts.auto_trading_enabled IS '자동 매매 활성화 여부';

-- virtual_trades 테이블에 컬럼 추가
ALTER TABLE virtual_trades
    ADD COLUMN IF NOT EXISTS rule_id INTEGER REFERENCES investment_rules(rule_id),
    ADD COLUMN IF NOT EXISTS execution_id INTEGER REFERENCES rule_executions(execution_id);

CREATE INDEX IF NOT EXISTS idx_trades_rule ON virtual_trades(rule_id);
CREATE INDEX IF NOT EXISTS idx_trades_execution ON virtual_trades(execution_id);

COMMENT ON COLUMN virtual_trades.rule_id IS '거래를 발생시킨 투자 룰 ID';
COMMENT ON COLUMN virtual_trades.execution_id IS '거래가 속한 룰 실행 ID';

-- ============================================================
-- 7. 뷰 생성 (편의성)
-- ============================================================

-- 활성화된 룰 목록
CREATE OR REPLACE VIEW v_active_rules AS
SELECT
    r.rule_id,
    r.rule_name,
    r.rule_type,
    r.asset_category,
    r.target_code,
    s.name as target_name,
    r.schedule_type,
    r.priority,
    r.conditions,
    r.actions,
    COUNT(DISTINCT e.execution_id) as total_executions,
    COUNT(DISTINCT e.execution_id) FILTER (WHERE e.execution_status = 'SUCCESS') as success_count,
    MAX(e.execution_date) as last_execution
FROM investment_rules r
LEFT JOIN stocks s ON r.target_code = s.code
LEFT JOIN rule_executions e ON r.rule_id = e.rule_id
WHERE r.is_active = true
GROUP BY r.rule_id, s.name;

COMMENT ON VIEW v_active_rules IS '활성화된 투자 룰 목록 및 실행 통계';

-- 실행 대기 중인 DCA 스케줄
CREATE OR REPLACE VIEW v_pending_dca_schedules AS
SELECT
    ds.schedule_id,
    ds.scheduled_date,
    ds.scheduled_amount,
    ds.execution_ratio,
    r.rule_name,
    r.target_code,
    s.name as target_name,
    r.asset_category,
    va.account_name
FROM dca_schedules ds
JOIN investment_rules r ON ds.rule_id = r.rule_id
JOIN virtual_accounts va ON ds.account_id = va.account_id
LEFT JOIN stocks s ON r.target_code = s.code
WHERE ds.is_executed = false
  AND ds.scheduled_date <= CURRENT_DATE + INTERVAL '7 days'
ORDER BY ds.scheduled_date, r.priority;

COMMENT ON VIEW v_pending_dca_schedules IS '실행 대기 중인 DCA 스케줄 (향후 7일)';

-- 룰별 성과 분석
CREATE OR REPLACE VIEW v_rule_performance AS
SELECT
    r.rule_id,
    r.rule_name,
    r.rule_type,
    r.asset_category,
    COUNT(DISTINCT t.trade_id) as total_trades,
    COUNT(DISTINCT CASE WHEN t.trade_type = 'buy' THEN t.trade_id END) as buy_count,
    COUNT(DISTINCT CASE WHEN t.trade_type = 'sell' THEN t.trade_id END) as sell_count,
    SUM(CASE WHEN t.trade_type = 'buy' THEN t.total_amount ELSE 0 END) as total_buy_amount,
    SUM(CASE WHEN t.trade_type = 'sell' THEN t.total_amount ELSE 0 END) as total_sell_amount,
    SUM(CASE WHEN t.trade_type = 'buy' THEN t.quantity ELSE 0 END) as total_buy_quantity,
    SUM(CASE WHEN t.trade_type = 'sell' THEN t.quantity ELSE 0 END) as total_sell_quantity
FROM investment_rules r
LEFT JOIN virtual_trades t ON r.rule_id = t.rule_id
WHERE r.is_active = true
GROUP BY r.rule_id;

COMMENT ON VIEW v_rule_performance IS '룰별 매매 성과 통계 (거래 횟수 및 금액)';

-- ============================================================
-- 8. 샘플 데이터 삽입 (테스트용)
-- 주의: stocks 테이블에 종목이 먼저 등록되어야 합니다.
-- 룰 매니저 (rule_manager.py)를 사용하여 추가하는 것을 권장합니다.
-- ============================================================

/*
-- KODEX 200 DCA 룰
INSERT INTO investment_rules (
    rule_name, rule_type, asset_category, target_code, target_name,
    conditions, actions, schedule_type, schedule_params, priority
) VALUES (
    'KODEX 200 월 70만원 DCA',
    'DCA',
    'CORE',
    '069500',
    'KODEX 200',
    '{"trigger": "monthly", "always_execute": true}',
    '{"action": "buy", "amount_type": "fixed", "amount_value": 700000, "ratio": 1.0}',
    'MONTHLY_SPLIT',
    '{"weeks": [1, 2, 3, 4], "ratios": [50, 30, 20]}',
    10
) ON CONFLICT DO NOTHING;

-- TIGER 미국 S&P500 DCA 룰
INSERT INTO investment_rules (
    rule_name, rule_type, asset_category, target_code, target_name,
    conditions, actions, schedule_type, schedule_params, priority
) VALUES (
    'TIGER 미국 S&P500 월 60만원 DCA',
    'DCA',
    'CORE',
    '360750',
    'TIGER 미국S&P500',
    '{"trigger": "monthly", "always_execute": true}',
    '{"action": "buy", "amount_type": "fixed", "amount_value": 600000, "ratio": 1.0}',
    'MONTHLY_SPLIT',
    '{"weeks": [1, 2, 3, 4], "ratios": [50, 30, 20]}',
    10
) ON CONFLICT DO NOTHING;

-- KODEX 고배당 DCA 룰
INSERT INTO investment_rules (
    rule_name, rule_type, asset_category, target_code, target_name,
    conditions, actions, schedule_type, schedule_params, priority
) VALUES (
    'KODEX 고배당 월 30만원 DCA',
    'DCA',
    'CORE',
    '364970',
    'KODEX 고배당',
    '{"trigger": "monthly", "always_execute": true}',
    '{"action": "buy", "amount_type": "fixed", "amount_value": 300000, "ratio": 1.0}',
    'MONTHLY_SPLIT',
    '{"weeks": [1, 2, 3, 4], "ratios": [50, 30, 20]}',
    10
) ON CONFLICT DO NOTHING;

-- KODEX 코스닥150 신호형 매수 룰 (-10%)
INSERT INTO investment_rules (
    rule_name, rule_type, asset_category, target_code, target_name,
    conditions, actions, schedule_type, priority
) VALUES (
    '코스닥150 -10% 1차 매수',
    'SIGNAL',
    'SATELLITE',
    '229200',
    'KODEX 코스닥150',
    '{"trigger": "price_change", "threshold": -10.0, "comparison": "<=", "reference": "avg_price"}',
    '{"action": "buy", "amount_type": "percentage", "amount_value": 50, "ratio": 0.5}',
    'REALTIME',
    50
) ON CONFLICT DO NOTHING;

-- KODEX 코스닥150 신호형 매수 룰 (-15%)
INSERT INTO investment_rules (
    rule_name, rule_type, asset_category, target_code, target_name,
    conditions, actions, schedule_type, priority
) VALUES (
    '코스닥150 -15% 2차 매수',
    'SIGNAL',
    'SATELLITE',
    '229200',
    'KODEX 코스닥150',
    '{"trigger": "price_change", "threshold": -15.0, "comparison": "<=", "reference": "avg_price"}',
    '{"action": "buy", "amount_type": "percentage", "amount_value": 50, "ratio": 0.5}',
    'REALTIME',
    40
) ON CONFLICT DO NOTHING;

-- KODEX 코스닥150 익절 룰 (+15%)
INSERT INTO investment_rules (
    rule_name, rule_type, asset_category, target_code, target_name,
    conditions, actions, schedule_type, priority
) VALUES (
    '코스닥150 +15% 익절',
    'TAKE_PROFIT',
    'SATELLITE',
    '229200',
    'KODEX 코스닥150',
    '{"trigger": "price_change", "threshold": 15.0, "comparison": ">=", "reference": "avg_price"}',
    '{"action": "sell", "amount_type": "percentage", "amount_value": 15, "ratio": 0.15}',
    'REALTIME',
    30
) ON CONFLICT DO NOTHING;
*/

-- ============================================================
-- 9. 트리거 함수 (자동 updated_at)
-- ============================================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER update_investment_rules_updated_at
    BEFORE UPDATE ON investment_rules
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================
-- 스키마 생성 완료
-- ============================================================
