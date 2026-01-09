from typing import Any, Dict
from graph.state import GraphState
from langchain_openai import ChatOpenAI
from langchain_core.chat_history import InMemoryChatMessageHistory
from langchain_core.messages import HumanMessage
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_community.graphs import Neo4jGraph
from graph.nodes.knowledge_graph import get_user_profile_str
import os

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE")
)

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)
store = {}

def get_session_history(session_id: str):
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]


daily_prompt = ChatPromptTemplate.from_messages([
    (
        "system",
        "Sen LC Waikiki için özel olarak geliştirilmiş, arkadaş canlısı ve zeki bir sohbet asistanısın. "
        "Küçük sohbetleri keyifli hale getirmeli, hiçbir soruyu cevapsız bırakmamalısın. "
         "Her zaman pozitif, destekleyici ve kullanıcıyı rahatlatıcı bir ton kullanırsın. "
        "Cevaplarında adıyla hitap edebilirsin. "
        "Tahminde bulunmak gerekiyorsa kibarca bunu yap. Asla 'bilmiyorum' deme, daima yardımcı olmaya çalış. "
        "Asla 'bilmiyorum' deme, en azından tahmin yürüt. Yardımcı olamazsan bile kullanıcıya değer ver ve yanında olduğunu hissettir."
        "Eğer kullanıcı moral olarak düşük görünüyorsa onu cesaretlendirecek şeyler söyleyebilirsin. "
        "Kullanıcıyla sıcak, samimi ve doğal bir tonla konuş. Gerektiğinde adıyla hitap edebilirsin. "

        "Sana gelen sorular her zaman bilgi içermek zorunda değil. Selamlaşma, merak, mizah, günlük sohbet hepsi olabilir. "
        "Şunu unutma: Senin görevin sadece teknik soruları yanıtlamak değil, aynı zamanda kullanıcıyı güvende ve değerli hissettirmek. "

        "Şunları yapabilirsin:\n"
        "- LC Waikiki'deki kampanyalar hakkında bilgi verebilirsin\n"
        "- Kullanıcının beden ve ayakkabı numarasını tahmin edebilirsin\n"
        "- Sohbet edebilir, moral verebilir, küçük konuşmalara katılabilirsin\n"
        "- Kullanıcının alışveriş davranışlarına göre öneride bulunabilirsin\n"
        "- Gerekirse kullanıcıyı yönlendirerek başka sistemlere bağlanmasına yardımcı olabilirsin\n"

        "Unutma: Asistan olarak senin rolün sadece bir cevap motoru değil, bir arkadaş gibi yanıt vermek."

    ),
    MessagesPlaceholder(variable_name="messages")
])


# LLM Chain
with_message_history = RunnableWithMessageHistory(
    daily_prompt | llm,
    get_session_history,
    input_messages_key="messages",
    history_messages_key="messages",
)

def llm_response(state: GraphState) -> Dict[str, Any]:
    print("---LLM RESPONSE---")
    question = state["question"]
    uid = state.get("uid")
    session_id = f"user-{uid or 'anonymous'}"
    profile_info = ""

    if uid:
        profile_info = get_user_profile_str(uid, graph)

    if not profile_info:
        history = get_session_history(session_id)
        for msg in reversed(history.messages):
            if msg.type == "system" and "Kullanıcı :" in msg.content:

                start = msg.content.find("Kullanıcı :")
                profile_info = msg.content[start:].replace("Kullanıcı :", "").strip()
                break


    history = get_session_history(session_id)
    history.add_user_message(question)
    messages = history.messages

    config = {"configurable": {"session_id": session_id}}


    response = with_message_history.invoke(
        {"messages": messages, "profile_info": profile_info},
        config=config
    )
    history.add_ai_message(response.content)
    return {
        "question": question,
        "generation": response.content,
        "source": "llm"
    }