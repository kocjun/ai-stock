-- ================================================
-- Paper Trading System Database Schema
-- ================================================

-- 1. 가상 계좌 테이블
CREATE TABLE IF NOT EXISTS virtual_accounts (
    account_id SERIAL PRIMARY KEY,
    account_name VARCHAR(100) NOT NULL,
    initial_balance DECIMAL(15,2) NOT NULL,
    current_balance DECIMAL(15,2) NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) DEFAULT 'active',
    strategy VARCHAR(50) DEFAULT 'ai_comprehensive',
    CONSTRAINT positive_initial_balance CHECK (initial_balance > 0),
    CONSTRAINT positive_current_balance CHECK (current_balance >= 0)
);

-- 2. 가상 거래 테이블
CREATE TABLE IF NOT EXISTS virtual_trades (
    trade_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES virtual_accounts(account_id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL,
    trade_type VARCHAR(10) NOT NULL CHECK (trade_type IN ('buy', 'sell')),
    quantity INTEGER NOT NULL CHECK (quantity > 0),
    price DECIMAL(10,2) NOT NULL CHECK (price > 0),
    total_amount DECIMAL(15,2) NOT NULL,
    commission DECIMAL(10,2) DEFAULT 0,
    trade_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    reason TEXT,
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE RESTRICT
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_virtual_trades_account ON virtual_trades(account_id);
CREATE INDEX IF NOT EXISTS idx_virtual_trades_code ON virtual_trades(code);
CREATE INDEX IF NOT EXISTS idx_virtual_trades_date ON virtual_trades(trade_date);

-- 3. 현재 포지션 테이블
CREATE TABLE IF NOT EXISTS virtual_portfolio (
    position_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES virtual_accounts(account_id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL,
    quantity INTEGER NOT NULL CHECK (quantity >= 0),
    avg_price DECIMAL(10,2) NOT NULL CHECK (avg_price > 0),
    current_price DECIMAL(10,2),
    current_value DECIMAL(15,2),
    profit_loss DECIMAL(15,2),
    profit_loss_pct DECIMAL(10,4),
    first_buy_date TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE RESTRICT,
    UNIQUE(account_id, code)
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_virtual_portfolio_account ON virtual_portfolio(account_id);
CREATE INDEX IF NOT EXISTS idx_virtual_portfolio_code ON virtual_portfolio(code);

-- 4. 보고서 테이블
CREATE TABLE IF NOT EXISTS virtual_reports (
    report_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES virtual_accounts(account_id) ON DELETE CASCADE,
    report_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    report_type VARCHAR(20) DEFAULT 'daily' CHECK (report_type IN ('daily', 'weekly', 'monthly')),
    total_value DECIMAL(15,2) NOT NULL,
    cash_balance DECIMAL(15,2) NOT NULL,
    stock_value DECIMAL(15,2) NOT NULL,
    total_return DECIMAL(15,2),
    return_pct DECIMAL(10,4),
    num_positions INTEGER DEFAULT 0,
    num_trades INTEGER DEFAULT 0,
    win_rate DECIMAL(10,4),
    avg_profit_per_trade DECIMAL(15,2),
    max_drawdown DECIMAL(10,4),
    sharpe_ratio DECIMAL(10,4),
    report_content TEXT
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_virtual_reports_account ON virtual_reports(account_id);
CREATE INDEX IF NOT EXISTS idx_virtual_reports_date ON virtual_reports(report_date);

-- 5. 포트폴리오 히스토리 (일별 스냅샷)
CREATE TABLE IF NOT EXISTS virtual_portfolio_history (
    history_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES virtual_accounts(account_id) ON DELETE CASCADE,
    snapshot_date DATE NOT NULL,
    total_value DECIMAL(15,2) NOT NULL,
    cash_balance DECIMAL(15,2) NOT NULL,
    stock_value DECIMAL(15,2) NOT NULL,
    return_pct DECIMAL(10,4),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(account_id, snapshot_date)
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_portfolio_history_account ON virtual_portfolio_history(account_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_history_date ON virtual_portfolio_history(snapshot_date);

-- ================================================
-- 뷰 생성
-- ================================================

-- 계좌 요약 뷰
CREATE OR REPLACE VIEW v_account_summary AS
SELECT
    a.account_id,
    a.account_name,
    a.initial_balance,
    a.current_balance as cash_balance,
    COALESCE(SUM(p.current_value), 0) as stock_value,
    a.current_balance + COALESCE(SUM(p.current_value), 0) as total_value,
    ((a.current_balance + COALESCE(SUM(p.current_value), 0) - a.initial_balance) / a.initial_balance * 100) as return_pct,
    COUNT(p.position_id) as num_positions,
    a.strategy,
    a.status,
    a.created_at
FROM virtual_accounts a
LEFT JOIN virtual_portfolio p ON a.account_id = p.account_id
GROUP BY a.account_id, a.account_name, a.initial_balance, a.current_balance, a.strategy, a.status, a.created_at;

-- 거래 내역 상세 뷰
CREATE OR REPLACE VIEW v_trade_details AS
SELECT
    t.trade_id,
    t.account_id,
    a.account_name,
    t.code,
    s.name as stock_name,
    t.trade_type,
    t.quantity,
    t.price,
    t.total_amount,
    t.commission,
    t.trade_date,
    t.reason
FROM virtual_trades t
JOIN virtual_accounts a ON t.account_id = a.account_id
JOIN stocks s ON t.code = s.code
ORDER BY t.trade_date DESC;

-- 포지션 상세 뷰
CREATE OR REPLACE VIEW v_position_details AS
SELECT
    p.position_id,
    p.account_id,
    a.account_name,
    p.code,
    s.name as stock_name,
    s.sector,
    p.quantity,
    p.avg_price,
    p.current_price,
    p.current_value,
    p.profit_loss,
    p.profit_loss_pct,
    (p.current_value / NULLIF((SELECT a.current_balance + SUM(p2.current_value)
                               FROM virtual_portfolio p2
                               WHERE p2.account_id = p.account_id), 0) * 100) as weight_pct,
    p.first_buy_date,
    p.updated_at
FROM virtual_portfolio p
JOIN virtual_accounts a ON p.account_id = a.account_id
JOIN stocks s ON p.code = s.code
WHERE p.quantity > 0
ORDER BY p.current_value DESC;

-- ================================================
-- 함수 생성
-- ================================================

-- 포지션 정리 함수 (수량이 0인 포지션 삭제)
CREATE OR REPLACE FUNCTION cleanup_zero_positions()
RETURNS INTEGER AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM virtual_portfolio WHERE quantity = 0;
    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$ LANGUAGE plpgsql;

-- 일별 스냅샷 저장 함수
CREATE OR REPLACE FUNCTION save_daily_snapshot(p_account_id INTEGER)
RETURNS VOID AS $$
DECLARE
    v_total_value DECIMAL(15,2);
    v_cash_balance DECIMAL(15,2);
    v_stock_value DECIMAL(15,2);
    v_return_pct DECIMAL(10,4);
    v_initial_balance DECIMAL(15,2);
BEGIN
    -- 계좌 정보 조회
    SELECT current_balance, initial_balance
    INTO v_cash_balance, v_initial_balance
    FROM virtual_accounts
    WHERE account_id = p_account_id;

    -- 주식 평가액 계산
    SELECT COALESCE(SUM(current_value), 0)
    INTO v_stock_value
    FROM virtual_portfolio
    WHERE account_id = p_account_id;

    v_total_value := v_cash_balance + v_stock_value;
    v_return_pct := ((v_total_value - v_initial_balance) / v_initial_balance * 100);

    -- 스냅샷 저장
    INSERT INTO virtual_portfolio_history (
        account_id, snapshot_date, total_value, cash_balance, stock_value, return_pct
    )
    VALUES (
        p_account_id, CURRENT_DATE, v_total_value, v_cash_balance, v_stock_value, v_return_pct
    )
    ON CONFLICT (account_id, snapshot_date)
    DO UPDATE SET
        total_value = EXCLUDED.total_value,
        cash_balance = EXCLUDED.cash_balance,
        stock_value = EXCLUDED.stock_value,
        return_pct = EXCLUDED.return_pct,
        created_at = CURRENT_TIMESTAMP;
END;
$$ LANGUAGE plpgsql;

-- ================================================
-- 초기 데이터 (선택적)
-- ================================================

-- 예시 계좌 생성 (필요시 주석 해제)
-- INSERT INTO virtual_accounts (account_name, initial_balance, current_balance)
-- VALUES ('AI 투자 시뮬레이션 #1', 10000000.00, 10000000.00);

-- ================================================
-- 권한 설정 (필요시)
-- ================================================

-- GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA public TO invest_user;
-- GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO invest_user;
-- GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO invest_user;
