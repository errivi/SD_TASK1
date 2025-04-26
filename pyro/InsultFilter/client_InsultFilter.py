#!/usr/bin/env python3

import sys
import Pyro4

def main():

    uri = sys.argv[1]

    # Determine if using name server (PYRONAME:) or direct URI
    if uri.startswith("PYRONAME:"):
        proxy = Pyro4.Proxy(uri)
    else:
        # direct URI (e.g., PYRO:example.insultfilter@localhost:8888)
        proxy = Pyro4.Proxy(uri)

    # Example text to filter
    text_to_filter = "Eres muy tonto"

    try:
        # Call the remote filter method
        filtered_text = proxy.filter(text_to_filter)
        print("Original text:", text_to_filter)
        print("Filtered text:", filtered_text)

        # Retrieve all filtered texts from the server
        all_filtered = proxy.getFiltered()
        print("\nFiltered text list:")
        for idx, item in enumerate(all_filtered, start=1):
            print(f"{idx}. {item}")

    except Pyro4.errors.CommunicationError as e:
        print("Error communicating with InsultFilter service:", e)


if __name__ == '__main__':
    main()
