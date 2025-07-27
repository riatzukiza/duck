# Duckman Discord Assistant

Duckman is an LLM powered discord bot assistant. It has access to your servers entire discord chat history. It executes searches in the background based on the message history, and stores the results in a chromadb vector database. It has access to a filesystem, and also indexes the contents of those files and their histories.

When a message is sent to Duckman, it retrieves relavent stored search results, files, and messages to add to its context to answer your questions.

Duckman gets to know you and your server, and responds accordingly.

To get it started, just run docker compose:

```bash
docker compose up
```

And it will start indexing the files in the current directory. By default that is a folder in this git repository, so you can ask it questions about how it arrived at its answers and develop a copy of it specific to your own needs by just talking to it.
