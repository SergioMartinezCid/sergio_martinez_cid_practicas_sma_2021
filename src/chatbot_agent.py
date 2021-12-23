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
from const import ENVIRONMENT_FOLDER, SEARCH_PEOPLE_URL, TIMEOUT_SECONDS

class ChatbotAgent(agent.Agent):
    def __init__(self, jid, password, verify_security=False):
        super().__init__(jid, password, verify_security=verify_security)

        with open('credentials.json', 'r', encoding='utf8') as creedentials_file:
            creedentials = json.load(creedentials_file)
        self.user_address = creedentials['user']['username']

    async def setup(self):
        template = Template()
        template.set_metadata('performative', 'inform')
        template.set_metadata('language', 'chatbot-query')
        self.add_behaviour(HandleRequestsBehaviour(), template)
        self.add_behaviour(SendGreetingBehaviour())

class SendGreetingBehaviour(OneShotBehaviour):
    async def run(self):
        message = Message(to=self.agent.user_address)
        message.set_metadata('performative', 'inform')
        message.set_metadata('language', 'chatbot-greeting')
        message.body = 'Hi Human! What do you want?'
        await self.send(message)

class HandleRequestsBehaviour(CyclicBehaviour):
    available_queries = {
        re.compile(r'\s*show\s*me\s*the\s*time\s*', re.I):
            (lambda _: ShowTimeBehaviour()),
        re.compile(r'who\s*is\s*(\S.*)\s*', re.I):
            (lambda name: SearchPersonInfoBehaviour(name[0])),
        re.compile(r'\s*create\s*file\s*[\"\'](\S.*)[\"\']\s*', re.I):
            (lambda name: MakeFileBehaviour(name[0])),
        re.compile(r'\s*exit\s*', re.I):
            (lambda _: SendExitBehaviour()),
    }

    async def run(self):
        message = await self.receive(TIMEOUT_SECONDS)
        if message is None:
            return
        action = self.get_response_from_message(message.body)
        self.agent.add_behaviour(action)
        await action.join()

    def get_response_from_message(self, message):
        for query_regex, behaviour_factory in self.available_queries.items():
            match = query_regex.match(message)
            if match is not None:
                return behaviour_factory(match.groups())
        return NotUnderstoodBehaviour()

class ShowTimeBehaviour(OneShotBehaviour):
    async def run(self):
        message = Message(to=self.agent.user_address)
        message.set_metadata('performative', 'inform')
        message.set_metadata('language', 'chatbot-response')
        message.body = 'The time is ' + strftime("%d-%m-%Y %H:%M:%S", gmtime())
        await self.send(message)

class SearchPersonInfoBehaviour(OneShotBehaviour):
    def __init__(self, name):
        super().__init__()
        self.name = name

    async def run(self):
        req = requests.get(SEARCH_PEOPLE_URL + urllib.parse.quote(self.name))
        html = BeautifulSoup(req.content, 'html.parser')

        content_text = html.find('div', {'id': 'mw-content-text'})

        # Use a more general id if the previous one stops working
        if content_text is None:
            content = html.find('div', {'id': 'bodyContent'})
            content_text = reduce(lambda x, y: x if len(x.text) > len(y.text) else y,
                                    content.children)
        first_paragraph = next(filter(lambda x: len(x.text) > 5, content_text.find_all('p')))

        message = Message(to=self.agent.user_address)
        message.set_metadata('performative', 'inform')
        message.set_metadata('language', 'chatbot-response')

        message.body = f'No information was found about "{self.name}"'
        if first_paragraph is not None:
            match = re.match(r'The page \".*\" does not exist\. You can ask for it to be created\.',
                                first_paragraph.text.strip())
            if match is None:
                message.body = re.sub(r'\[[^\[]*\]', '', first_paragraph.text).strip()
        await self.send(message)

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
        message = Message(to=self.agent.user_address)
        message.set_metadata('performative', 'inform')
        message.set_metadata('language', 'chatbot-response')
        message.body = message_body
        await self.send(message)

class SendExitBehaviour(OneShotBehaviour):
    async def run(self):
        message = Message(to=self.agent.user_address)
        message.set_metadata('performative', 'request')
        message.set_metadata('language', 'chatbot-exit')
        message.body = ''
        await self.send(message)
        await self.agent.stop()

class NotUnderstoodBehaviour(OneShotBehaviour):
    async def run(self):
        message = Message(to=self.agent.user_address)
        message.set_metadata('performative', 'inform')
        message.set_metadata('language', 'chatbot-response')
        message.body = 'Message not understood'
        await self.send(message)
