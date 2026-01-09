from langchain_core.output_parsers import StrOutputParser
from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

llm = ChatOpenAI(temperature=0)

prompt = ChatPromptTemplate.from_messages([
    ("system", """Sen bir LC Waikiki alışveriş asistanısın. Kullanıcıdan gelen sorulara belgelerden yola çıkarak tek cümle ile özet kısa cevap ver,kullanıcnın sorusunu karşılasın.

    Ek olarak eğer kullanıcı profilinde isim geldiyse kullanıcı aksini iddia etmediği sürece ismiyle hitap et. 
    
    Knowledge graphtan dönen bilgileri eksiksiz ve doğru şekilde günlük konuşma diline uygun doğal bir şekilde kullanıcıya ilet.


    Belgelerden gelen bilgi:
    {context}
    Kullanıcı Profili:
    {user_profile}
    Knowledge Graphtan gelen bilgi:
    {knowledge_graph_discount_result}
    {knowledge_graph_size_result}

"""),
    ("human", "{question}")
])

generation_chain = prompt | llm | StrOutputParser()