import json
import logging
import re
import urllib
from functools import reduce
from pathlib import Path
from time import gmtime, strftime
import requests
from bs4 import BeautifulSoup
from spade import agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template
from sqlalchemy.sql.expression import select, func
from app.exceptions import InitFailedException
from .loaded_answers import loaded_answers as la
from .const import API_KEYS_FILE, ENVIRONMENT_FOLDER, \
    DEFAULT_GIF_COUNT, LOGGER_NAME, MAX_GIF_COUNT, TIMEOUT_SECONDS, TRACEBACK_LOGGER_NAME
from .database import db, BaseUrl, FunctionalityRegex, Joke
from .functionality import Functionality

logger = logging.getLogger(LOGGER_NAME)
traceback_logger = logging.getLogger(TRACEBACK_LOGGER_NAME)

class ChatbotAgent(agent.Agent):
    def __init__(self, jid, password, user_address, verify_security=False):
        super().__init__(jid, password, verify_security=verify_security)
        self.user_address = user_address

        logger.debug('Loading API keys')
        with open(API_KEYS_FILE, 'r', encoding='utf-8') as api_keys_file:
            api_keys = json.load(api_keys_file)
        self.gif_api_key = api_keys['tenor.com']

        logger.debug('Loading base URLs')
        with db.get_new_session() as session:
            search_gifs_url_result = session.execute(select(BaseUrl.url)
                .where(BaseUrl.id == 'SEARCH_GIFS_URL')).first()
            search_people_url_result = session.execute(select(BaseUrl.url)
                .where(BaseUrl.id == 'SEARCH_PEOPLE_URL')).first()
            if search_gifs_url_result is None or search_people_url_result is None:
                raise InitFailedException()
            self.search_gifs_url = search_gifs_url_result[0]
            self.search_people_url = search_people_url_result[0]

    async def setup(self):
        template = Template()
        template.set_metadata('performative', 'request')
        template.set_metadata('language', 'chatbot-query')
        self.add_behaviour(HandleRequestsBehaviour(), template)
        self.add_behaviour(SendGreetingBehaviour())

    async def send_response_message(self, behaviour, body,
                    performative='inform', language='chatbot-response'):
        message = Message(to=self.user_address)
        message.set_metadata('performative',performative)
        message.set_metadata('language',language)
        message.body = body
        logger.debug('Sending message to user agent: %s', str(message))
        await behaviour.send(message)

class SendGreetingBehaviour(OneShotBehaviour):
    async def run(self):
        self.agent: ChatbotAgent
        await self.agent.send_response_message(self, la['BOT_GREETING'],
            performative='inform', language='chatbot-greeting')

class HandleRequestsBehaviour(CyclicBehaviour):
    #  pylint: disable=unnecessary-lambda
    functionality_to_behaviour = {
        Functionality.SEND_FUNCTIONALITY:
            (lambda _: SendFunctionalityBehaviour()),
        Functionality.SHOW_TIME:
            (lambda _: ShowTimeBehaviour()),
        Functionality.SEARCH_PERSON_INFO:
            (lambda groups: SearchPersonInfoBehaviour(groups)),
        Functionality.MAKE_FILE:
            (lambda groups: MakeFileBehaviour(groups)),
        Functionality.DOWNLOAD_GIFS:
            (lambda groups: DownloadGifsBehaviour(groups)),
        Functionality.TELL_JOKE:
            (lambda groups: TellJokeBehaviour(groups)),
        Functionality.SEND_EXIT:
            (lambda _: SendExitBehaviour()),
    }
    #  pylint: enable=unnecessary-lambda

    def __init__(self):
        super().__init__()
        logger.debug('Loading functionality regex from database')
        with db.get_new_session() as session:
            raw_functionality_regex = session.execute(
                select(FunctionalityRegex.regex, FunctionalityRegex.functionality)).all()
            self.functionality_regex = dict(map(lambda x: (re.compile(x[0], re.I), x[1]),
                                                raw_functionality_regex))

    async def run(self):
        logger.debug('Waiting for user request')
        message = await self.receive(TIMEOUT_SECONDS)
        if message is None:
            logger.debug('Timeout exceeded while waiting for user request')
            return
        logger.debug('Received user request: %s', str(message))
        action = self.get_functionality_from_message(message.body)
        self.agent.add_behaviour(action)
        await action.join()

    def get_functionality_from_message(self, message) -> OneShotBehaviour:
        for regex, functionality in self.functionality_regex.items():
            match = regex.match(message)
            if match is not None:
                logger.debug('Selected functionality %s', str(functionality))
                return self.functionality_to_behaviour[functionality](match.groups())
        return NotUnderstoodBehaviour()

