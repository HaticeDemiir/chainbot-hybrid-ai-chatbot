from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import JsonOutputParser


llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)
parser = JsonOutputParser()


prompt = ChatPromptTemplate.from_messages([
    ("system",
     """Sen bir LC Waikiki alışveriş asistanısın. Kullanıcının mesajından aşağıdaki bilgileri, 
     yalnızca kullanıcı kendisiyle ilgili ve giyim/stil konusuna dair doğrudan veya dolaylı şekilde ifade edilmişse çıkarmaya çalış:
    - name (kullanıcnın adı,ismi)
    - size (örnek: S, M, L, XL)
    - shoe_size (kullanıcının ayakkabı numarası,örnek: 37, 38)
    - age (kullanıcının yaşı,örnek: 22)
    - gender (kullanıcının cinsiyeti,örnek: kadın, erkek)  (Eğer kullanıcı adını belirtiyorsa ve bu ad Türkiye'de yaygın bir kadın veya erkek adıysa, gender bilgisini adından tahmin etmeye çalış.)

    - interests (sadece giyim/stil ile ilgili olanlar: spor giyim, ofis şıklığı, rahat kıyafetler gibi)

    Eğer bu bilgiler mesajda yoksa null döndür. LC Waikiki dışı konuları (müzik, yemek vs.) dikkate alma.
    
    Çıktıyı sadece şu formatta ver:
    
    json
    {{
      "name":"",
      "age": 0,
      "size": "",
      "shoe_size": "",
      "gender": "",
      "interests": ""
    }}
    """),

    ("human", "{question}")
])

extract_chain = prompt | llm | parser