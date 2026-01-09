import pandas as pd
from dotenv import load_dotenv
load_dotenv()

from langchain_openai import ChatOpenAI
from langchain_core.messages import HumanMessage
from langchain_community.graphs import Neo4jGraph
import os
from admin_update import update

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE")
)

from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    os.getenv("NEO4J_URI"),
    auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
)


def draw_cluster_only_graph(segment_id: int, driver):
    net = Network(height='100vh', width='100vw', directed=True, bgcolor="#ffffff", font_color="black")
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=250, spring_strength=0.05, damping=0.09)

    cypher_query = f"""
    MATCH (s:FinalSegment {{id: {segment_id}}})
    OPTIONAL MATCH (s)-[:CONTAINS]->(sc:SegmentCluster)
    RETURN s, collect(DISTINCT sc) AS clusters
    """

    with driver.session() as session:
        result = session.run(cypher_query)
        record = result.single()
        if not record:
            print("Segment bulunamadı.")
            return

        s = record["s"]
        clusters = record["clusters"]

        sid = f's_{s["id"]}'
        net.add_node(sid, label=f'FinalSegment\nID: {s["id"]}', color='orange')

        for sc in clusters:
            if sc:
                sc_label = f'{sc["name"]}'
                if "min" in sc and "max" in sc:
                    sc_label += f'\n({sc["min"]}–{sc["max"]})'
                scid = f'sc_{sc["id"]}'
                net.add_node(scid, label=f'SegmentCluster\n{sc_label}', color='lightblue')
                net.add_edge(sid, scid, label='İÇERİR', color='blue')

    output_file = f"Virtualized Segment Infos/segment_{segment_id}_clusters_only.html"
    net.write_html(output_file)
    print(f"Cluster grafiği oluşturuldu: {output_file}")

def draw_category_only_graph(segment_id: int, driver):
    net = Network(height='100vh', width='100vw', directed=True, bgcolor="#ffffff", font_color="black")
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=250, spring_strength=0.05, damping=0.09)

    cypher_query = f"""
    MATCH (s:FinalSegment {{id: {segment_id}}})
    OPTIONAL MATCH (s)-[r:HAS_DISCOUNT]->(c:Category)
    RETURN s, collect(DISTINCT {{cat: c, rel: r}}) AS categories
    """

    def format_rel_label(rel):
        if rel is None:
            return ""
        if "ratio" in rel and "predicted" in rel:
            ratio = round(rel["ratio"] * 100, 2)
            predicted = round(rel["predicted"] * 100, 2)
            return wrap_by_word_count(f"Kategoride bir sonraki alışveriş ihtimali %{ratio} olduğu için %{predicted} indirim önerilmelidir.", words_per_line=3)
        return ""

    with driver.session() as session:
        result = session.run(cypher_query)
        record = result.single()
        if not record:
            print("Segment bulunamadı.")
            return

        s = record["s"]
        categories = record["categories"]

        sid = f's_{s["id"]}'
        net.add_node(sid, label=f'FinalSegment\nID: {s["id"]}', color='orange')


        max_ratio = 0
        for item in categories:
            rel = item.get("rel")
            if rel and "ratio" in rel:
                max_ratio = max(max_ratio, rel["ratio"])

        for item in categories:
            c = item.get("cat")
            rel = item.get("rel")
            if c:
                cid = f'c_{c["name"]}'
                label = wrap_by_word_count(format_rel_label(rel), words_per_line=3)


                node_size = 20
                if rel and "ratio" in rel and rel["ratio"] == max_ratio:
                    node_size = 40

                net.add_node(cid, label=f'Category\n{c["name"]}', color='lightgreen', size=node_size)
                net.add_edge(sid, cid, label=label, color='green')

    output_file = f"Virtualized Segment Infos/segment_{segment_id}_categories_only.html"
    net.write_html(output_file)
    print(f"Category grafiği oluşturuldu: {output_file}")


