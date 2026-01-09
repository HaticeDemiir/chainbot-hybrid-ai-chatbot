
import pandas as pd
from dotenv import load_dotenv
load_dotenv()

import os
from neo4j import GraphDatabase
from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_core.chat_history import BaseChatMessageHistory, InMemoryChatMessageHistory
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder

from graph.graph import app
from langchain_community.graphs import Neo4jGraph

#Graph Zeynep
NEO4J_URI="neo4j+ssc://ae504ea9.databases.neo4j.io"
NEO4J_USERNAME="neo4j"
NEO4J_PASSWORD="7PD6uEL8HLpzUFV5UamAkeOvCN6BDBsuu8eFYqMBP30"
AURA_INSTANCEID="ae504ea9"
AURA_INSTANCENAME="Free instance"

# Neo4j bağlantısı
graph2 = Neo4jGraph(
    url=NEO4J_URI,
    username=NEO4J_USERNAME,
    password=NEO4J_PASSWORD,
    database="neo4j"
)

def get_segment_discount_info():
    try:
        segment_input = input("📌 Hangi segmentin indirim oranını öğrenmek istersiniz? (Çıkmak için 'çıkış' yazın) ").strip()
        if segment_input.lower() == 'çıkış':
            return None

        segment_input = int(segment_input)
    except ValueError:
        print("❗ Lütfen geçerli bir sayı girin.")
        return None

    query = """
    MATCH (s:FinalSegment {id: $segment}) 
    MATCH (s)-[r:HAS_DISCOUNT]->(d:Category)
    RETURN r.discount AS discount_ratio, r.predicted AS predicted_ratio, d AS category
    """

    try:
        result = graph2.query(query, params={"segment": segment_input})
        if result and len(result) > 0:
            segment_info_list = []

            for row in result:
                segment_info_list.append({
                    "segment": segment_input,
                    "discount_ratio": row["discount_ratio"],
                    "predicted_ratio": row["predicted_ratio"],
                    "category": row["category"]
                })

            return segment_info_list
        else:
            print("❗ Belirtilen segmente ait bilgi bulunamadı.")
            return None
    except Exception as e:
        print(f"🚨 Hata oluştu: {e}")
        return None


def get_category_max_indexes(csv_path="Datas\\sorted_category_predicted_ratio.csv"):
    df = pd.read_csv(csv_path, sep=";")
    max_indexes = df.groupby('Category')['Index'].max().to_dict()
    return max_indexes

def get_category_indexes_from_csv(segment_infos, max_indexes, csv_path="Datas\\sorted_category_predicted_ratio.csv"):
    df = pd.read_csv(csv_path, sep=";")
    category_info = []

    for info in segment_infos:
        category_data = info["category"]
        category_name = category_data.get("name") if isinstance(category_data, dict) else category_data
        predicted_ratio = info["predicted_ratio"]

        match = df[(df["Category"] == category_name) & (abs(df["Predicted_Ratio"] - predicted_ratio) < 0.0001)]

        if not match.empty:
            index = match["Index"].values[0]
            max_index = max_indexes.get(category_name, 0)

            category_info.append((category_name, index, max_index))
        else:
            print(f"⚠ {category_name} için eşleşme bulunamadı.")

    return category_info

def build_summary_messages(segment_infos, category_indexes):
    messages = []

    for info, (category_name, segment_index, max_index) in zip(segment_infos, category_indexes):
        segment_id = info["segment"]
        predicted_ratio = round(info["predicted_ratio"] * 100, 2)
        discount_ratio = round(info["discount_ratio"] * 100, 2)

        message = (
            f"📌 {segment_id} numaralı segmentin, bir sonraki alışverişinde **{category_name}** kategorisinde alışveriş yapma tahmini **%{predicted_ratio}**'dir. "
            f"Bu da o kategorideki segmentler arasında **{segment_index}. sırada** yer aldığını gösterir (Toplam: {max_index}). "
            f"Bu nedenle önerilen indirim miktarı **%{discount_ratio}**'dir."
        )

        messages.append(message)

    return messages



def build_llm_summaries(segment_infos, category_indexes):
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)

    summaries = []

    for info, (category_name, segment_index, max_index) in zip(segment_infos, category_indexes):
        segment_id = info["segment"]
        predicted_ratio = round(info["predicted_ratio"] * 100, 2)
        discount_ratio = round(info["discount_ratio"] * 100, 2)

        # LLM'e verilecek prompt
        user_prompt = (
            f"{segment_id} numaralı segmentin {category_name} kategorisinde alışveriş yapma olasılığı %{predicted_ratio} ve bu kategoriye özel önerilen indirim %{discount_ratio}. "
            f"Segment, bu kategori için {segment_index}. sırada yer alıyor (Toplam: {max_index} segment). "
            f"Bunu kullanarak kullanıcıya yönelik kısa ve açıklayıcı bir özet yaz."
        )

        # LLM'den cevap al
        response = llm.invoke([HumanMessage(content=user_prompt)])
        summaries.append(response.content)

    return summaries

# Ana döngü başlatılıyor
while True:
    segment_infos = get_segment_discount_info()

    if segment_infos is None:
        print("🛑 Çıkılıyor...")
        break

    max_indexes = get_category_max_indexes()
    category_indexes = get_category_indexes_from_csv(segment_infos, max_indexes)

    summary_messages = build_llm_summaries(segment_infos, category_indexes)

    print("\n📌 Özetler:")
    for msg in summary_messages:
        print(msg)
