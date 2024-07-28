# Example usage
from shared.create_message_embeddings import find_similar_documents


query = "Your query text here"
similar_documents = find_similar_documents(query)
for doc in similar_documents:
    print(doc)