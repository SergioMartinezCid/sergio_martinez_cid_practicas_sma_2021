import json
from spade import agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour

class AssistUserBehaviour(CyclicBehaviour):
    def __init__(self):
        super().__init__()
        with open('credentials.json', 'r', encoding='utf8') as creedentials_file:
            creedentials = json.load(creedentials_file)
        self.chatbot_address = creedentials['chatbot']['username']

    async def run(self):
        try:
            message = input('You say: ')
        except EOFError:
            message = ''
        msg = Message(to=self.chatbot_address)
        msg.set_metadata("performative", "inform")
        msg.set_metadata("language", "chatbot")
        msg.body = message

        await self.send(msg)

class UserAgent(agent.Agent):
    def __init__(self, jid, password, verify_security=False):
        super().__init__(jid, password, verify_security=verify_security)
        self.assist_user_behaviour = None

    async def setup(self):
        self.assist_user_behaviour = AssistUserBehaviour()
        self.add_behaviour(self.assist_user_behaviour)
