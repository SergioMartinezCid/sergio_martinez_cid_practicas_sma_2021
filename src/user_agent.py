import json
# The following import makes arrows work properly
# when writing an input
import readline #  pylint: disable=unused-import
from spade import agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.template import Template

class UserAgent(agent.Agent):
    def __init__(self, jid, password, verify_security=False):
        super().__init__(jid, password, verify_security=verify_security)

        with open('credentials.json', 'r', encoding='utf8') as creedentials_file:
            creedentials = json.load(creedentials_file)
        self.chatbot_address = creedentials['chatbot']['username']

    async def setup(self):
        template = Template()
        template.set_metadata('performative', 'inform')
        template.set_metadata('language', 'chatbot-greeting')
        self.add_behaviour(AwaitGreetingBehaviour(), template)

class AwaitGreetingBehaviour(OneShotBehaviour):
    async def run(self):
        response = await self.receive(10000)
        if response is None:
            return
        print(f'Bot says: {response.body}')

        template = Template()
        template.set_metadata('performative', 'inform')
        template.set_metadata('language', 'chatbot-response')
        self.agent.add_behaviour(AssistUserBehaviour(), template)

        template = Template()
        template.set_metadata('performative', 'request')
        template.set_metadata('language', 'chatbot-exit')
        self.agent.add_behaviour(ReceiveExitBehaviour(), template)

class AssistUserBehaviour(CyclicBehaviour):
    async def run(self):
        try:
            message_content = input('You say: ')
        except EOFError:
            message_content = ''
        message = Message(to=self.agent.chatbot_address)
        message.set_metadata('performative', 'inform')
        message.set_metadata('language', 'chatbot-query')
        message.body = message_content
        await self.send(message)

        response = await self.receive(10000)
        if response is None:
            return
        print(f'Bot says: {response.body}')

class ReceiveExitBehaviour(CyclicBehaviour):
    async def run(self):
        response = await self.receive(10000)
        if response is not None:
            await self.agent.stop()
