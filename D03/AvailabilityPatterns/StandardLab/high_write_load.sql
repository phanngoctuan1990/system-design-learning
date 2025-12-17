-- High write load script: Insert 1000 transactions
DO $$
BEGIN
  FOR i IN 1..1000 LOOP
    INSERT INTO transactions (value) VALUES ('Transaction-' || i);
  END LOOP;
END $$;
