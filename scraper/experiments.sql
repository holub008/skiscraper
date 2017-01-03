-- create a new user to get at the tables, give permissions
CREATE USER 'scraper'@'localhost';
SET PASSWORD FOR 'scraper'@'localhost' = PASSWORD('Compellent04');
CREATE USER 'web'@'localhost';
SET PASSWORD FOR 'web'@'localhost' = PASSWORD('Compellent04');

CREATE DATABASE IF NOT EXISTS skiscraper;
GRANT ALL PRIVILEGES ON skiscraper.* TO 'scraper'@'localhost';
GRANT READ PRIVILEGES ON skiscraper.* TO 'web'@'localhost';

DROP TABLE IF EXISTS skiscraper.races;
-- todo it may be a good idea to have 1. an event table that may have sub-races 2. an extra column here pointing to any parent races (i.e. events)
-- this will make it easier (actually, just fewer requests) to determine if a race has already been processed in advance
CREATE TABLE skiscraper.races
(
    id INT NOT NULL AUTO_INCREMENT,
    rname VARCHAR(128) COLLATE utf8_unicode_ci,
    rdate VARCHAR(32) COLLATE utf8_unicode_ci,  -- todo
    ryear VARCHAR(16) COLLATE utf8_unicode_ci,
    rurl VARCHAR(512) COLLATE utf8_unicode_ci,
    result_type VARCHAR(16),
    PRIMARY KEY(id)
);

DROP TABLE IF EXISTS skiscraper.structured_race_results;
CREATE TABLE skiscraper.structured_race_results
(
    id INT NOT NULL AUTO_INCREMENT,
    race_id INT NOT NULL,
    name VARCHAR(512) COLLATE utf8_unicode_ci,
    placement VARCHAR(16) COLLATE utf8_unicode_ci,
    race_time VARCHAR(32) COLLATE utf8_unicode_ci,
    PRIMARY KEY(id)
);

DROP TABLE IF EXISTS skiscraper.unstructured_race_results;
CREATE TABLE skiscraper.unstructured_race_results
(
    id INT NOT NULL AUTO_INCREMENT,
    race_id INT NOT NULL,
    text_blob TEXT COLLATE utf8_unicode_ci,
    PRIMARY KEY(id)
);