def wrap_by_word_count(text, words_per_line=15):
    words = text.split()
    lines = [' '.join(words[i:i + words_per_line]) for i in range(0, len(words), words_per_line)]
    return '\n'.join(lines)

from pyvis.network import Network
import os

def draw_segment_graph_pyvis(segment_id: int, driver):
    net = Network(height='100vh', width='100vw', directed=True, bgcolor="#ffffff", font_color="black")
    net.barnes_hut(gravity=-8000, central_gravity=0.3, spring_length=250, spring_strength=0.05, damping=0.09)


    cypher_query = f"""
    MATCH (s:FinalSegment {{id: {segment_id}}})
    OPTIONAL MATCH (s)-[r1:HAS_DISCOUNT]->(c:Category)
    OPTIONAL MATCH (s)-[r2:CONTAINS]->(sc:SegmentCluster)
    RETURN s, collect(DISTINCT {{cat: c, rel: r1}}) AS categories, collect(DISTINCT sc) AS clusters
    """

    def format_rel_label(rel):
        if rel is None:
            return ""
        if "ratio" in rel and "predicted" in rel:
            ratio = round(rel["ratio"] * 100, 2)
            predicted = round(rel["predicted"] * 100, 2)
            return f"Kategoride bir sonraki alışveriş ihtimali %{ratio}\nolduğu için %{predicted} indirim önerilmelidir."
        return ""

    with driver.session() as session:
        result = session.run(cypher_query)
        records = list(result)
        print(f"Record sayısı: {len(records)}")
        if len(records) == 0:
            print("Hiç kayıt yok.")
            return
        else:
            print("Kayıt var, işleme devam ediliyor.")

        for record in records:
            s = record["s"]
            categories = record["categories"]
            clusters = record["clusters"]

            sid = f's_{s["id"]}'
            net.add_node(sid, label=f'FinalSegment\nID: {s["id"]}', color='orange')


            for item in categories:
                c = item.get("cat")
                rel = item.get("rel")
                if c:
                    cid = f'c_{c["name"]}'
                    net.add_node(cid, label=f'Category\n{c["name"]}', color='lightgreen')
                    label = format_rel_label(rel)
                    net.add_edge(sid, cid, label=label, color='green')


            for sc in clusters:
                if sc:
                    sc_label = f'{sc["name"]}'
                    if "min" in sc and "max" in sc:
                        sc_label += f'\n({sc["min"]}–{sc["max"]})'
                    scid = f'sc_{sc["id"]}'
                    net.add_node(scid, label=f'SegmentCluster\n{sc_label}', color='lightblue')
                    net.add_edge(sid, scid, label='CONTAINS', color='blue')

    output_dir = "Virtualized Segment Infos"
    os.makedirs(output_dir, exist_ok=True)

    output_file = os.path.join(output_dir, f"segment_{segment_id}_graph.html")
    net.write_html(output_file)
    print(f"Segment {segment_id} için grafik dosyası oluşturuldu: {output_file}")

def get_segment_questions():
    return [
        ("age", "Segmenti görebilmek için öğrenmek istediğiniz yaş nedir? "),
        ("customer_type", "Hangi müşteri tipini öğrenmek istiyorsunuz? (New/Regular/Premium)"),
        ("income", "Öğrenmek istediğiniz gelir seviyesi seçeneklerden hangisidir? (Low/Medium/High)"),
        ("shopping_count", "Öğrenmek istediğiniz alışveriş sayısı kaçtır?"),
        ("total_spend", "Öğrenmek istediğiniz ortalama toplam harcama tutarı nedir? ₺")
    ]


