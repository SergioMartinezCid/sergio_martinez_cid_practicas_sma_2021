#!/usr/bin/env python3

from spade import agent, quit_spade
import json

ENVIRONMENT_FOLDER = 'environment'

# SPADE instalation
# pip install spade
class DummyAgent(agent.Agent):
    async def setup(self):
        message = "[{jid}] '{message}'".format(jid = self.jid, message = input('Introduce the message: '))
        print(message)
        with open('{}/message.txt'.format(ENVIRONMENT_FOLDER), 'w') as outFile:
            outFile.write(message)

def main():
    # The agent must be registered in a XMPP server

    # Load the json file with the crendentials
    f = open('credentials.json',)
    data = json.load(f)

    # Create the agent
    dummy = DummyAgent(data['user1']['username'],
                            data['user1']['password'])

    # Start the agent
    future = dummy.start()
    future.result()

    # Stop the agent
    dummy.stop()

    # Quit SPADE, optional, clean all the resources
    quit_spade()

if __name__=='__main__':
    main()
