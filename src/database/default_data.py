from const import DEFAULT_JOKES_FILE
from functionality import Functionality

def get_default_base_urls():
    return [
        {'id': 'SEARCH_PEOPLE_URL', 'url': 'https://en.wikipedia.org/w/index.php'},
        {'id': 'SEARCH_GIFS_URL', 'url': 'https://g.tenor.com/v1/search'}
    ]

def get_default_functionality_regex():
    return [
        {'regex': r'\s*what\s+can\s+you\s+do\s*\??\s*$',
            'functionality': Functionality.SEND_FUNCTIONALITY},
        {'regex': r'\s*show\s+me\s+the\s+time\s*$',
            'functionality': Functionality.SHOW_TIME},
        {'regex': r'\s*who\s+is\s+(\S.*?)\s*\??\s*$',
            'functionality': Functionality.SEARCH_PERSON_INFO},
        {'regex': r'\s*(?:create|make)\s+file\s+\'(\S.*)\'\s*$',
            'functionality': Functionality.MAKE_FILE},
        {'regex': r'\s*download\s+gifs\s+(?:about|of)\s+(\S.*)\s*$',
            'functionality': Functionality.DOWNLOAD_GIFS},
        {'regex': r'\s*tell\s+(?:me\s+)?a\s+(new\s+|)joke\s*$',
            'functionality': Functionality.TELL_JOKE},
        {'regex': r'\s*exit\s*$',
            'functionality': Functionality.SEND_EXIT}
    ]

def get_default_jokes():
    with open(DEFAULT_JOKES_FILE, 'r', encoding='utf-8') as joke_file:
        return map(lambda joke: {'joke': joke.strip()}, joke_file.readlines())