def get_final_segment_id(answers: dict, graph: Neo4jGraph) -> str | None:
    """
    answers: dict with keys:
        - "age": int
        - "customer_type": str (New, Regular, Premium)
        - "income": str (Low, Medium, High)
        - "shopping_count": int
        - "total_spend": float

    Returns:
        segment_id string veya None
    """
    try:

        age = int(answers.get("age", -1))
        customer_type = str(answers.get("customer_type", "")).strip()
        income = str(answers.get("income", "")).strip()
        shopping_count = int(answers.get("shopping_count", -1))
        total_spend = float(answers.get("total_spend", -1))


        customer_type = customer_type.lower().capitalize()
        income = income.lower().capitalize()

        if age < 0 or shopping_count < 0 or total_spend < 0 or not customer_type or not income:
            print("Girilen değerler eksik veya geçersiz.")
            return None

        cluster_ids = []
        queries = [
            ("MATCH (sc:SegmentCluster) WHERE sc.name STARTS WITH 'AgeCluster' AND sc.min <= $v AND $v <= sc.max RETURN sc.id AS cid", {"v": age}),
            ("MATCH (sc:SegmentCluster)-[:HAS_VALUE]->(val:Value) WHERE sc.name STARTS WITH 'CustomerSegment' AND toLower(val.name) = toLower($v) RETURN sc.id AS cid", {"v": customer_type}),
            ("MATCH (sc:SegmentCluster)-[:HAS_VALUE]->(val:Value) WHERE sc.name STARTS WITH 'IncomeCluster' AND toLower(val.name) = toLower($v) RETURN sc.id AS cid", {"v": income}),
            ("MATCH (sc:SegmentCluster) WHERE sc.name STARTS WITH 'ShoppingCountCluster' AND sc.min <= $v AND $v <= sc.max RETURN sc.id AS cid", {"v": shopping_count}),
            ("MATCH (sc:SegmentCluster) WHERE sc.name STARTS WITH 'TotalPurchaseCluster' AND sc.min <= $v AND $v <= sc.max RETURN sc.id AS cid", {"v": total_spend}),
        ]

        for query, param in queries:
            result = graph.query(query, params=param)
            if result and "cid" in result[0]:
                cluster_ids.append(result[0]["cid"])
            else:
                print(f"Uygun cluster bulunamadı: {param}")
                return None


        seg_match = graph.query("""
            UNWIND $ids AS cid
            MATCH (sc:SegmentCluster {id: cid})
            WITH collect(sc) AS cs
            MATCH (fs:FinalSegment)
            WHERE ALL(c IN cs WHERE (fs)-[:CONTAINS]->(c))
            RETURN fs.id AS segment_id
            LIMIT 1
        """, {"ids": cluster_ids})

        if not seg_match:
            print("Segment bulunamadı.")
            return None

        return seg_match[0]["segment_id"]

    except Exception as e:
        print(f"Segment bulunurken hata oluştu: {e}")
        return None



def get_segment_discount_info():
    try:
        segment_input = input("Hangi segmentin indirim oranını öğrenmek istersiniz? (Çıkmak için 'çıkış' yazın) ").strip()


        if segment_input.lower() == 'çıkış':
            return None

        segment_input = int(segment_input)
    except ValueError:
        print(" Lütfen geçerli bir sayı girin.")
        return None

    query = """
    MATCH (s:FinalSegment {id: $segment}) 
    MATCH (s)-[r:HAS_DISCOUNT]->(d:Category)
    RETURN r.ratio AS discount_ratio, r.predicted AS predicted_ratio, d AS category
    """

    try:
        result = graph.query(query, params={"segment": segment_input})
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
            print(" Belirtilen segmente ait bilgi bulunamadı.")
            return None
    except Exception as e:
        print(f" Hata oluştu: {e}")
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
            print(f" {category_name} için eşleşme bulunamadı.")

    return category_info

def build_summary_messages(segment_infos, category_indexes):
    messages = []

    for info, (category_name, segment_index, max_index) in zip(segment_infos, category_indexes):
        segment_id = info["segment"]
        predicted_ratio = round(info["predicted_ratio"] * 100, 2)
        discount_ratio = round(info["discount_ratio"] * 100, 2)

        message = (
            f" {segment_id} numaralı segmentin, bir sonraki alışverişinde {category_name} kategorisinde alışveriş yapma tahmini %{predicted_ratio}'dir. "
            f"Bu da o kategorideki segmentler arasında {segment_index}. sırada yer aldığını gösterir (Toplam: {max_index}). "
            f"Bu nedenle önerilen indirim miktarı %{discount_ratio}'dir."
        )

        messages.append(message)

    return messages



