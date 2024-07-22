"""Tools for managing the state that persists between contexts.
"""
from doc_qa import ask_docs



default_state={}
def update_state(new_state,state=default_state):
    state.update(new_state)
    return state
def query_state(query,docs,state=default_state):
    return ask_docs(
        query,
        state=update_state(),
        example_response={"channel_name":"general"},
        answer_key="channel_name",
        docs=docs,
        format="json",
    )