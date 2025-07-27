"""
Handles the agent's actions and interactions with the environment.
"""
import ollama
import uuid
import json

class Agent:
    def __init__(self, name, environment, collection, model_name, provider="http://ollama-gpu:11434"):
        self.name = name
        self.environment = environment
        self.state = None
        self.collection = collection # Chroma collection
        self.model_name = model_name
        self.provider = provider
        self.client=ollama.AsyncClient(host=provider)

    @property
    def context(self):
        """
        Placeholder for the context property.
        This should return the current context of the agent.
        """
        return []
    def ask_docs(self):

        """
        Placeholder for the ask_docs method.
        This method should be implemented to interact with the document QA system.
        """
        pass

    async def ask_context(self):
        """
        Placeholder for the ask_context method.
        This method should be implemented to interact with the context system.
        """
        pass
    async def async_complete(self, context, format=None, streaming=False, streaming_callback=None):
        try:
            model=self.model_name
            client=self.client
            response=await client.chat(
                model=model,
                messages=context,
                format="json" if format=="json" else None,
                stream=streaming,
            )
            if streaming and streaming_callback:
                stream_id=str(uuid.uuid4())
                result=""
                async for chunk in response:
                    text=chunk['message']['content']
                    if text:
                        result+=text
                        done=await streaming_callback(text,stream_id,finished=False)
                        if done:
                            break

                    else:
                        # the last chunk will be the full string.
                        return await streaming_callback(result,stream_id,finished=True)
            else:
                string=response['message']['content']
                return json.loads(string) if format=="json" else string

        except Exception as e:
            print("Error in async_complete")
            print(e)
            raise e
