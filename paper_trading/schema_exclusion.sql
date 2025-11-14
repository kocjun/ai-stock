-- ================================================
-- 제외 종목 관리 테이블
-- ================================================

-- 제외 종목 테이블
CREATE TABLE IF NOT EXISTS excluded_stocks (
    exclusion_id SERIAL PRIMARY KEY,
    code VARCHAR(10) NOT NULL,
    name VARCHAR(100),
    reason TEXT NOT NULL,
    excluded_by VARCHAR(50) DEFAULT 'user',
    excluded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    is_active BOOLEAN DEFAULT TRUE,
    notes TEXT,
    FOREIGN KEY (code) REFERENCES stocks(code) ON DELETE CASCADE,
    UNIQUE(code)
);

-- 인덱스 추가
CREATE INDEX IF NOT EXISTS idx_excluded_stocks_code ON excluded_stocks(code);
CREATE INDEX IF NOT EXISTS idx_excluded_stocks_active ON excluded_stocks(is_active);

-- 제외 종목 조회 뷰
CREATE OR REPLACE VIEW v_excluded_stocks AS
SELECT
    e.exclusion_id,
    e.code,
    COALESCE(e.name, s.name) as stock_name,
    s.sector,
    s.market as market_type,
    e.reason,
    e.excluded_by,
    e.excluded_at,
    e.notes
FROM excluded_stocks e
LEFT JOIN stocks s ON e.code = s.code
WHERE e.is_active = TRUE
ORDER BY e.excluded_at DESC;

-- 제외 종목인지 확인하는 함수
CREATE OR REPLACE FUNCTION is_stock_excluded(p_code VARCHAR(10))
RETURNS BOOLEAN AS $$
DECLARE
    v_excluded BOOLEAN;
BEGIN
    SELECT EXISTS(
        SELECT 1
        FROM excluded_stocks
        WHERE code = p_code
        AND is_active = TRUE
    ) INTO v_excluded;

    RETURN v_excluded;
END;
$$ LANGUAGE plpgsql;

-- 제외 종목을 필터링하는 함수 (종목 코드 배열을 받아 제외 종목을 제거)
CREATE OR REPLACE FUNCTION filter_excluded_stocks(p_codes VARCHAR(10)[])
RETURNS VARCHAR(10)[] AS $$
DECLARE
    v_filtered_codes VARCHAR(10)[];
BEGIN
    SELECT ARRAY(
        SELECT unnest(p_codes)
        EXCEPT
        SELECT code FROM excluded_stocks WHERE is_active = TRUE
    ) INTO v_filtered_codes;

    RETURN v_filtered_codes;
END;
$$ LANGUAGE plpgsql;

-- 제외 종목 추가 함수
CREATE OR REPLACE FUNCTION add_excluded_stock(
    p_code VARCHAR(10),
    p_reason TEXT,
    p_excluded_by VARCHAR(50) DEFAULT 'user',
    p_notes TEXT DEFAULT NULL
)
RETURNS INTEGER AS $$
DECLARE
    v_stock_name VARCHAR(100);
    v_exclusion_id INTEGER;
BEGIN
    -- 종목명 조회
    SELECT name INTO v_stock_name
    FROM stocks
    WHERE code = p_code;

    -- 이미 제외된 종목인 경우 업데이트
    IF EXISTS(SELECT 1 FROM excluded_stocks WHERE code = p_code) THEN
        UPDATE excluded_stocks
        SET is_active = TRUE,
            reason = p_reason,
            excluded_by = p_excluded_by,
            notes = p_notes,
            excluded_at = CURRENT_TIMESTAMP
        WHERE code = p_code
        RETURNING exclusion_id INTO v_exclusion_id;
    ELSE
        -- 새로운 제외 종목 추가
        INSERT INTO excluded_stocks (code, name, reason, excluded_by, notes)
        VALUES (p_code, v_stock_name, p_reason, p_excluded_by, p_notes)
        RETURNING exclusion_id INTO v_exclusion_id;
    END IF;

    RETURN v_exclusion_id;
END;
$$ LANGUAGE plpgsql;

-- 제외 종목 해제 함수
CREATE OR REPLACE FUNCTION remove_excluded_stock(p_code VARCHAR(10))
RETURNS BOOLEAN AS $$
DECLARE
    v_updated INTEGER;
BEGIN
    UPDATE excluded_stocks
    SET is_active = FALSE
    WHERE code = p_code
    AND is_active = TRUE;

    GET DIAGNOSTICS v_updated = ROW_COUNT;
    RETURN v_updated > 0;
END;
$$ LANGUAGE plpgsql;

-- 권한 설정 (필요시)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON excluded_stocks TO invest_user;
-- GRANT USAGE, SELECT ON SEQUENCE excluded_stocks_exclusion_id_seq TO invest_user;
-- GRANT EXECUTE ON FUNCTION is_stock_excluded(VARCHAR) TO invest_user;
-- GRANT EXECUTE ON FUNCTION filter_excluded_stocks(VARCHAR[]) TO invest_user;
-- GRANT EXECUTE ON FUNCTION add_excluded_stock(VARCHAR, TEXT, VARCHAR, TEXT) TO invest_user;
-- GRANT EXECUTE ON FUNCTION remove_excluded_stock(VARCHAR) TO invest_user;
