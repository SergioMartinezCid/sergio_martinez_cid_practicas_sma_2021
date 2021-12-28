import json
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
from sqlalchemy.sql.expression import select, update, func
from const import API_KEYS_FILE, AGENT_CREDENTIALS_FILE, DEFAULT_GIF_COUNT, ENVIRONMENT_FOLDER
from const import TIMEOUT_SECONDS
from database import db, BaseUrl, FunctionalityRegex, Joke
from functionality import Functionality

class ChatbotAgent(agent.Agent):
    def __init__(self, jid, password, verify_security=False):
        super().__init__(jid, password, verify_security=verify_security)

        with open(AGENT_CREDENTIALS_FILE, 'r', encoding='utf8') as creedentials_file:
            creedentials = json.load(creedentials_file)
        self.user_address = creedentials['user']['username']

        with open(API_KEYS_FILE, 'r', encoding='utf-8') as api_keys_file:
            api_keys = json.load(api_keys_file)
        self.gif_api_key = api_keys['tenor.com']

        with db.get_new_session() as session:
            self.search_gifs_url = session.execute(select(BaseUrl.url)
                .where(BaseUrl.id == 'SEARCH_GIFS_URL')).first()[0]
            self.search_people_url = session.execute(select(BaseUrl.url)
                .where(BaseUrl.id == 'SEARCH_PEOPLE_URL')).first()[0]

    async def setup(self):
        template = Template()
        template.set_metadata('performative', 'inform')
        template.set_metadata('language', 'chatbot-query')
        self.add_behaviour(HandleRequestsBehaviour(), template)
        self.add_behaviour(SendGreetingBehaviour())

    async def send_response_message(self, behaviour, body,
                    performative='inform', language='chatbot-response'):
        message = Message(to=self.user_address)
        message.set_metadata('performative',performative)
        message.set_metadata('language',language)
        message.body = body
        await behaviour.send(message)

class SendGreetingBehaviour(OneShotBehaviour):
    async def run(self):
        message = Message(to=self.agent.user_address)
        message.set_metadata('performative', 'inform')
        message.set_metadata('language', 'chatbot-greeting')
        message.body = 'Hi Human! What do you want?'
        await self.send(message)

class HandleRequestsBehaviour(CyclicBehaviour):
    functionality_to_behaviour = {
        Functionality.SEND_FUNCTIONALITY:
            (lambda _: SendFunctionalityBehaviour()),
        Functionality.SHOW_TIME:
            (lambda _: ShowTimeBehaviour()),
        Functionality.SEARCH_PERSON_INFO:
            (lambda matches: SearchPersonInfoBehaviour(matches[0])),
        Functionality.MAKE_FILE:
            (lambda matches: MakeFileBehaviour(matches[0])),
        Functionality.DOWNLOAD_GIFS:
            (lambda matches: DownloadGifsBehaviour(matches[0])),
        Functionality.TELL_JOKE:
            (lambda matches: TellJokeBehaviour(matches[0])),
        Functionality.SEND_EXIT:
            (lambda _: SendExitBehaviour()),
    }

    def __init__(self):
        super().__init__()
        self.template_intermediate = Template()
        self.template_intermediate.set_metadata('performative', 'inform')
        self.template_intermediate.set_metadata('language', 'chatbot-intermediate-query')

        with db.get_new_session() as session:
            raw_functionality_regex = session.execute(
                select(FunctionalityRegex.regex, FunctionalityRegex.functionality)).all()
            self.functionality_regex = dict(map(lambda x: (re.compile(x[0], re.I), x[1]),
                                                raw_functionality_regex))

    async def run(self):
        message = await self.receive(TIMEOUT_SECONDS)
        if message is None:
            return
        action = self.get_response_from_message(message.body)
        self.agent.add_behaviour(action, self.template_intermediate)
        await action.join()

    def get_response_from_message(self, message) -> OneShotBehaviour:
        for regex, functionality in self.functionality_regex.items():
            match = regex.match(message)
            if match is not None:
                return self.functionality_to_behaviour[functionality](match.groups())
        return NotUnderstoodBehaviour()

class SendFunctionalityBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, '''I can do the following
    Show you this message: "What can you do?"
    Show you the time: "Show me the time"
    Look for information about someone: "Who is Barack Obama"
    Create an empty file: "Create file 'Very important file'"
    Download gifs: "Download gifs of potatoes"
    Tell a joke: "Tell me a joke"
    End the execution: "exit"''')

class ShowTimeBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self,
            'The time is ' + strftime("%d-%m-%Y %H:%M:%S", gmtime()))

