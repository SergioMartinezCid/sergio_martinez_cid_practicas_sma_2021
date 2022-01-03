from app.const import DEFAULT_JOKES_FILE
from app.functionality import Functionality

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
        {'regex':
            r'\s*(?:create|make)\s+file\s+(?:named\s+)?\'(.+?)\'(?:\s+containing\s+\'(.+?)\')?\s*$',
            'functionality': Functionality.MAKE_FILE},
        {'regex': r'\s*download\s+(\d+|some)\s+gifs\s+(?:about|of)\s+(\S.*)\s*$',
            'functionality': Functionality.DOWNLOAD_GIFS},
        {'regex': r'\s*tell\s+(?:me\s+)?a\s+(new\s+)?joke\s*$',
            'functionality': Functionality.TELL_JOKE},
        {'regex': r'\s*exit\s*$',
            'functionality': Functionality.SEND_EXIT},
    ]

def get_answers():
    return [
        # General
        {'id': 'AGENTS_FINISHED', 'text': 'All agents are finished'},
        {'id': 'BOT_ANSWER_F', 'text': 'Bot says: {response}'},
        {'id': 'USER_QUERY', 'text': 'You say: '},
        {'id': 'BOT_GREETING', 'text': 'Hi Human! What do you want?'},
        {'id': 'MESSAGE_NOT_UNDERSTOOD', 'text':
            'Message not understood. Try asking me \'What can you do?\''},
        {'id': 'NETWORK_ERROR', 'text': 'An error ocurred while accesing the internet. Try later'},

        # Available functionality
        {'id': 'AVAILABLE_FUNCTIONALITY', 'text': '''I can do the following things
    Show you this message: What can you do?
    Show you the time: Show me the time
    Look for information about someone: Who is Barack Obama?
    Create an empty file: Create file 'filename' /  Create file 'filename' containing 'content'
    Download gifs: Download 10 gifs of potatoes /  Download some gifs of potatoes
    Tell a joke: Tell me a joke / Tell me a new joke 
    End the execution: exit'''},

        # Show time
        {'id': 'SHOW_TIME_F', 'text': 'The time is {time}'},

        # Search person
        {'id': 'AMBIGUOUS_PERSON_F', 'text': 'The name "{name}" is too ambiguous'},
        {'id': 'NO_INFORMATION_PERSON_F', 'text': 'No information was found about "{name}"'},

        # Create file
        {'id': 'ABSOLUTE_PATH_F',
            'text': '\'{name}\' is an absolute path, use a relative path instead'},
        {'id': 'FILE_EXISTS_F', 'text': '\'{name}\' already exists'},
        {'id': 'IS_FOLDER_F', 'text': '\'{name}\' is a folder'},
        {'id': 'ACCESS_PARENT_ENVIRONMENT_F',
            'text': '\'{name}\' should not access the parent folder of environment'},
        {'id': 'CREATE_FILE_SUCCESS_F', 'text': 'Successfully created \'{name}\''},

        # Download gifs
        {'id': 'MAX_GIF_COUNT', 'text': 'Maximum number of gifs is 50'},
        {'id': 'NO_RESULTS_F', 'text': 'No results were found about {search_text}'},
        {'id': 'DOWNLOAD_GIFS_SUCCESS_F', 'text':
            'Successfully downloaded gifs about \'{search_text}\''},

        # Tell jokes
        {'id': 'ERROR_NO_JOKES', 'text': 'There are no jokes in the database'},
        {'id': 'ERROR_NO_NEW_JOKES', 'text': 'There are no new jokes in the database'},
    ]

def get_default_jokes():
    with open(DEFAULT_JOKES_FILE, 'r', encoding='utf-8') as joke_file:
        return map(lambda joke: {'joke': joke.strip()}, joke_file.readlines())
