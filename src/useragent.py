from spade import agent
from spade.behaviour import CyclicBehaviour, OneShotBehaviour

class AssistUserBehaviour(CyclicBehaviour):
    async def run(self):
        message = input('You say: ')
        action = None
        if message.strip().lower() == 'exit':
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

class UserAgent(agent.Agent):
    def __init__(self, jid, password, verify_security=False):
        super().__init__(jid, password, verify_security=verify_security)
        self.assist_user_behaviour = None

    async def setup(self):
        print(f'[{self.jid}] Starting...')
        print('Bot says: Hi Human! What do you want?')
        self.assist_user_behaviour = AssistUserBehaviour()
        self.add_behaviour(self.assist_user_behaviour)
