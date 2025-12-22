-- Massive write load: Insert 10,000 transactions as SEPARATE transactions
-- Mỗi INSERT là 1 transaction riêng biệt để có thể replicate từng phần
DO $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1..10000 LOOP
        -- Mỗi INSERT + COMMIT là 1 transaction riêng
        EXECUTE 'INSERT INTO transactions (value) VALUES (''BigTransaction-' || i || ''')';
        COMMIT; -- Commit ngay sau mỗi insert
        PERFORM pg_sleep(0.0001); -- 0.1ms delay
    END LOOP;
END $$;
