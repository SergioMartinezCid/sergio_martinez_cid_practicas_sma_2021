#!/usr/bin/env python3

import json
from spade import quit_spade
from useragent import UserAgent


def main():
    # The agent must be registered in a XMPP server

    # Load the json file with the crendentials
    with open('credentials.json', 'r', encoding='utf8') as creedentials_file:
        creedentials = json.load(creedentials_file)

        # Create the agent
        user = UserAgent(creedentials['user1']['username'],
                                creedentials['user1']['password'])

    # Start the agent
    future = user.start()
    future.result()

    # Wait until the execution is finished
    user.assist_user_behaviour.join()

    # Stop the agent
    user.stop()

    # Quit SPADE, optional, clean all the resources
    quit_spade()

    print('All agents are finished')

if __name__=='__main__':
    main()
