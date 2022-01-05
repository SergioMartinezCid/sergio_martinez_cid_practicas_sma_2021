#!/usr/bin/env python3

import json
import logging
from spade import quit_spade
from sqlalchemy.exc import DatabaseError
from app.chatbot_agent import ChatbotAgent
from app.const import AGENT_CREDENTIALS_FILE, API_KEYS_FILE, \
    DEFAULT_LOG_FILE, CHATBOT_LOG_FILE, APP_LOGGER_NAME, TRACEBACK_LOGGER_NAME
from app.database import db
from app.exceptions import InitFailedException
from app.loaded_answers import loaded_answers as la
from app.user_agent import UserAgent

logger = logging.getLogger(APP_LOGGER_NAME)
traceback_logger = logger.getChild(TRACEBACK_LOGGER_NAME)

def main():
    # Configure library loggers
    file_log_level = logging.DEBUG
    logging.basicConfig(filename=DEFAULT_LOG_FILE,
                            filemode='a',
                            format='%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s',
                            datefmt='%H:%M:%S',
                            level=file_log_level)

    # Configure app loggers
    logger.handlers.clear()
    traceback_logger.handlers.clear()

    # App logs go to a separate file
    file_handler = logging.FileHandler(CHATBOT_LOG_FILE)
    file_handler.setLevel(file_log_level)
    formatter = logging.Formatter('%(asctime)s,%(msecs)d %(name)s %(levelname)s %(message)s')
    formatter.datefmt = '%H:%M:%S'
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    traceback_logger.addHandler(file_handler)

    # Additionally, log warnings to the console
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.ERROR)
    logger.addHandler(stream_handler)

    # Load the database
    try:
        logger.debug('Connecting to the database')
        db.initialize_connection()
        logger.debug('Seeding default data')
        db.seed_data()
        logger.debug('Loading Answers from the database')
        la.load_answers_from_database()
    except DatabaseError:
        logger.error('There was an error while connecting to the database')
        traceback_logger.error('', exc_info=True)
        return
    except Exception:
        logger.error('An unknown exception was raised')
        traceback_logger.error('', exc_info=True)
        return

    try:
        logger.debug('Loading agent credentials')
        # Load the json file with the crendentials
        with open(AGENT_CREDENTIALS_FILE, 'r', encoding='utf8') as creedentials_file:
            creedentials = json.load(creedentials_file)

        # Assert keys exist
        #  pylint: disable=pointless-statement
        creedentials['user']['username']
        creedentials['user']['password']
        creedentials['chatbot']['username']
        creedentials['chatbot']['password']
        #  pylint: enable=pointless-statement
    except FileNotFoundError:
        logger.error('File with the credentials (%s) was not found', AGENT_CREDENTIALS_FILE)
        traceback_logger.error('', exc_info=True)
        return
    except (json.decoder.JSONDecodeError, KeyError):
        logger.error('File with the credentials (%s) does not have the appropriate formatting \
(see the sample file)', AGENT_CREDENTIALS_FILE)
        traceback_logger.error('', exc_info=True)
        return

    try:
        # Create the agents
        logger.debug('Creating agents')
        user = UserAgent(creedentials['user']['username'],
                            creedentials['user']['password'],
                            creedentials['chatbot']['username'])
        chatbot = ChatbotAgent(creedentials['chatbot']['username'],
                            creedentials['chatbot']['password'],
                            creedentials['user']['username'])
    except FileNotFoundError:
        logger.error('File with the API keys (%s) was not found', AGENT_CREDENTIALS_FILE)
        traceback_logger.error('', exc_info=True)
        return
    except (json.decoder.JSONDecodeError, KeyError):
        logger.error('File with the API keys (%s) does not have the appropriate formatting \
(see the sample file)', API_KEYS_FILE)
        traceback_logger.error('', exc_info=True)
        return
    except DatabaseError:
        logger.error('There was an error while connecting to the database')
        traceback_logger.error('', exc_info=True)
        return
    except InitFailedException:
        logger.error('Base URLs could not be loaded from the database')
        traceback_logger.error('', exc_info=True)
        return

    try:
        # Start the agents
        logger.debug('Starting agents agents')
        user.start().result()
        chatbot.start().result()

        # Wait until the execution is finished
        user.exit_behaviour.join()
    except KeyboardInterrupt:
        print()
    except DatabaseError:
        logger.error('There was an error while connecting to the database')
        traceback_logger.error('', exc_info=True)
        return
    except Exception:
        logger.error('An unknown exception was raised')
        traceback_logger.error('', exc_info=True)
        return

    # Quit SPADE, just in case, clean all the resources
    logger.debug('Stopping execution')
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
