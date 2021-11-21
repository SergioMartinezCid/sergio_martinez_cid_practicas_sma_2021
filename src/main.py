from spade import agent, quit_spade
import json
import time

# SPADE instalation
# pip install spade
class DummyAgent(agent.Agent):
    async def setup(self):
        print("Hello World! I'm agent {}".format(str(self.jid)))

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
