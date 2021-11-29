#!/usr/bin/env python3

import json
from spade import agent, quit_spade

ENVIRONMENT_FOLDER = 'environment'

# SPADE instalation
# pip install spade
class DummyAgent(agent.Agent):
    async def setup(self):
        message = f"[{self.jid}] '{input('Introduce the message: ')}'"
        print(message)
        with open(f'{ENVIRONMENT_FOLDER}/message.txt', 'w', encoding='utf-8') as outFile:
            outFile.write(message)

def main():
    # The agent must be registered in a XMPP server

    # Load the json file with the crendentials
    with open('credentials.json', 'r', encoding='utf8') as creedentials_file:
        creedentials = json.load(creedentials_file)

        # Create the agent
        dummy = DummyAgent(creedentials['user1']['username'],
                                creedentials['user1']['password'])

    # Start the agent
    future = dummy.start()
    future.result()

    # Stop the agent
    dummy.stop()

    # Quit SPADE, optional, clean all the resources
    quit_spade()

if __name__=='__main__':
    main()
