from langchain_core.messages import HumanMessage, AIMessage
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_openai import ChatOpenAI


model = ChatOpenAI(model="gpt-3.5-turbo")
store = {}

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


prompt = ChatPromptTemplate.from_messages(
    [
        (
            "system",  "You are a friendly assistant. Remember what the user says in this session and reply accordingly.",
        ),
        MessagesPlaceholder(variable_name="messages"),
    ]
)

chain = prompt | model

config = {"configurable": {"session_id": "firstChat"}}

with_message_history = RunnableWithMessageHistory(
    chain, get_session_history
)
