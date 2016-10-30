DROP TABLE skiscraper.races;

CREATE DATABASE IF NOT EXISTS skiscraper;
GRANT ALL PRIVILEGES ON skiscraper.* TO 'scraper'@'localhost' WITH GRANT OPTION;
DROP TABLE IF EXISTS skiscraper.races;
CREATE TABLE skiscraper.races
(
    id INT NOT NULL AUTO_INCREMENT,
    rpath VARCHAR(512), rname VARCHAR(512),
    rdate VARCHAR(32),  -- todo
    ryear VARCHAR(16),
    rurl VARCHAR(512),
    result_type VARCHAR(16),
    PRIMARY KEY(id)
);

DROP TABLE IF EXISTS skiscraper.structured_race_results;
CREATE TABLE skiscraper.structured_race_results
(
    id INT NOT NULL AUTO_INCREMENT,
    race_id INT NOT NULL,
    name VARCHAR(512),
    placement VARCHAR(16),
    race_time VARCHAR(32),
    PRIMARY KEY(id)
);


-- create a new user to get at the tables, give permissions
CREATE USER 'scraper'@'localhost';
SET PASSWORD FOR 'scraper'@'localhost' = PASSWORD('Compellent04');





-- test insertion into race db
INSERT INTO skiscraper.races (rpath, rname, rdate, ryear, rurl) VALUES('text/2015/test.txt','tester','2015/10/31','2015','skinnyski.com');
SELECT * FROM skiscraper.races;
DELETE FROM skiscraper.races LIMIT 100;
