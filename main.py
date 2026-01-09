from dotenv import load_dotenv
load_dotenv()

import os
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from graph.chains.discount_chain import discount
from graph.graph import app
from langchain_community.graphs import Neo4jGraph
from neo4j import GraphDatabase



def wrap_by_word_count(text, words_per_line=15):
    words = text.split()
    lines = [' '.join(words[i:i + words_per_line]) for i in range(0, len(words), words_per_line)]
    return '\n'.join(lines)

# Neo4j setup
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE")
)

# LLM Setup
store = {}
def get_session_history(session_id: str) -> BaseChatMessageHistory:
    if session_id not in store:
        store[session_id] = InMemoryChatMessageHistory()
    return store[session_id]

model = ChatOpenAI(model="gpt-3.5-turbo", temperature=0)
prompt = ChatPromptTemplate.from_messages([
    ("system", "You are a helpful assistant. Answer all questions to the best of your ability."),
    MessagesPlaceholder(variable_name="messages"),
])
chain = prompt | model
with_message_history = RunnableWithMessageHistory(
    chain, get_session_history,
    input_messages_key="messages",
    history_messages_key="messages",
)

session_uid = None
asked_uid = False
extraction_list = []
discount_shown_true = False

store["menu_stage"] = "awaiting_first_message"

def get_segment_questions():
    return [
        ("age", "Yaşınızı öğrenebilir miyim?\nSize daha uygun öneriler sunmam için bu bilgi önemli"),
        ("customer_type", "Aşağıdaki gruplardan hangisi sizi en iyi tanımlar dersiniz? \nYeni bir müşteri misiniz, düzenli olarak alışveriş yapan biri misiniz yoksa premium müşterilerden misiniz? (New/Regular/Premium)"),
        ("income", "Gelir seviyenizi nasıl tanımlarsınız? \nBöylece bütçenize uygun seçenekler sunabilirim. (Low/Medium/High)"),
        ("shopping_count", "Bir ayda ortalama kaç kez alışveriş yaparsınız?\nYaklaşık bir sayı yeterli olacaktır."),
        ("total_spend", "Genel olarak bir ayda yaptığınız toplam harcama ne kadar olur?\nTahmini bir tutar belirtmeniz yeterlidir. ₺")
    ]

