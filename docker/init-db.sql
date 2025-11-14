-- 한국 주식 투자 분석 AI 에이전트 데이터베이스 초기화 스크립트

-- 종목 마스터 테이블
CREATE TABLE IF NOT EXISTS stocks (
    code VARCHAR(10) PRIMARY KEY,
    name VARCHAR(100) NOT NULL,
    market VARCHAR(10),
    sector VARCHAR(50),
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- 가격 데이터 테이블
CREATE TABLE IF NOT EXISTS prices (
    code VARCHAR(10),
    date DATE,
    open DECIMAL(10,2),
    high DECIMAL(10,2),
    low DECIMAL(10,2),
    close DECIMAL(10,2),
    volume BIGINT,
    PRIMARY KEY (code, date),
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE
);

-- 재무 데이터 테이블
CREATE TABLE IF NOT EXISTS financials (
    code VARCHAR(10),
    year INT,
    quarter INT,
    revenue BIGINT,
    operating_profit BIGINT,
    net_profit BIGINT,
    total_assets BIGINT,
    total_equity BIGINT,
    total_debt BIGINT,
    PRIMARY KEY (code, year, quarter),
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE
);

-- 뉴스 요약 테이블
CREATE TABLE IF NOT EXISTS news_summary (
    id SERIAL PRIMARY KEY,
    code VARCHAR(10),
    title TEXT NOT NULL,
    summary TEXT,
    sentiment FLOAT,
    published_at TIMESTAMP,
    source VARCHAR(100),
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE SET NULL
);

-- 인덱스 생성
CREATE INDEX IF NOT EXISTS idx_prices_date ON prices(date);
CREATE INDEX IF NOT EXISTS idx_prices_code_date ON prices(code, date DESC);
CREATE INDEX IF NOT EXISTS idx_stocks_sector ON stocks(sector);
CREATE INDEX IF NOT EXISTS idx_stocks_market ON stocks(market);
CREATE INDEX IF NOT EXISTS idx_financials_year_quarter ON financials(year DESC, quarter DESC);
CREATE INDEX IF NOT EXISTS idx_news_published_at ON news_summary(published_at DESC);
CREATE INDEX IF NOT EXISTS idx_news_code ON news_summary(code);

-- 뷰 생성: 최신 재무 데이터
CREATE OR REPLACE VIEW latest_financials AS
SELECT DISTINCT ON (code)
    code,
    year,
    quarter,
    revenue,
    operating_profit,
    net_profit,
    total_assets,
    total_equity,
    total_debt,
    CASE
        WHEN total_equity > 0 THEN ROUND((net_profit::DECIMAL / total_equity * 100)::NUMERIC, 2)
        ELSE NULL
    END as roe,
    CASE
        WHEN total_assets > 0 THEN ROUND((net_profit::DECIMAL / total_assets * 100)::NUMERIC, 2)
        ELSE NULL
    END as roa,
    CASE
        WHEN total_equity > 0 THEN ROUND((total_debt::DECIMAL / total_equity * 100)::NUMERIC, 2)
        ELSE NULL
    END as debt_ratio
FROM financials
ORDER BY code, year DESC, quarter DESC;

-- 뷰 생성: 종목 기본 정보 + 최신 가격
CREATE OR REPLACE VIEW stocks_with_latest_price AS
SELECT
    s.code,
    s.name,
    s.market,
    s.sector,
    p.date as last_trade_date,
    p.close as last_price,
    p.volume as last_volume
FROM stocks s
LEFT JOIN LATERAL (
    SELECT date, close, volume
    FROM prices
    WHERE code = s.code
    ORDER BY date DESC
    LIMIT 1
) p ON true;

-- 코멘트 추가
COMMENT ON TABLE stocks IS '상장 종목 마스터 테이블';
COMMENT ON TABLE prices IS '일별 가격 및 거래량 데이터';
COMMENT ON TABLE financials IS '분기별 재무제표 데이터';
COMMENT ON TABLE news_summary IS '뉴스 요약 및 감성 분석 결과';

-- 초기 데이터 삽입 (테스트용)
-- 주요 종목 샘플 (실제 데이터는 Python 스크립트로 수집)
INSERT INTO stocks (code, name, market, sector) VALUES
    ('005930', '삼성전자', 'KOSPI', '전기전자'),
    ('000660', 'SK하이닉스', 'KOSPI', '전기전자'),
    ('035420', 'NAVER', 'KOSPI', '서비스업'),
    ('005380', '현대차', 'KOSPI', '운수장비'),
    ('051910', 'LG화학', 'KOSPI', '화학')
ON CONFLICT (code) DO NOTHING;

-- 완료 메시지
DO $$
BEGIN
    RAISE NOTICE '데이터베이스 초기화 완료!';
    RAISE NOTICE '테이블: stocks, prices, financials, news_summary';
    RAISE NOTICE '뷰: latest_financials, stocks_with_latest_price';
END $$;
