import logging
# The following import makes arrows work properly
# when writing an input
#  pylint: disable=unused-import
import readline
#  pylint: enable=unused-import
from spade import agent
from spade.message import Message
from spade.behaviour import CyclicBehaviour, OneShotBehaviour
from spade.template import Template
from .loaded_answers import loaded_answers as la
from .const import TIMEOUT_SECONDS, USER_LOGGER_NAME

logger = logging.getLogger(USER_LOGGER_NAME)

class UserAgent(agent.Agent):
    def __init__(self, jid, password, chatbot_address, verify_security=False):
        super().__init__(jid, password, verify_security=verify_security)
        self.chatbot_address = chatbot_address
        self.exit_behaviour = None

    async def setup(self):
        template = Template()
        template.set_metadata('performative', 'inform')
        template.set_metadata('language', 'chatbot-greeting')
        self.add_behaviour(AwaitGreetingBehaviour(), template)

        template = Template()
        template.set_metadata('performative', 'request')
        template.set_metadata('language', 'chatbot-exit')
        self.exit_behaviour = ReceiveExitBehaviour()
        self.add_behaviour(self.exit_behaviour, template)

class AwaitGreetingBehaviour(OneShotBehaviour):
    async def run(self):
        logger.debug('Waiting for chatbot greeting')
        response = await self.receive(TIMEOUT_SECONDS)
        if response is None:
            logger.warning('Timeout exceeded while waiting for greeting')
            return
        logger.debug('Received chatbot greeting')
        print(la['BOT_ANSWER_F'].format(response=response.body))

        template = Template()
        template.set_metadata('performative', 'inform')
        template.set_metadata('language', 'chatbot-response')
        self.agent.add_behaviour(AssistUserBehaviour(), template)

class AssistUserBehaviour(CyclicBehaviour):
    async def run(self):
        try:
            message_content = input(la['USER_QUERY'])
        except EOFError:
            print()
            message_content = ''

        logger.debug('Sending request: %s', message_content)
        message = Message(to=self.agent.chatbot_address)
        message.set_metadata('performative', 'request')
        message.set_metadata('language', 'chatbot-query')
        message.body = message_content
        await self.send(message)

        logger.debug('Waiting for response from chatbot')
        response = await self.receive(TIMEOUT_SECONDS)
        if response is None:
            logger.warning('Timeout exceeded while waiting for chatbot response')
            return
        logger.debug('Received response: %s', str(response))
        print(la['BOT_ANSWER_F'].format(response=response.body))

class ReceiveExitBehaviour(CyclicBehaviour):
    async def run(self):
        response = await self.receive(TIMEOUT_SECONDS)
        if response is not None:
            logger.debug('Received exit message from chatbot')
            await self.agent.stop()
