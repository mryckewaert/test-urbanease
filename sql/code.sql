CREATE DATABASE test_urbanease
    WITH
    OWNER = postgres
    ENCODING = 'UTF8'
    LC_COLLATE = 'C'
    LC_CTYPE = 'C'
    TABLESPACE = pg_default
    CONNECTION LIMIT = -1
    IS_TEMPLATE = False;
	
-- Create table offer;

CREATE TABLE offer (
	offer_id SERIAL PRIMARY KEY,
	title TEXT UNIQUE,
	url TEXT NOT NULL,
	price INT NOT NULL,
	surface INT
);

SELECT * FROM offer;