class SendFunctionalityBehaviour(OneShotBehaviour):
    async def run(self):
        logger.debug('Sending functionality list')
        await self.agent.send_response_message(self, la['AVAILABLE_FUNCTIONALITY'])

class ShowTimeBehaviour(OneShotBehaviour):
    async def run(self):
        logger.debug('Sending current time')
        await self.agent.send_response_message(self,
            la['SHOW_TIME_F'].format(time=strftime("%d-%m-%Y %H:%M:%S", gmtime())))

class SearchPersonInfoBehaviour(OneShotBehaviour):
    def __init__(self, groups):
        super().__init__()
        self.name = groups[0]

    async def run(self):
        logger.debug('Scrapping for information about %s', self.name)
        res = requests.get(self.agent.search_people_url +
            f'?search={urllib.parse.quote(self.name)}')
        if res.status_code != 200:
            logger.debug('Failed to reach server, code %s', res.status_code)
            await self.agent.send_response_message(self, la['NETWORK_ERROR'])
            return
        html = BeautifulSoup(res.content, 'html.parser')

        # Check whether the result is ambiguous
        if html.find('div', {'id': 'disambigbox'}) is not None:
            logger.debug('An ambiguous result was found')
            await self.agent.send_response_message(self,
                la['AMBIGUOUS_PERSON_F'].format(name=self.name))
            return

        content_text = html.find('div', {'id': 'mw-content-text'})

        # Use a more general id if the previous one stops working
        if content_text is None:
            logger.debug('Initial web scrapping strategy failed. Trying alternative strategy...')
            content = html.find('div', {'id': 'bodyContent'})
            content_text = reduce(lambda x, y: x if len(x.text) > len(y.text) else y,
                                    content.children)

        first_paragraph = next(filter(lambda x: len(x.text) > 5, content_text.find_all('p')))
        if first_paragraph is not None:
            logger.debug('There is a first paragraph in the page')
            match = re.match(r'The page \".*\" does not exist\. You can ask for it to be created',
                                first_paragraph.text.strip())
            if match is None:
                logger.debug('Cleaning text in the first paragraph')
                await self.agent.send_response_message(self,
                    re.sub(r'\[[^\[]*\]', '', first_paragraph.text).strip())
                return
        await self.agent.send_response_message(self,
            la['NO_INFORMATION_PERSON_F'].format(name=self.name))

