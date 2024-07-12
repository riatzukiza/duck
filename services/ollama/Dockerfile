# Dockerfile for Ollama service

FROM ollama/ollama:latest

# Pull the new model
RUN ollama pull nomic-embed-text
RUN ollama pull llama3

# Expose the port for the API
EXPOSE 11434

CMD ["ollama", "serve"]