def build_llm_summaries(segment_infos, category_indexes):
    llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.7)

    summaries = []

    for info, (category_name, segment_index, max_index) in zip(segment_infos, category_indexes):
        segment_id = info["segment"]
        predicted_ratio = round(info["predicted_ratio"] * 100, 2)
        discount_ratio = round(info["discount_ratio"] * 100, 2)


        user_prompt = (
            f"{segment_id} numaralı segmentin {category_name} kategorisinde alışveriş yapma olasılığı %{predicted_ratio} ve bu kategoriye özel önerilen indirim %{discount_ratio}. "
            f"Segment, bu kategori için {segment_index}. sırada yer alıyor (Toplam: {max_index} segment). "
            f"Bunu kullanarak kullanıcıya yönelik kısa ve açıklayıcı bir özet yaz."
        )


        response = llm.invoke([HumanMessage(content=user_prompt)])
        summaries.append(response.content)

    return summaries




while True:
    print("\nNe yapmak istersiniz? Aşağıdaki seçeneklerden birini seçebilirsiniz:")
    print("1 - Belirli bir müşteri segmenti için tanımlanmış kampanya (indirim) bilgisini görmek istiyorum.")
    print("2 - Sistemdeki verileri güncellemek istiyorum.")
    print("3 - Belirli bir segmentin ilişkili olduğu kategorileri ve kümeleri görsel olarak incelemek istiyorum.")
    print("4 - Cevaplarıma göre hangi müşteri segmentine ait olduğumu öğrenmek istiyorum.")
    print("5 - Programdan çıkmak istiyorum.")

    choice = input("Lütfen yapmak istediğiniz işlemi kısaca açıklayın veya ilgili numarayı yazın (1/2/3/4): ").strip()

    if choice == "1":
        segment_infos = get_segment_discount_info()
        if segment_infos is None:
            continue

        max_indexes = get_category_max_indexes()
        category_indexes = get_category_indexes_from_csv(segment_infos, max_indexes)
        summary_messages = build_llm_summaries(segment_infos, category_indexes)

        print("\n Özetler:")
        for msg in summary_messages:
            formatted_response = wrap_by_word_count(msg, words_per_line=15)
            print(formatted_response)

    elif choice == "2":
        try:
            update()
            print(" Güncelleme başarıyla tamamlandı.")
        except Exception as e:
            print(f" Güncelleme sırasında bir hata oluştu: {e}")

    elif choice == "5":
        print(" Programdan çıkılıyor...")
        break

    elif choice == "3":
        try:
            segment_input = input("Hangi segmentin grafiğini görmek istersiniz? (Çıkmak için 'çıkış' yazın): ").strip()
            if segment_input.lower() == "çıkış":
                continue
            segment_id = int(segment_input)

            draw_cluster_only_graph(segment_id, driver)
            draw_category_only_graph(segment_id, driver)
        except ValueError:
            print("Lütfen geçerli bir sayı girin.")
        except Exception as e:
            print(f"Grafik oluşturma sırasında hata: {e}")


    elif choice == "4":



        answers = {}

        for key, question in get_segment_questions():

            while True:

                val = input(question + " ").strip()

                if val:

                    answers[key] = val

                    break

                else:

                    print("Lütfen geçerli bir değer girin.")



        segment_id = get_final_segment_id(answers, graph)

        if segment_id is not None:

            print(f"Cevaplarınıza uygun segment ID: {segment_id}")

        else:

            print("Verilen cevaplara uygun bir segment bulunamadı.")


    else:
        print(" Geçersiz seçim. Lütfen 1, 2, 3, 4 veya 5 giriniz.")