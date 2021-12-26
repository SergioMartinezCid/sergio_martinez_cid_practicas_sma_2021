import json
# The following import makes arrows work properly
# when writing an input
import readline #  pylint: disable=unused-import
from spade import agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.template import ORTemplate, Template
from const import AGENT_CREDENTIALS_FILE, TIMEOUT_SECONDS

class UserAgent(agent.Agent):
    def __init__(self, jid, password, verify_security=False):
        super().__init__(jid, password, verify_security=verify_security)

        with open(AGENT_CREDENTIALS_FILE, 'r', encoding='utf8') as creedentials_file:
            creedentials = json.load(creedentials_file)
        self.chatbot_address = creedentials['chatbot']['username']

    async def setup(self):
        template = Template()
        template.set_metadata('performative', 'inform')
        template.set_metadata('language', 'chatbot-greeting')
        self.add_behaviour(AwaitGreetingBehaviour(), template)

class AwaitGreetingBehaviour(OneShotBehaviour):
    async def run(self):
        response = await self.receive(TIMEOUT_SECONDS)
        if response is None:
            return
        print(f'Bot says: {response.body}')

        template_final = Template()
        template_final.set_metadata('performative', 'inform')
        template_final.set_metadata('language', 'chatbot-response')

        template_intermediate = Template()
        template_intermediate.set_metadata('performative', 'inform')
        template_intermediate.set_metadata('language', 'chatbot-intermediate-response')

        template = ORTemplate(template_final, template_intermediate)
        self.agent.add_behaviour(AssistUserBehaviour(), template)

        template = Template()
        template.set_metadata('performative', 'request')
        template.set_metadata('language', 'chatbot-exit')
        self.agent.add_behaviour(ReceiveExitBehaviour(), template)

class AssistUserBehaviour(CyclicBehaviour):
    def __init__(self):
        super().__init__()
        self.is_intermediate_query = False

    async def run(self):
        try:
            message_content = input('You say: ')
        except EOFError:
            message_content = ''
        message = Message(to=self.agent.chatbot_address)
        message.set_metadata('performative', 'inform')
        language = 'chatbot-intermediate-query' if self.is_intermediate_query else 'chatbot-query'
        message.set_metadata('language', language)
        message.body = message_content
        await self.send(message)

        response = await self.receive(TIMEOUT_SECONDS)
        if response is None:
            return
        self.is_intermediate_query = \
            response.get_metadata('language') == 'chatbot-intermediate-response'
        print(f'Bot says: {response.body}')

class ReceiveExitBehaviour(CyclicBehaviour):
    async def run(self):
        response = await self.receive(TIMEOUT_SECONDS)
        if response is not None:
            await self.agent.stop()