class MakeFileBehaviour(OneShotBehaviour):
    def __init__(self, groups):
        super().__init__()
        self.name = groups[0]
        self.file_contents = groups[1] if len(groups) > 1 else None

    async def run(self):
        file = Path(f'{ENVIRONMENT_FOLDER}/{self.name}')
        parent_folder = Path(ENVIRONMENT_FOLDER).resolve()

        try:
            if Path(self.name).is_absolute(): # Check if input was an absolute path
                message_body = la['ABSOLUTE_PATH_F'].format(name=self.name)
            elif file.exists():
                if file.is_file():
                    message_body = la['FILE_EXISTS_F'].format(name=self.name)
                elif file.exists() and file.is_dir():
                    message_body = la['IS_FOLDER_F'].format(name=self.name)
            elif not file.resolve().is_relative_to(parent_folder):
                message_body = la['ACCESS_PARENT_ENVIRONMENT_F'].format(name=self.name)
            else:
                # Create empty file
                logger.debug('No error found in the request')
                file = file.resolve()

                if not file.parent.exists():
                    logger.debug('Creating parent folder containing the file')
                    file.parent.mkdir(parents=True, exist_ok=True)

                with file.open('w', encoding='utf-8') as file:
                    if self.file_contents is not None:
                        file.write(self.file_contents)
                message_body = la['CREATE_FILE_SUCCESS_F'].format(name=self.name)
        except OSError as error:
            logger.info('Unexpected error: %s', str(error))
            traceback_logger.info('', stack_info=True)
            message_body = error.strerror
        await self.agent.send_response_message(self, message_body)

class DownloadGifsBehaviour(OneShotBehaviour):
    def __init__(self, groups):
        super().__init__()
        self.gif_count = int(groups[0]) if groups[0].isdecimal() \
                         else DEFAULT_GIF_COUNT
        self.search_text = groups[1]

    async def run(self):
        if self.gif_count > MAX_GIF_COUNT:
            await self.agent.send_response_message(self, la['MAX_GIF_COUNT'])
            return

        res = requests.get(self.agent.search_gifs_url +
                    f'?key={self.agent.gif_api_key}&q={self.search_text}&limit={self.gif_count}' +
                    '&contentfilter=medium&media_filter=minimal')
        if res.status_code != 200:
            logger.debug('Failed to reach server, code %s', res.status_code)
            await self.agent.send_response_message(self, la['NETWORK_ERROR'])
            return

        results = res.json()['results']

        if len(results) <= 0:
            await self.agent.send_response_message(self,
                la['NO_RESULTS_F'].format(search_term=self.search_text))
            return

        folder_name = ''.join(x if x.isalnum() or x in '-_.() ' else '_' for x in self.search_text)
        result_urls = map(lambda result: result['media'][0]['gif']['url'], results)
        for index, result_url in enumerate(result_urls):
            res = requests.get(result_url, stream=True)

            if res.status_code != 200:
                await self.agent.send_response_message(self, la['NETWORK_ERROR'])
                return

            gif_path = Path(f'{ENVIRONMENT_FOLDER}/{folder_name}/{index+1}.gif').resolve()
            if not gif_path.parent.exists():
                logger.debug('Creating parent folder containing the file')
                gif_path.parent.mkdir(parents=True, exist_ok=True)
            with gif_path.open('wb') as gif_file:
                logger.debug('Writing file in chunks')
                for chunk in res.iter_content(chunk_size=1024):
                    if chunk:
                        gif_file.write(chunk)

        await self.agent.send_response_message(self,
            la['DOWNLOAD_GIFS_SUCCESS_F'].format(search_text=self.search_text))

class TellJokeBehaviour(OneShotBehaviour):
    def __init__(self, groups):
        super().__init__()
        self.is_new = len(groups) > 0

    async def run(self):
        stmt = select(Joke).order_by(func.random()).limit(1)
        if self.is_new:
            logger.debug('Filtering only new jokes')
            stmt = stmt.where(Joke.is_new)

        with db.get_new_session() as session:
            joke_row = session.execute(stmt).first()

            if joke_row is None:
                error_message = la['ERROR_NO_NEW_JOKES'] if self.is_new else \
                                la['ERROR_NO_JOKES']
                await self.agent.send_response_message(self,error_message)
            else:
                joke = joke_row[0]
                logger.debug('Marking joke as old in the database')
                joke.is_new = False
                session.commit()
                await self.agent.send_response_message(self, joke.joke)

class SendExitBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, '',
            performative='request', language='chatbot-exit')
        await self.agent.stop()

class NotUnderstoodBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, la['MESSAGE_NOT_UNDERSTOOD'])
