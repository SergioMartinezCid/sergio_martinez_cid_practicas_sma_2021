-- Base URLs
CREATE TABLE base_url (
    id  VARCHAR ( 50 ) PRIMARY KEY,
    url  VARCHAR ( 255 ) UNIQUE NOT NULL
);

INSERT INTO base_url VALUES
	('SEARCH_PEOPLE_URL', 'https://en.wikipedia.org/w/index.php'),
	('SEARCH_GIFS_URL', 'https://g.tenor.com/v1/search'),
	('SEARCH_JOKES_URL', 'https://api.jokes.one/jod');
