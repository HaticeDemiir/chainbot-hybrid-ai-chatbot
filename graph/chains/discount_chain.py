from langchain_core.runnables import RunnableLambda
from langchain_community.graphs import Neo4jGraph
import os
from dotenv import load_dotenv

load_dotenv()

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE")
)

def handle_user_and_segment():
    try:

        age = int(input("Yaşınız kaç? "))
        customer_segment = input("Müşteri tipiniz nedir? (New/Regular/Premium): ")
        income = input("Gelir seviyenizi seçin (Low/Medium/High): ")
        shopping_count = int(input("Alışveriş sıklığınız nedir?: "))
        total_purchase = float(input("Toplam harcamanız ne düzeyde?: "))

        segment_clusters = []


        queries = [
            ("""
             MATCH (sc:SegmentCluster)
             WHERE sc.name STARTS WITH 'AgeCluster'
               AND sc.min <= $value AND $value <= sc.max
             RETURN sc.id AS cluster_id
             """, {"value": age}),
            ("""
             MATCH (sc:SegmentCluster)-[:HAS_VALUE]->(v:Value)
             WHERE sc.name STARTS WITH 'CustomerSegment'
               AND v.name = $value
             RETURN sc.id AS cluster_id
             """, {"value": customer_segment}),
            ("""
             MATCH (sc:SegmentCluster)-[:HAS_VALUE]->(v:Value)
             WHERE sc.name STARTS WITH 'IncomeCluster'
               AND v.name = $value
             RETURN sc.id AS cluster_id
             """, {"value": income}),
            ("""
             MATCH (sc:SegmentCluster)
             WHERE sc.name STARTS WITH 'ShoppingCountCluster'
               AND sc.min <= $value AND $value <= sc.max
             RETURN sc.id AS cluster_id
             """, {"value": shopping_count}),
            ("""
             MATCH (sc:SegmentCluster)
             WHERE sc.name STARTS WITH 'TotalPurchaseCluster'
               AND sc.min <= $value AND $value <= sc.max
             RETURN sc.id AS cluster_id
             """, {"value": total_purchase}),
        ]

        for query, param in queries:
            result = graph.query(query, params=param)
            if result and result[0].get("cluster_id"):
                segment_clusters.append(result[0]["cluster_id"])


        result = graph.query("MATCH (u:UID) RETURN MAX(toInteger(u.value)) AS max_uid")
        max_uid = result[0]["max_uid"] if result and result[0]["max_uid"] is not None else 0
        uid_value = str(max_uid + 1).zfill(4)
        graph.query("CREATE (u:UID {value: $uid_value})", params={"uid_value": uid_value})


        segment_query = """
            UNWIND $cluster_ids AS cluster_id
            MATCH (sc:SegmentCluster {id: cluster_id})
            WITH collect(sc) AS clusters
            MATCH (fs:FinalSegment)
            WHERE ALL(c IN clusters WHERE (fs)-[:CONTAINS]->(c))
            RETURN fs.id AS final_segment_id
        """
        match_result = graph.query(segment_query, {"cluster_ids": segment_clusters})

        if not match_result:
            return {"generation": "Sizin için uygun bir segment bulunamadı."}

        final_segment_id = match_result[0]["final_segment_id"]
        graph.query("""
            MATCH (u:UID {value: $uid_value})
            MATCH (fs:FinalSegment {id: $fid})
            MERGE (u)-[:HAS_SEGMENT]->(fs)
        """, {"uid_value": uid_value, "fid": final_segment_id})

        return {
            "generation": f"Yeni kullanıcı ID’niz oluşturuldu: {uid_value}",
            "uid": uid_value
        }
    except Exception as e:
        return {"generation": f"Hata oluştu: {str(e)}"}

def get_discount_info(uid_value: str) -> str:
    discount_query = """
        MATCH (u:UID {value: $uid_value})-[:HAS_SEGMENT]->(fs:FinalSegment)
        MATCH (fs)-[r:HAS_DISCOUNT]->(c:Category)
        RETURN c.name AS category, r.ratio AS discount_ratio
    """
    discount_result = graph.query(discount_query, params={"uid_value": uid_value})

    if not discount_result:
        return "İndirim bilgisi bulunamadı."

    return "\n".join([
        f"{row['category']} → %{int(row['discount_ratio'] * 100)} indirim"
        for row in discount_result
    ])

def discount():
    def inner(state):
        uid_value = state.get("uid")

        if not uid_value:
            response = handle_user_and_segment()
            if not response or not isinstance(response, dict):
                return {"generation": "Bir hata oluştu."}
            uid_value = response.get("uid")
            if not uid_value:
                return response


        check_query = """
            MATCH (u:UID {value: $uid_value})-[:HAS_SEGMENT]->(fs:FinalSegment)
            RETURN fs.id AS final_segment_id
        """
        assigned = graph.query(check_query, {"uid_value": uid_value})
        if not assigned:
            return {"generation": "UID’inize ait segment bulunamadı."}

        response = get_discount_info(uid_value)
        return {
            "generation": f"ID’niz : {uid_value}\n{response}",
            "uid": uid_value
        }

    return RunnableLambda(inner)