-- High write load script: Insert 1000 transactions with delay to create replication lag
DO $$
DECLARE
    i INT;
BEGIN
    FOR i IN 1..1000 LOOP
        INSERT INTO transactions (value) VALUES ('Transaction-' || i);
        PERFORM pg_sleep(0.0005); -- 0.5ms delay (faster inserts)
    END LOOP;
END $$;
