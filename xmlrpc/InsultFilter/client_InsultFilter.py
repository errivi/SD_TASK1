import xmlrpc.client


def main():
    # create client and connect to InsultFilterServer
    filter_server = xmlrpc.client.ServerProxy("http://localhost:8000", allow_none=True)

    text_to_filter = "Eres muy tonto"

    # call filter for example text
    filtered_text = filter_server.filter(text_to_filter)
    print("Non filtered text:", text_to_filter, "\nFiltered text:", filtered_text)

    # Get all filtered texts on server
    all_filtered_texts = filter_server.getFiltered()
    print("\nFiltered text list:")
    for idx, text in enumerate(all_filtered_texts, start=1):
        print(f"{idx}. {text}")


if __name__ == '__main__':
    main()
