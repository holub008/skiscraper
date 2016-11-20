-- create a new user to get at the tables, give permissions
CREATE USER 'scraper'@'localhost';
SET PASSWORD FOR 'scraper'@'localhost' = PASSWORD('Compellent04');
CREATE USER 'web'@'localhost';
SET PASSWORD FOR 'web'@'localhost' = PASSWORD('Compellent04');

CREATE DATABASE IF NOT EXISTS skiscraper;
GRANT ALL PRIVILEGES ON skiscraper.* TO 'scraper'@'localhost';
GRANT READ PRIVILEGES ON skiscraper.* TO 'web'@'localhost';

DROP TABLE IF EXISTS skiscraper.races;
CREATE TABLE skiscraper.races
(
    id INT NOT NULL AUTO_INCREMENT,
    rname VARCHAR(128),
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

DROP TABLE IF EXISTS skiscraper.unstructured_race_results;
CREATE TABLE skiscraper.unstructured_race_results
(
    id INT NOT NULL AUTO_INCREMENT,
    race_id INT NOT NULL,
    text_blob TEXT,
    PRIMARY KEY(id)
);

