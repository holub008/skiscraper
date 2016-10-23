DROP TABLE skiscraper.races;

CREATE DATABASE skiscraper;
GRANT ALL PRIVILEGES ON skiscraper.* TO 'scraper'@'localhost' WITH GRANT OPTION;
CREATE TABLE skiscraper.races (rpath VARCHAR(512), rname VARCHAR(512),
                                rdate DATE, ryear VARCHAR(16), rurl VARCHAR(512), result_type VARCHAR(16));
/* create a new user to get at the table, give permissions*/
CREATE USER 'scraper'@'localhost';
SET PASSWORD FOR 'scraper'@'localhost' = PASSWORD('Compellent04');


CREATE TABLE skiscraper.structured_race_results
(
    id INT NOT NULL AUTO_INCREMENT,
    race_id INT NOT NULL,
    name VARCHAR(512),
    place VARCHAR(16),
    race_time VARCHAR(32)
)

/*test insertion into db */
INSERT INTO skiscraper.races (rpath, rname, rdate, ryear, rurl) VALUES('text/2015/test.txt','tester','2015/10/31','2015','skinnyski.com');
SELECT * FROM skiscraper.races;
DELETE FROM skiscraper.races LIMIT 100;
