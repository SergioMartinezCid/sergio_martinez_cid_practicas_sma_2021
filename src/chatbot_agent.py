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
        re.compile(r'\s*create\s+file\s+\'(\S.*)\'\s*$', re.I):
            (lambda matches: MakeFileBehaviour(matches[0])),
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

class SendFunctionalityBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, '''I can do the following
    Show you this message: "What can you do?"
    Show you the time: "Show me the time"
    Look for information about someone: "Who is Barack Obama"
    Create an empty file: "Create file 'Very important file'"
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
        req = requests.get(SEARCH_PEOPLE_URL + urllib.parse.quote(self.name))
        html = BeautifulSoup(req.content, 'html.parser')

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


class SendExitBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, '',
            performative='request', language='chatbot-exit')
        await self.agent.stop()

class NotUnderstoodBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.send_response_message(self, 'Message not understood')
