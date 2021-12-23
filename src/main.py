#!/usr/bin/env python3

import json
import logging
from time import sleep
from spade import quit_spade
from chatbot_agent import ChatbotAgent
from const import LOG_FILE
from user_agent import UserAgent


def main():
    logging.basicConfig(filename=LOG_FILE,
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=logging.DEBUG)
    # Load the json file with the crendentials
    with open('credentials.json', 'r', encoding='utf8') as creedentials_file:
        creedentials = json.load(creedentials_file)

    # Create the agents
    user = UserAgent(creedentials['user']['username'],
                            creedentials['user']['password'])
    chatbot = ChatbotAgent(creedentials['chatbot']['username'],
                            creedentials['chatbot']['password'])

    # Start the agents
    user.start().result()
    chatbot.start().result()

    # Wait until the execution is finished
    while chatbot.is_alive() or user.is_alive():
        try:
            sleep(1)
        except KeyboardInterrupt:
            chatbot.stop()
            user.stop()
            print()
            break

    # Stop the agents, just in case
    user.stop()
    chatbot.stop()

    # Quit SPADE, just in case, clean all the resources
    quit_spade()
    print('All agents are finished')

if __name__=='__main__':
    main()
