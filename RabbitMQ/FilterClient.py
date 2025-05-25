from rapi import RabbitMQ_ClientAPI
import random

# Configuration parameters
RABBITMQ_DIR = '127.0.0.1'
INSULT_FILTER_QUEUE = 'insult_filter'

# List of phrases with or without insults
_insults = ["You absolute buffoon, always acting like a total clown and making everyone around you cringe with your dimwit antics, you complete nincompoop who can't even tie his own shoelaces.",
            "Honestly, you're such a dullard and a nitwit that it's amazing you manage to breathe without causing some sort of catastrophe, you half-witted scatterbrain with the intelligence of a turnip.",
            "Listening to your stupidity is like hearing a bunch of buffoons trying to solve a simple problem, you knuckleheaded doofus who never learns from their idiotic mistakes, you utter ninny.",
            "You dimwit, you clueless nincompoop, your brain is so mushy and pudding-like that I wonder how you even function in everyday life, you scatterbrained fool with no common sense at all.",
            "You absolute simpleton, always acting like a total moron and never catching on to anything, you nitwit of a bonehead who seems to exist solely to embarrass himself with every word he speaks.",
            "You complete blockhead, always stumbling through life like a buffoon and proving time and again that you're nothing more than a dullard with the mental capacity of a lizard, you utter nincompoop.",
            "Honestly, you’re such a scatterbrained dimwit and a total ninnyhammer that I wouldn’t trust you to pour water out of a boot even if the instructions were on the heel, you doofus.",
            "Your mind is a total mushbrain, you clueless nincompoop, and your inability to understand simple things makes you the perfect example of a bonehead and a half-wit combined, you ignoramus.",
            "Listening to your nonsense is like hearing a bunch of fools trying to solve a puzzle with half the pieces missing, you knuckleheaded nitwit who’s always a step behind everyone else, you maroon.",
            "You are a hopeless simpleton and a true scatterbrained fool, a dullard who manages to bungle basic tasks and make a fool of himself every time you open your mouth, you ninnyhammer.",
            "Pardon my intromission, gentleman, but I must request you to empty the compartments of your pantaloons."
]

if __name__=='__main__':
    print(" [*] Starting connection to RabbitMQ...")
    rapi = RabbitMQ_ClientAPI(host=RABBITMQ_DIR, method_queue=INSULT_FILTER_QUEUE)

    print(" [*] Testing some sentences to check if the filter is working:")
    for _ in range(6):
        phrase = random.choice(_insults)
        filtered= rapi.call("filter", phrase)
        print("   [x] Original: ", phrase)
        print("   [x] Filtered: ", filtered)
    phrase = _insults[len(_insults)-1]
    filtered= rapi.call("filter", phrase)
    print("   [x] Original: ", phrase)
    print("   [x] Filtered: ", filtered)

    print(" [*] Retrieving the history of corrections made:")
    print(rapi.call("getHistory"))