class SearchPersonInfoBehaviour(OneShotBehaviour):
    def __init__(self, name):
        super().__init__()
        self.name = name

    async def run(self):
        res = requests.get(self.agent.search_people_url +
            f'?search={urllib.parse.quote(self.name)}')
        html = BeautifulSoup(res.content, 'html.parser')

        # Check whether the result is ambiguous
        if html.find('div', {'id': 'disambigbox'}) is not None:
            await self.agent.send_response_message(self,
                f'The name "{self.name}" is too ambiguous')
            return

        content_text = html.find('div', {'id': 'mw-content-text'})

        # Use a more general id if the previous one stops working
        if content_text is None:
            content = html.find('div', {'id': 'bodyContent'})
            content_text = reduce(lambda x, y: x if len(x.text) > len(y.text) else y,
                                    content.children)
        first_paragraph = next(filter(lambda x: len(x.text) > 5, content_text.find_all('p')))

        if first_paragraph is not None:
            match = re.match(r'The page \".*\" does not exist\. You can ask for it to be created',
                                first_paragraph.text.strip())
            if match is None:
                await self.agent.send_response_message(self,
                    re.sub(r'\[[^\[]*\]', '', first_paragraph.text).strip())
                return
        await self.agent.send_response_message(self,
            f'No information was found about "{self.name}"')

class MakeFileBehaviour(OneShotBehaviour):
    def __init__(self, name):
        super().__init__()
        self.name = name

    async def run(self):
        file = Path(f'{ENVIRONMENT_FOLDER}/{self.name}')
        parent_folder = Path(ENVIRONMENT_FOLDER).resolve()

        try:
            if Path(self.name).is_absolute(): # Check if input was an absolute path
                message_body = f'\'{self.name}\' is an absolute path, use a relative path instead'
            elif file.exists():
                if file.is_file():
                    message_body = f'\'{self.name}\' already exists'
                elif file.exists() and file.is_dir():
                    message_body = f'\'{self.name}\' is a folder'
            elif not file.resolve().is_relative_to(parent_folder):
                message_body = f'\'{self.name}\' should not access the parent folder of environment'
            else:
                # Create empty file
                file = file.resolve()

                if not file.parent.exists():
                    file.parent.mkdir(parents=True, exist_ok=True)

                with file.open('a', encoding='utf-8'):
                    pass
                message_body = f'Successfully created \'{self.name}\''
        except OSError as error:
            message_body = error.strerror
        await self.agent.send_response_message(self, message_body)

class DownloadGifsBehaviour(OneShotBehaviour):
    def __init__(self, search_text):
        super().__init__()
        self.search_text = search_text

    async def run(self):
        gif_count = await self.ask_gif_count()
        if gif_count > 50:
            await self.agent.send_response_message(self, 'Maximum number of gifs is 50')
            return

        response = requests.get(self.agent.search_gifs_url +
                    f'?key={self.agent.gif_api_key}&q={self.search_text}&limit={gif_count}' +
                    '&contentfilter=medium&media_filter=minimal') \
                .json()

        results = response['results']

        if len(results) <= 0:
            await self.agent.send_response_message(self,
                f'No results were found about {self.search_text}')
            return
        result_urls = map(lambda result: result['media'][0]['gif']['url'], results)
        for index, result_url in enumerate(result_urls):
            res = requests.get(result_url, stream=True)
            folder_name = ''.join(x if x.isalnum() or x in '-_.() ' else '_'
                for x in self.search_text)
            gif_path = Path(f'{ENVIRONMENT_FOLDER}/{folder_name}/{index+1}.gif').resolve()
            if not gif_path.parent.exists():
                gif_path.parent.mkdir(parents=True, exist_ok=True)
            with gif_path.open('wb') as gif_file:
                for chunk in res.iter_content(chunk_size=1024):
                    if chunk:
                        gif_file.write(chunk)

        await self.agent.send_response_message(self,
            f'Successfully downloaded gifs about \'{self.search_text}\'')

    async def ask_gif_count(self):
        gif_count = None
        ask_message = 'How many gifs?'
        while gif_count is None or gif_count == 0 or gif_count > 50 :
            await self.agent.send_response_message(self, ask_message,
                language='chatbot-intermediate-response')
            response = await self.receive(TIMEOUT_SECONDS)
            if response:
                if response.body.isdigit():
                    gif_count = int(response.body)
                    if gif_count == 0:
                        ask_message = 'At least a gif must be downloaded\nAgain, how many gifs?'
                    elif gif_count > 50:
                        ask_message = 'No more than 50 gifs can be downloaded\n' + \
                            'Again, how many gifs?'
                elif response.body.lower().strip() == 'some':
                    gif_count = DEFAULT_GIF_COUNT
                else:
                    ask_message = 'Select a number or \'some\'\nAgain, how many gifs?'
        return gif_count

class TellJokeBehaviour(OneShotBehaviour):
    def __init__(self, is_new):
        super().__init__()
        self.is_new = is_new.strip() != ''

    async def run(self):
        stmt = select(Joke.joke).order_by(func.random()).limit(1)
        if self.is_new:
            stmt = stmt.where(Joke.is_new)

        with db.get_new_session() as session:
            joke_row = session.execute(stmt).first()

        if joke_row is None:
            error_message = 'There are no new jokes in the database' if self.is_new else \
                            'There are no jokes in the database'
            await self.agent.send_response_message(self,error_message)
        else:
            joke = joke_row[0]
            with db.get_new_session() as session:
                session.execute(update(Joke).where(Joke.joke == joke).values(is_new=False))
                session.commit()
            await self.agent.send_response_message(self, joke)

class SendExitBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, '',
            performative='request', language='chatbot-exit')
        await self.agent.stop()

class NotUnderstoodBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, 'Message not understood')
