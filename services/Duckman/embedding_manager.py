from time import sleep
from discord_client import client
from shared.create_message_embeddings import update_embeddings


while True:
    sleep(10)
    update_embeddings(100)