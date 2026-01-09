from typing import Literal
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI
import os

api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OPENAI_API_KEY bulunamadı! Lütfen .env dosyasınızı kontrol edin.")

class RouteQuery(BaseModel):
    datasource: Literal["vectorstore", "websearch", "llm", "discount","size"] = Field(...)

llm = ChatOpenAI(api_key=api_key, temperature=0.1, model="gpt-4")
structured_llm_router = llm.with_structured_output(RouteQuery)
structured_llm_extractor = llm.with_structured_output(RouteQuery)

system = """
Sen, LC Waikiki için geliştirilmiş bir sınıflandırma modelisin. 
Amaç: kullanıcı sorusunu aşağıdaki kaynaklardan hangisinin yanıtlaması gerektiğine karar vermek.

--- 
Seçenekler:
- 'vectorstore': LC Waikiki'ye özgü belgeler için (sipariş, iade, değişim, ürün,  ödeme, site, uygulama, teslimat, kariyer vb.)
- 'websearch': Güncel, dış kaynak veya internette taranması gereken bilgiler (hava durumu, haber, genel bilgi)
- 'llm': Günlük sohbetler, selamlaşma, küçük konular, kişisel sorular
- 'discount': Kullanıcı indirim, kampanya, fırsat gibi şeyler soruyorsa bu seçilmeli
- 'size': Kullanıcı beden, ayakkabı numarası gibi şeyler soruyorsa bu seçilmeli
Kullanıcı açıkça LC Waikiki konularına gönderme yapıyorsa, 'vectorstore' seç.
LC Waikiki ile ilgili bile olsa, soruya belgeler cevap veremeyecekse ve yorum gerektiriyorsa, 'llm' seç.
Kullanıcı indirim, kampanya gibi şeyler soruyorsa, 'discount' seç, kullanıcı beden, ayakkabı numarası gibi şeyler soruyorsa bu seç.
Belirsizse, önceliği vectorstore'a ver.
"""

route_prompt = ChatPromptTemplate.from_messages([
    ("system", system),
    ("human", "{question}"),
])

question_router = route_prompt | structured_llm_router