def chat():
    global session_uid, asked_uid, extraction_list, discount_shown_true
    print("LC Waikiki Chatbot’a Hoş Geldiniz!")
    print("Herhangi bir şey sorabilirsiniz. Çıkmak için 'exit' yazın.")

    while True:
        question = input("\n👤: ").strip()

        if question.lower() == "exit":
            if session_uid and not discount_shown_true:
                discount_chain = discount()
                result = discount_chain.invoke({"uid": session_uid})
                if result and isinstance(result, dict):
                    print("\nSize özel indirimler:")
                    print(result.get("generation", "İndirim bilgisi alınamadı."))
                discount_shown_true = True
                confirm = input("\nHala çıkmak istiyorsanız tekrar 'exit' yazın, devam etmek için herhangi bir tuşa basın: ")
                if confirm.lower() != "exit":
                    continue
            print("Görüşmek üzere!")
            break

        if question.lower() in ["reset", "yeni kullanıcı", "baştan başla"]:
            if session_uid:
                if not discount_shown_true:
                    discount_chain = discount()
                    result = discount_chain.invoke({"uid": session_uid})
                    if result and isinstance(result, dict):
                        print("\nSize özel indirimler:")
                        print(result.get("generation", "İndirim bilgisi alınamadı."))
                    discount_shown_true = True

            session_uid = None
            asked_uid = False
            extraction_list = []
            store["menu_stage"] = "awaiting_first_message"  # <-- eksikti

            print(" Yeni kullanıcı olarak başlatıldı.")
            continue

        if not session_uid and not asked_uid:
            if store.get("menu_stage") == "awaiting_first_message":
                print("\nHoş geldiniz! Lütfen aşağıdaki seçeneklerden birini seçin:")
                print("1) Kullanıcı ID ile giriş yap")
                print("2) ID'niz yoksa yeni bir kullanıcı oluştur")
                print("3) IDsiz devam et (sadece genel sorular için)")
                store["menu_stage"] = "awaiting_choice"
                continue

            if store.get("menu_stage") == "awaiting_choice":
                if question == "1":
                    session_uid = input("Lütfen kullanıcı ID’nizi girin: ").strip()

                    if session_uid.lower() == "admin":
                            password = input("🔐 Lütfen şifrenizi girin: ").strip()
                            if password != "12345":
                                print("Hatalı şifre. Admin girişi reddedildi.")
                                session_uid = None
                                asked_uid = False
                                continue

                            print("\nSayın Kampanya Yöneticisi, hoş geldiniz!")

                            try:
                                import admin
                            except Exception as e:
                                print(f"Kampanya yöneticisi modülü çalıştırılamadı: {e}")

                            print(
                                "\n Kampanya Yöneticisi görünümü tamamlandı. Şimdi normal kullanıcı gibi devam edebilirsiniz.")
                            input(" Devam etmek için Enter'a basın...")

                            session_uid = None
                            asked_uid = False
                            continue

                    driver = GraphDatabase.driver(
                        os.getenv("NEO4J_URI"),
                        auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
                    )
                    with driver.session(database=os.getenv("NEO4J_DATABASE")) as session:
                        result = session.run("""
                            MATCH (u:UID {value: $uid})
                            OPTIONAL MATCH (u)-[:HAS_NAME]->(n:Name)
                            RETURN u, n.value AS name
                        """, uid=session_uid)
                        record = result.single()
                    driver.close()

                    if not record:
                        session_uid = None
                        print(" Bu kullanıcı ID’si bulunamadı. Lütfen geçerli bir ID giriniz.")
                        continue

                    name = record.get("name")
                    print(f" Hoş geldiniz {name or ''}! Size nasıl yardımcı olabilirim?")
                    store["menu_stage"] = "chat"
                    continue

                elif question == "2":
                    store["segment_progress"] = {
                        "step_index": 0,
                        "answers": {}
                    }
                    store["menu_stage"] = "segment_creation"
                    print(" Yeni kullanıcı oluşturuluyor... Lütfen aşağıdaki soruları cevaplayın:")

                    steps = get_segment_questions()
                    while store["segment_progress"]["step_index"] < len(steps):
                        idx = store["segment_progress"]["step_index"]
                        step_key, question_text = steps[idx]
                        answer = input(f"{question_text} ").strip()
                        store["segment_progress"]["answers"][step_key] = answer
                        store["segment_progress"]["step_index"] += 1

                    from graph.nodes.knowledge_graph import create_user_from_segments
                    result = create_user_from_segments(store["segment_progress"]["answers"])
                    del store["segment_progress"]
                    store["menu_stage"] = "chat"

                    if result.get("uid"):
                        session_uid = result["uid"]
                        print(f" Kullanıcı ID’niz oluşturuldu: {session_uid}\nSize nasıl yardımcı olabilirim?")
                    else:
                        print(result.get("generation", " Segment ile kullanıcı oluşturulamadı."))
                    continue

                elif question == "3":
                    session_uid = None
                    store["menu_stage"] = "chat"
                    print("ID'siz devam ediyorsunuz. Bazı işlemler için ID gerekli olacaktır.")
                    continue

                else:
                    print("Lütfen geçerli bir seçim yapınız (1, 2 veya 3).")
                    continue

            if store.get("menu_stage") == "segment_creation":
                steps = get_segment_questions()
                answers = {}

                print(" Yeni kullanıcı oluşturuluyor... Lütfen aşağıdaki soruları cevaplayın:")
                for step_key, step_prompt in steps:
                    user_input = input(f"{step_prompt} ").strip()
                    answers[step_key] = user_input

                from graph.nodes.knowledge_graph import create_user_from_segments
                result = create_user_from_segments(answers)
                store["menu_stage"] = "chat"

                if result.get("uid"):
                    session_uid = result["uid"]
                    print(f" Kullanıcı ID’niz oluşturuldu: {session_uid}\nSize nasıl yardımcı olabilirim?")
                else:
                    print(result.get("generation", " Segment ile kullanıcı oluşturulamadı."))
                continue

        state = {"question": question}
        # ID'siz devam ediliyorsa ve UID gerektiren bir işlem sorulursa menüye yönlendir
        uid_gerektiren_kelimeler = ["indirim", "kampanya", "geçmiş", "alışveriş", "benim", "kişisel", "beden", "numara"]
        if not session_uid and any(word in question.lower() for word in uid_gerektiren_kelimeler):
            print("⚠ Bu işlem için kullanıcı ID’niz gereklidir. Lütfen kimlik doğrulaması yapınız.")
            print("\nLütfen aşağıdaki seçeneklerden birini seçin:")
            print("1) Kullanıcı ID ile giriş yap")
            print("2) ID'niz yoksa yeni bir kullanıcı oluştur")
            print("3) IDsiz devam et (sadece genel sorular için)")
            store["menu_stage"] = "awaiting_choice"
            continue

        if session_uid:
            state["uid"] = session_uid

        result = app.invoke(state)

        if result.get("uid") and session_uid != result["uid"]:
            session_uid = result["uid"]
            state["uid"] = session_uid
            result = app.invoke(state)

        if result.get("seg_step"):
            cevap = input(result["generation"] + "\n👤 Seçiminiz: ")
            state[result["seg_step"]] = cevap
            continue



        elif result.get("generation"):
            formatted_text = wrap_by_word_count(result["generation"], words_per_line=15)
            print("🤖", formatted_text)

            if result.get("discount_shown") == True:
                discount_shown_true = True
            continue

        elif result.get("source") == "llm":
            response = with_message_history.invoke(
                [HumanMessage(content=question)],
                config={"configurable": {"session_id": "firstChat"}}
            )
            formatted_response = wrap_by_word_count(response.content, words_per_line=15)
            print("🤖", formatted_response)
            continue

        else:
            print("Beklenmeyen sonuç:", result)
            continue

if __name__ == "__main__":
    chat()