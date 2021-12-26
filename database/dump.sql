-- Base URLs
CREATE TABLE base_url (
    id  VARCHAR ( 50 ) PRIMARY KEY,
    url  VARCHAR ( 255 ) UNIQUE NOT NULL
);

INSERT INTO base_url VALUES
	('SEARCH_PEOPLE_URL', 'https://en.wikipedia.org/w/index.php'),
	('SEARCH_GIFS_URL', 'https://g.tenor.com/v1/search'),
	('SEARCH_JOKES_URL', 'https://api.jokes.one/jod');


-- Functionality regex
CREATE TYPE FUNCTIONALITY_T AS ENUM (
    'SEND_FUNCTIONALITY',
    'SHOW_TIME',
    'SEARCH_PERSON_INFO',
    'MAKE_FILE',
    'DOWNLOAD_GIFS',
    'TELL_JOKE_OF_THE_DAY',
    'SEND_EXIT'
);

CREATE TABLE functionality_regex (
	id serial PRIMARY KEY,
    regex  VARCHAR ( 255 ) UNIQUE NOT NULL,
    functionality  FUNCTIONALITY_T NOT NULL
);

INSERT INTO functionality_regex (regex, functionality) VALUES
    ('\s*what\s+can\s+you\s+do\s*\??\s*$', 'SEND_FUNCTIONALITY'),
    ('\s*show\s+me\s+the\s+time\s*$', 'SHOW_TIME'),
    ('\s*who\s+is\s+(\S.*?)\s*\??\s*$', 'SEARCH_PERSON_INFO'),
    ('\s*(?:create|make)\s+file\s+''(\S.*)''\s*$', 'MAKE_FILE'),
    ('\s*download\s+(\d+|some)\s+gifs\s+(?:about|of)\s+(\S.*)\s*$', 'DOWNLOAD_GIFS'),
    ('\s*download\s+(0*1)\s+gif\s+(?:about|of)\s+(\S.*)\s*$', 'DOWNLOAD_GIFS'),
    ('\s*tell\s+(?:me\s)?\s*a\s+joke\s*$', 'TELL_JOKE_OF_THE_DAY'),
    ('\s*exit\s*$', 'SEND_EXIT');
