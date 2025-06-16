import Pyro4
import random

# List of test phrases with insults (English)
TEST_PHRASES = [
    "You absolute buffoon, always acting like a total clown and making everyone around you cringe with your dimwit antics, you complete nincompoop!",
    "Honestly, you're such a dullard and a nitwit that it's amazing you manage to breathe without causing some sort of catastrophe, you half-witted scatterbrain with the intelligence of a turnip.",
    "Listening to your stupidity is like hearing a bunch of buffoons trying to solve a simple problem, you knuckleheaded doofus who never learns from their idiotic mistakes, you utter ninny.",
    "You dimwit, you clueless nincompoop, your brain is so mushy and pudding-like that I wonder how you even function in everyday life, you scatterbrained fool with no common sense at all.",
    "You absolute simpleton, always acting like a total moron and never catching on to anything, you nitwit of a bonehead who seems to exist solely to embarrass himself with every word he speaks.",
    "You complete blockhead, always stumbling through life like a buffoon and proving time and again that you're nothing more than a dullard with the mental capacity of a lizard, you utter nincompoop.",
    "Pardon my intrusion, gentleman, but I must request you to empty the compartments of your pantaloons."
]

if __name__ == "__main__":
    try:
        # Locate the Name Server
        ns = Pyro4.locateNS()
        print("[+] Name Server located.")

        # Lookup the URI of the filter server
        filter_uri = ns.lookup("example.InsultFilterServer")
        print(f"[+] Filter server found: {filter_uri}")

        # Create proxy to the remote filter server
        filter_proxy = Pyro4.Proxy(filter_uri)

        # Test filtering on random phrases
        print("\n[*] Testing sentence filtering:")
        for i in range(6):
            phrase = random.choice(TEST_PHRASES)
            print(f"--- Test {i+1} ---")
            print("Original : ", phrase)
            filtered = filter_proxy.filter_text(phrase)
            print("Filtered   : ", filtered)
            print()

        # Retrieve and display history of filtered texts
        print("[*] Retrieving filtered text history:")
        history = filter_proxy.get_filtered_texts()
        for idx, entry in enumerate(history):
            print(f"{idx + 1}. {entry}")

    except Pyro4.errors.CommunicationError as e:
        print("[-] Communication error with server:", e)
    except Exception as e:
        print("[-] Error:", e)