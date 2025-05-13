import xmlrpc.client

addr_to_produce = ('127.0.0.1', 9000)
addr_to_produce_as_str = f'http://{addr_to_produce[0]}:{addr_to_produce[1]}'

def main():
    # create client and connect to InsultFilterServer
    filter_server = xmlrpc.client.ServerProxy(uri=addr_to_produce_as_str, allow_none=True)

    texts_to_filter = [
        "Pero como vas a insultar a tu amigo",
        "El no tiene la culpa de ser bajito",
        "Ay pero cuidado que me pisas al pitufo",
        "Vaya con el tarzan de maceta, como sube de rapido",
        "Ah pero eres un duende media pulga pitufo inspector de baldosas",
        "Cuidado con el chichon de suelo no te caigas, que el muy duende va y se duerme en medio del pasillo",
        "Me gusta el platano"
    ]

    # call filter for example text
    for phrase in texts_to_filter:
        filtered_text = filter_server.filter(phrase)
        print("New text to process:\nNon filtered text:", phrase, "\nFiltered text:", filtered_text)

    # Get all filtered texts on server
    all_filtered_texts = filter_server.getFiltered()
    print("\nFiltered text list:")
    for idx, text in enumerate(all_filtered_texts, start=1):
        print(f"{idx}. {text}")


if __name__ == '__main__':
    main()