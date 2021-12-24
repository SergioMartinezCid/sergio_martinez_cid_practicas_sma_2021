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
from const import SEARCH_GIFS_URL, SEARCH_PEOPLE_URL, SEARCH_JOKES_URL
from const import ENVIRONMENT_FOLDER, TIMEOUT_SECONDS

class ChatbotAgent(agent.Agent):
    def __init__(self, jid, password, verify_security=False):
        super().__init__(jid, password, verify_security=verify_security)

        with open('credentials.json', 'r', encoding='utf8') as creedentials_file:
            creedentials = json.load(creedentials_file)
        self.user_address = creedentials['user']['username']

        with open('api_keys.json', 'r', encoding='utf-8') as api_keys_file:
            api_keys = json.load(api_keys_file)
        self.gif_api_key = api_keys['tenor.com']

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
    available_queries = {
        re.compile(r'\s*what\s+can\s+you\s+do\s*\??\s*$', re.I):
            (lambda _: SendFunctionalityBehaviour()),
        re.compile(r'\s*show\s+me\s+the\s+time\s*$', re.I):
            (lambda _: ShowTimeBehaviour()),
        re.compile(r'\s*who\s+is\s+(\S.*?)\s*\??\s*$', re.I):
            (lambda matches: SearchPersonInfoBehaviour(matches[0])),
        re.compile(r'\s*(?:create|make)\s+file\s+\'(\S.*)\'\s*$', re.I):
            (lambda matches: MakeFileBehaviour(matches[0])),
        re.compile(r'\s*(?:download\s)?\s*(\d+|some)\s+gifs\s+(?:about|of)\s+(\S.*)\s*$', re.I):
            (lambda matches: DownloadGifsBehaviour(matches[0], matches[1])),
        re.compile(r'\s*tell\s+(?:me\s)?\s*a\s+joke\s*', re.I):
            (lambda _: TellJokeOfTheDayBehaviour()),
        re.compile(r'\s*exit\s*', re.I):
            (lambda _: SendExitBehaviour()),
    }

    def __init__(self):
        super().__init__()
        self.template_intermediate = Template()
        self.template_intermediate.set_metadata('performative', 'inform')
        self.template_intermediate.set_metadata('language', 'chatbot-intermediate-query')

    async def run(self):
        message = await self.receive(TIMEOUT_SECONDS)
        if message is None:
            return
        action = self.get_response_from_message(message.body)
        self.agent.add_behaviour(action, self.template_intermediate)
        await action.join()

    def get_response_from_message(self, message) -> OneShotBehaviour:
        for query_regex, behaviour_factory in self.available_queries.items():
            match = query_regex.match(message)
            if match is not None:
                return behaviour_factory(match.groups())
        return NotUnderstoodBehaviour()

class SendFunctionalityBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, '''I can do the following
    Show you this message: "What can you do?"
    Show you the time: "Show me the time"
    Look for information about someone: "Who is Barack Obama"
    Create an empty file: "Create file 'Very important file'"
    Download gifs: "Download 10 gifs of potatoes"
    Tell the joke of the day: "Tell me a joke"
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
        res = requests.get(SEARCH_PEOPLE_URL + f'?search={urllib.parse.quote(self.name)}')
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
    def __init__(self, gif_count, search_text):
        super().__init__()
        self.gif_count = int(gif_count) if gif_count.isdigit() else 5
        self.search_text = search_text

    async def run(self):
        if self.gif_count > 50:
            await self.agent.send_response_message(self, 'Maximum number of gifs is 50')
            return

        response = requests.get(SEARCH_GIFS_URL +
                    f'?key={self.agent.gif_api_key}&q={self.search_text}&limit={self.gif_count}' +
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

class TellJokeOfTheDayBehaviour(OneShotBehaviour):
    headers = {'content-type': 'application/json'}

    async def run(self):
        response = requests.get(SEARCH_JOKES_URL + '/categories', headers=self.headers) \
                        .json()
        if 'error' in response:
            await self.agent.send_response_message(self,
                'Too many joke requests within the last hour')
            return

        categories = response['contents']['categories']
        selected_category = await self.ask_for_category(categories)

        response = requests.get(SEARCH_JOKES_URL + f'?category={selected_category}',
                    headers=self.headers).json()

        if 'error' in response:
            await self.agent.send_response_message(self,
                'Too many joke requests within the last hour')
            return

        jokes = response['contents']['jokes']

        if len(jokes) <= 0:
            await self.agent.send_response_message(self,
                'There was an error retrieving the joke of the day')
        else:
            await self.agent.send_response_message(self,
                jokes[0]['joke']['text'].strip())

    async def ask_for_category(self, categories):
        valid_categories = set(map(lambda x: x['name'], categories))
        ask_message = 'Select a joke category:'
        for category in categories:
            ask_message += f"\n\t{category['name']}: {category['description']}"

        selected_category = ''
        while selected_category not in valid_categories:
            await self.agent.send_response_message(self, ask_message,
                language='chatbot-intermediate-response')
            response = await self.receive(TIMEOUT_SECONDS)
            if response:
                selected_category = response.body
        return selected_category

class SendExitBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, '',
            performative='request', language='chatbot-exit')
        await self.agent.stop()

class NotUnderstoodBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, 'Message not understood')
