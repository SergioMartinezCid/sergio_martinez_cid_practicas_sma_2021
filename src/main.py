#!/usr/bin/env python3

import json
import logging
from time import sleep
from spade import quit_spade
from app.chatbot_agent import ChatbotAgent
from app.const import AGENT_CREDENTIALS_FILE, LOG_FILE
from app.database import db
from app.loaded_answers import loaded_answers as la
from app.user_agent import UserAgent


def main():
    # Configure logging
    level = logging.INFO
    logging.basicConfig(filename=LOG_FILE,
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=level)
    logging.getLogger('sqlalchemy').setLevel(level)

    # Load the database
    db.initialize_connection()
    db.seed_data()
    la.load_answers_from_database()

    # Load the json file with the crendentials
    with open(AGENT_CREDENTIALS_FILE, 'r', encoding='utf8') as creedentials_file:
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
            print()
            break

    # Quit SPADE, just in case, clean all the resources
    user.stop()
    chatbot.stop()

    quit_spade()
    print(la['AGENTS_FINISHED'])

    # Disable logging before shutdown to avoid async logging
    # https://bugs.python.org/issue26789 (Upgrading to python 3.10
    # is not viable, since SPADE has some issues with it)
    logging.disable()

if __name__=='__main__':
    main()
