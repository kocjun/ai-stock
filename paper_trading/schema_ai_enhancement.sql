-- ================================================
-- AI 분석 저장 스키마 확장
-- Paper Trading System에 AI 분석 결과 저장 기능 추가
-- ================================================

-- 1. AI 종목 분석 결과 테이블
CREATE TABLE IF NOT EXISTS ai_stock_analysis (
    analysis_id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL REFERENCES stocks(code) ON DELETE CASCADE,
    analysis_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 종합 점수 및 세부 점수 (0-100)
    overall_score DECIMAL(5, 2),
    financial_score DECIMAL(5, 2),
    technical_score DECIMAL(5, 2),
    risk_score DECIMAL(5, 2),

    -- 가격 예측
    target_price DECIMAL(10, 2),
    target_horizon_days INTEGER,
    confidence_level DECIMAL(5, 2),

    -- 리스크 평가
    risk_grade VARCHAR(20) CHECK (risk_grade IN ('Low', 'Medium', 'High')),
    volatility DECIMAL(10, 4),
    max_drawdown DECIMAL(10, 4),

    -- 투자 근거 및 분석 내용
    buy_rationale TEXT,
    key_factors JSONB,

    -- 기술적 지표
    technical_indicators JSONB,

    -- 재무 지표
    financial_metrics JSONB,

    -- 분석 출처
    analysis_source VARCHAR(50) DEFAULT 'integrated_crew',

    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_ai_stock_analysis_code ON ai_stock_analysis(code);
CREATE INDEX IF NOT EXISTS idx_ai_stock_analysis_date ON ai_stock_analysis(analysis_date);
CREATE INDEX IF NOT EXISTS idx_ai_stock_analysis_overall_score ON ai_stock_analysis(overall_score DESC);

-- 2. 거래와 AI 분석 연결 테이블
CREATE TABLE IF NOT EXISTS trade_ai_analysis (
    link_id SERIAL PRIMARY KEY,
    trade_id INTEGER NOT NULL REFERENCES virtual_trades(trade_id) ON DELETE CASCADE,
    analysis_id INTEGER NOT NULL REFERENCES ai_stock_analysis(analysis_id) ON DELETE CASCADE,

    -- 분석이 거래에 미친 영향도
    influence_score DECIMAL(5, 2),
    analysis_used_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    UNIQUE(trade_id, analysis_id)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_trade_ai_analysis_trade ON trade_ai_analysis(trade_id);
CREATE INDEX IF NOT EXISTS idx_trade_ai_analysis_analysis ON trade_ai_analysis(analysis_id);

-- 3. 포트폴리오 AI 인사이트 테이블
CREATE TABLE IF NOT EXISTS portfolio_ai_insights (
    insight_id SERIAL PRIMARY KEY,
    account_id INTEGER NOT NULL REFERENCES virtual_accounts(account_id) ON DELETE CASCADE,
    insight_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,

    -- 포트폴리오 성과 예측
    expected_return DECIMAL(10, 4),
    expected_volatility DECIMAL(10, 4),
    sharpe_ratio DECIMAL(10, 4),

    -- 리밸런싱 추천
    rebalance_needed BOOLEAN DEFAULT FALSE,
    rebalance_suggestions JSONB,

    -- 시장 전망
    market_sentiment VARCHAR(20) CHECK (market_sentiment IN ('Bearish', 'Neutral', 'Bullish')),
    market_analysis TEXT,

    -- 위험 경고
    risk_warnings JSONB,

    -- 섹터별 추천 배분
    sector_allocation JSONB,

    -- 종합 평가
    portfolio_analysis TEXT,
    recommendations TEXT,

    -- 메타데이터
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    analysis_source VARCHAR(50) DEFAULT 'integrated_crew'
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_portfolio_ai_insights_account ON portfolio_ai_insights(account_id);
CREATE INDEX IF NOT EXISTS idx_portfolio_ai_insights_date ON portfolio_ai_insights(insight_date);

-- 4. AI 예측 추적 테이블 (AI 예측이 맞았는지 검증)
CREATE TABLE IF NOT EXISTS ai_prediction_tracking (
    tracking_id SERIAL PRIMARY KEY,
    analysis_id INTEGER NOT NULL REFERENCES ai_stock_analysis(analysis_id) ON DELETE CASCADE,
    code VARCHAR(10) NOT NULL REFERENCES stocks(code) ON DELETE CASCADE,

    -- 예측 정보
    predicted_target_price DECIMAL(10, 2),
    predicted_date TIMESTAMP,
    prediction_horizon_days INTEGER,

    -- 실제 결과
    actual_price_on_target_date DECIMAL(10, 2),
    actual_return_pct DECIMAL(10, 4),
    was_prediction_correct BOOLEAN,

    -- 분석
    accuracy_error_pct DECIMAL(10, 4),
    feedback TEXT,

    -- 타임스탐프
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_ai_prediction_tracking_code ON ai_prediction_tracking(code);
CREATE INDEX IF NOT EXISTS idx_ai_prediction_tracking_analysis ON ai_prediction_tracking(analysis_id);

-- 5. AI 분석 히스토리 (모든 분석 버전 추적)
CREATE TABLE IF NOT EXISTS ai_analysis_history (
    history_id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL REFERENCES stocks(code) ON DELETE CASCADE,
    analysis_date DATE NOT NULL,

    -- 시계열 점수
    overall_score DECIMAL(5, 2),
    target_price DECIMAL(10, 2),
    risk_grade VARCHAR(20),

    -- 변화 추적
    score_change DECIMAL(5, 2),
    price_change DECIMAL(10, 2),

    -- 메모
    notes TEXT,

    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(code, analysis_date)
);

-- 인덱스
CREATE INDEX IF NOT EXISTS idx_ai_analysis_history_code ON ai_analysis_history(code);
CREATE INDEX IF NOT EXISTS idx_ai_analysis_history_date ON ai_analysis_history(analysis_date);

-- ================================================
-- 뷰 생성
-- ================================================

-- AI 분석과 거래 통합 뷰
CREATE OR REPLACE VIEW v_trade_with_ai_analysis AS
SELECT
    t.trade_id,
    t.account_id,
    t.code,
    s.name as stock_name,
    t.trade_type,
    t.quantity,
    t.price,
    t.trade_date,
    t.reason as trade_reason,
    a.analysis_id,
    a.overall_score,
    a.target_price,
    a.risk_grade,
    a.buy_rationale,
    a.analysis_date,
    ta.influence_score
FROM virtual_trades t
LEFT JOIN stocks s ON t.code = s.code
LEFT JOIN trade_ai_analysis ta ON t.trade_id = ta.trade_id
LEFT JOIN ai_stock_analysis a ON ta.analysis_id = a.analysis_id
ORDER BY t.trade_date DESC;

-- 현재 포지션에 대한 최신 AI 분석 뷰
CREATE OR REPLACE VIEW v_portfolio_with_latest_ai AS
SELECT
    p.position_id,
    p.account_id,
    p.code,
    s.name as stock_name,
    s.sector,
    p.quantity,
    p.avg_price,
    p.current_price,
    p.current_value,
    p.profit_loss,
    p.profit_loss_pct,
    p.first_buy_date,
    -- 최신 AI 분석
    a.analysis_id,
    a.overall_score,
    a.financial_score,
    a.technical_score,
    a.risk_score,
    a.target_price,
    a.confidence_level,
    a.risk_grade,
    a.buy_rationale,
    a.key_factors,
    a.analysis_date
FROM virtual_portfolio p
JOIN stocks s ON p.code = s.code
LEFT JOIN LATERAL (
    SELECT *
    FROM ai_stock_analysis
    WHERE code = p.code
    ORDER BY analysis_date DESC
    LIMIT 1
) a ON TRUE
WHERE p.quantity > 0
ORDER BY p.current_value DESC;

-- 포트폴리오별 AI 분석 요약 뷰
CREATE OR REPLACE VIEW v_portfolio_ai_summary AS
SELECT
    poi.insight_id,
    poi.account_id,
    a.account_name,
    poi.insight_date,
    poi.expected_return,
    poi.expected_volatility,
    poi.sharpe_ratio,
    poi.market_sentiment,
    poi.rebalance_needed,
    poi.sector_allocation,
    COUNT(DISTINCT pwla.code) as analyzed_positions,
    AVG(pwla.overall_score) as avg_stock_score
FROM portfolio_ai_insights poi
JOIN virtual_accounts a ON poi.account_id = a.account_id
LEFT JOIN v_portfolio_with_latest_ai pwla ON poi.account_id = pwla.account_id
GROUP BY
    poi.insight_id,
    poi.account_id,
    a.account_name,
    poi.insight_date,
    poi.expected_return,
    poi.expected_volatility,
    poi.sharpe_ratio,
    poi.market_sentiment,
    poi.rebalance_needed,
    poi.sector_allocation;

-- ================================================
-- 함수 생성
-- ================================================

-- AI 분석 결과 저장 함수
CREATE OR REPLACE FUNCTION save_ai_stock_analysis(
    p_code VARCHAR,
    p_overall_score DECIMAL,
    p_financial_score DECIMAL,
    p_technical_score DECIMAL,
    p_risk_score DECIMAL,
    p_target_price DECIMAL,
    p_target_horizon_days INTEGER,
    p_confidence_level DECIMAL,
    p_risk_grade VARCHAR,
    p_volatility DECIMAL,
    p_max_drawdown DECIMAL,
    p_buy_rationale TEXT,
    p_key_factors JSONB,
    p_technical_indicators JSONB,
    p_financial_metrics JSONB,
    p_analysis_source VARCHAR DEFAULT 'integrated_crew'
)
RETURNS INTEGER AS $$
DECLARE
    v_analysis_id INTEGER;
BEGIN
    INSERT INTO ai_stock_analysis (
        code, overall_score, financial_score, technical_score, risk_score,
        target_price, target_horizon_days, confidence_level,
        risk_grade, volatility, max_drawdown,
        buy_rationale, key_factors, technical_indicators, financial_metrics,
        analysis_source
    )
    VALUES (
        p_code, p_overall_score, p_financial_score, p_technical_score, p_risk_score,
        p_target_price, p_target_horizon_days, p_confidence_level,
        p_risk_grade, p_volatility, p_max_drawdown,
        p_buy_rationale, p_key_factors, p_technical_indicators, p_financial_metrics,
        p_analysis_source
    )
    RETURNING analysis_id INTO v_analysis_id;

    RETURN v_analysis_id;
END;
$$ LANGUAGE plpgsql;

-- 거래와 AI 분석 연결 함수
CREATE OR REPLACE FUNCTION link_trade_to_ai_analysis(
    p_trade_id INTEGER,
    p_analysis_id INTEGER,
    p_influence_score DECIMAL DEFAULT NULL
)
RETURNS BOOLEAN AS $$
BEGIN
    INSERT INTO trade_ai_analysis (trade_id, analysis_id, influence_score)
    VALUES (p_trade_id, p_analysis_id, p_influence_score)
    ON CONFLICT (trade_id, analysis_id) DO NOTHING;

    RETURN TRUE;
END;
$$ LANGUAGE plpgsql;

-- 포트폴리오 AI 인사이트 저장 함수
CREATE OR REPLACE FUNCTION save_portfolio_ai_insight(
    p_account_id INTEGER,
    p_expected_return DECIMAL,
    p_expected_volatility DECIMAL,
    p_sharpe_ratio DECIMAL,
    p_market_sentiment VARCHAR,
    p_rebalance_needed BOOLEAN,
    p_market_analysis TEXT,
    p_sector_allocation JSONB,
    p_portfolio_analysis TEXT,
    p_recommendations TEXT
)
RETURNS INTEGER AS $$
DECLARE
    v_insight_id INTEGER;
BEGIN
    INSERT INTO portfolio_ai_insights (
        account_id, expected_return, expected_volatility, sharpe_ratio,
        market_sentiment, rebalance_needed, market_analysis,
        sector_allocation, portfolio_analysis, recommendations
    )
    VALUES (
        p_account_id, p_expected_return, p_expected_volatility, p_sharpe_ratio,
        p_market_sentiment, p_rebalance_needed, p_market_analysis,
        p_sector_allocation, p_portfolio_analysis, p_recommendations
    )
    RETURNING insight_id INTO v_insight_id;

    RETURN v_insight_id;
END;
$$ LANGUAGE plpgsql;

-- ================================================
-- 사용 예제 (주석)
-- ================================================

-- AI 분석 저장 예제
-- SELECT save_ai_stock_analysis(
--     '005930', 78.5, 75.0, 82.0, 65.0,
--     120000, 90, 85.0, 'Medium',
--     15.2, 12.5,
--     '반도체 업황 회복, PER 저평가, HBM 수요 증가',
--     '{"buy_strength": "Strong", "momentum": "Positive"}'::jsonb,
--     '{"RSI": 52, "MACD": "Bullish"}'::jsonb,
--     '{"PER": 10.5, "PBR": 1.2, "ROE": 15.5}'::jsonb
-- );

-- ================================================
-- 권한 설정 (필요시)
-- ================================================

-- GRANT SELECT, INSERT, UPDATE ON ai_stock_analysis TO invest_user;
-- GRANT SELECT, INSERT, UPDATE ON trade_ai_analysis TO invest_user;
-- GRANT SELECT, INSERT, UPDATE ON portfolio_ai_insights TO invest_user;
-- GRANT SELECT ON v_portfolio_with_latest_ai TO invest_user;
-- GRANT SELECT ON v_portfolio_ai_summary TO invest_user;
