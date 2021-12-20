import json
import re
from time import gmtime, strftime
from spade import agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.message import Message
from spade.template import Template

from const import ENVIRONMENT_FOLDER

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
        re.compile(r'who\s*is\s*(.*)\s*', re.I):
            (lambda name: SearchPersonInfoBehaviour(name[0])),
        re.compile(r'\s*create\s*file\s*named\s*(.*)\s*', re.I):
            (lambda name: MakeFileBehaviour(name[0])),
        re.compile(r'\s*exit\s*', re.I):
            (lambda _: SendExitBehaviour()),
    }

    async def run(self):
        message = await self.receive(10000)
        if message is None:
            return
        action = self.get_response_from_message(message.body)
        self.agent.add_behaviour(action)
        await action.join()

    def get_response_from_message(self, message):
        for query in self.available_queries:
            match = query.match(message)
            if match is not None:
                return self.available_queries[query](match.groups())
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
        message = Message(to=self.agent.user_address)
        message.set_metadata('performative', 'inform')
        message.set_metadata('language', 'chatbot-response')
        message.body = 'who ' + self.name
        await self.send(message)

class MakeFileBehaviour(OneShotBehaviour):
    def __init__(self, name):
        super().__init__()
        self.name = name

    async def run(self):
        try:
            with open(f'{ENVIRONMENT_FOLDER}/{self.name}', 'a', encoding='utf-8'):
                pass
            message_body = f'Successfully created \'{self.name}\''
        except OSError as e:
            message_body = e.strerror
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
