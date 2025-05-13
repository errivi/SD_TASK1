#!/usr/bin/env python3

import sys
import Pyro4

def main():

    uri = sys.argv[1]
    proxy = Pyro4.Proxy(uri)

    # Example text to filter
    text_to_filter = "Eres muy tonto"

    try:
        # Call the remote filter method
        filtered_text = proxy.filter(text_to_filter)
        print("Non filtered text:", text_to_filter, "\nFiltered text:", filtered_text)

        # Get all filtered texts on serverr
        all_filtered_texts = proxy.getFiltered()
        print("\nFiltered text list:")
        for idx, item in enumerate(all_filtered_texts, start=1):
            print(f"{idx}. {item}")

    except Pyro4.errors.CommunicationError as e:
        print("Error communicating with InsultFilter service:", e)


if __name__ == '__main__':
    main()
