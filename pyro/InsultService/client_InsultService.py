import Pyro4
import sys

# insults list hardcoded
insults = [
    "clown", "blockhead", "dimwit", "nincompoop", "simpleton",
    "dullard", "buffoon", "nitwit", "half-wit", "scatterbrain",
    "knucklehead", "dingbat", "doofus", "ninny", "ignoramus",
    "bonehead", "airhead", "puddingbrain", "dunderhead", "numbskull",
    "sap", "scofflaw", "screwball", "twit", "yahoo", "zany",
    "idiot", "moron", "imbecile", "chucklehead", "lunatic",
    "wanker", "dunce", "twerp", "asshat", "donkey"
]

def main():
    try:
        # Locate the Name Server
        ns = Pyro4.locateNS()
        print("[+] Name Server located.")

        # Get the server URI from the Name Server
        uri = ns.lookup("example.InsultServer")
        print(f"[+] Server found: {uri}")

        # Create a proxy to the remote server
        server = Pyro4.Proxy(uri)

        # Show initial list of insults
        print("\n[>] Initial list of insults:")
        try:
            current_insults = server.get_insults()
            print(current_insults)
        except:
            current_insults = []

        # Add some insults if the list is empty
        if not current_insults:
            print("\n[!] The insult list is empty. Adding default insults for testing.")
            for insult in insults:
                server.add_insult(insult)
            print("[+] Default insults added.")
        else:
            print("\n[>] Server already has insults. Ready to go!")

        # Request 5 random insults
        print("\n[?] Receiving 5 random insults:")
        for i in range(5):
            print(f"Insult {i+1}: {server.insult_me()}")

    except Pyro4.errors.CommunicationError as e:
        print("[-] Communication error with server:", e)
    except Exception as e:
        print("[-] Error:", e)


if __name__ == "__main__":
    main()