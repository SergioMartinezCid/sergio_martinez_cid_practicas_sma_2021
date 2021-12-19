#!/usr/bin/env python3

import json
from spade import quit_spade
from chatbot_agent import ChatbotAgent
from user_agent import UserAgent


def main():
    # Load the json file with the crendentials
    with open('credentials.json', 'r', encoding='utf8') as creedentials_file:
        creedentials = json.load(creedentials_file)

    # Create the agents
    user = UserAgent(creedentials['user']['username'],
                            creedentials['user']['password'])
    chatbot = ChatbotAgent(creedentials['chatbot']['username'],
                            creedentials['chatbot']['password'])

    # Start the agents
    chatbot.start().result()
    user.start().result()

    # Wait until the execution is finished
    if user.is_alive():
        user.assist_user_behaviour.join()
    if chatbot.is_alive():
        chatbot.handle_request_behaviour.join()

    # Stop the agents, just in case
    user.stop()
    chatbot.stop()

    # Quit SPADE, just in case, clean all the resources
    quit_spade()
    print('All agents are finished')

if __name__=='__main__':
    main()
