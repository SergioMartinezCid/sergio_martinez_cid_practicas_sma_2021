import time
from spade import agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.template import Template

class ChatbotAgent(agent.Agent):
    def __init__(self, jid, password, verify_security=False):
        super().__init__(jid, password, verify_security=verify_security)
        self.handle_request_behaviour = None

    async def setup(self):
        self.handle_request_behaviour = HandleRequestsBehaviour()
        template = Template()
        template.set_metadata("performative", "inform")
        template.set_metadata("language", "chatbot")
        self.add_behaviour(self.handle_request_behaviour, template)
        print('Bot says: Hi Human! What do you want?')

class HandleRequestsBehaviour(CyclicBehaviour):
    async def run(self):
        message = await self.receive()
        action = None
        if message.body.strip().lower() == 'exit':
            action = ExitBehaviour()
        else :
            action = NotUnderstoodBehaviour()
        self.agent.add_behaviour(action)
        await action.join()

class ExitBehaviour(OneShotBehaviour):
    async def run(self):
        await self.agent.stop()

class NotUnderstoodBehaviour(OneShotBehaviour):
    async def run(self):
        print('Bot says: Message not understood')
