import pandas as pd
import ast
import os
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph

# Ortam değişkenlerini yükle
load_dotenv()
uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
database = os.getenv("NEO4J_DATABASE")

# Neo4j bağlantısı
graph = Neo4jGraph(
    url=uri,
    username=username,
    password=password,
    database=database
)

# CSV dosyalarını oku
segments_df = pd.read_csv("Datas/final_segments.csv")
clusters_df = pd.read_csv("Datas/segment_cluster.csv")
discounts_df = pd.read_csv("Datas/final_discount2.csv", sep=";")

# ----------------------------
# 1. SegmentCluster ↔ SegmentType ↔ ControlTable ↔ Value
# ----------------------------
for _, row in clusters_df.iterrows():
    try:
        cid = int(row["segment_clusterid"])
        ctype = int(row["segment_typeid"])
        cname = row["cluster_name"]
        control_table = row["control_table"]
        control_column = row["control_column"]
        min_val = int(row["min"]) if pd.notna(row["min"]) else None
        max_val = int(row["max"]) if pd.notna(row["max"]) else None
        value = row["value"] if pd.notna(row["value"]) else None

        parameters = {
            "segment_clusterid": cid,
            "segment_typeid": ctype,
            "control_table": control_table,
            "control_column": control_column,
            "min": min_val,
            "max": max_val,
            "value": value,
            "cluster_name": cname
        }

        query = """
        MERGE (sc:SegmentCluster {id: $segment_clusterid})
        MERGE (st:SegmentType {id: $segment_typeid})
        MERGE (ct:ControlTable {name: $control_table})
        MERGE (st)-[:STORED_IN]->(ct)
        MERGE (sc)-[:BELONGS_TO]->(st)
        SET sc.name = $cluster_name
        SET st.name = $control_column

        FOREACH (_ IN CASE WHEN $min IS NOT NULL AND $max IS NOT NULL THEN [1] ELSE [] END |
            SET st.min = $min, st.max = $max
        )

        FOREACH (_ IN CASE WHEN $value IS NOT NULL THEN [1] ELSE [] END |
            MERGE (v:Value {name: $value})
            MERGE (st)-[:HAS_VALUE]->(v)
        )
        """
        graph.query(query, params=parameters)

    except Exception as e:
        print(f"SegmentCluster yükleme hatası: {e}")

# ----------------------------
# 2. FinalSegment → SegmentCluster bağlantısı
# ----------------------------
for _, row in segments_df.iterrows():
    try:
        final_id = int(row["final_segment_id"])
        cluster_ids = ast.literal_eval(row["segment_cluster_ids"])

        parameters = {
            "final_segment_id": final_id,
            "cluster_ids": cluster_ids
        }

        query = """
        MERGE (fs:FinalSegment {id: $final_segment_id})
        WITH fs, $cluster_ids AS cluster_ids
        UNWIND cluster_ids AS cid
        MERGE (sc:SegmentCluster {id: cid})
        MERGE (fs)-[:CONTAINS]->(sc)
        """
        graph.query(query, params=parameters)

    except Exception as e:
        print(f"FinalSegment bağlama hatası: {e}")

# ----------------------------
# 3. FinalSegment → Category bağlantısı (HAS_DISCOUNT)
# ----------------------------
for _, row in discounts_df.iterrows():
    try:
        seg_id = int(row["final_segment_id"])
        category = row["Category"]
        disc_ratio = float(row["Discount_Ratio"])

        parameters = {
            "Segment": seg_id,
            "Category": category,
            "Discount_Ratio": disc_ratio
        }

        query = """
        MERGE (fs:FinalSegment {id: $Segment})
        MERGE (c:Category {name: $Category})
        MERGE (fs)-[:HAS_DISCOUNT {ratio: $Discount_Ratio}]->(c)
        """
        graph.query(query, params=parameters)

    except Exception as e:
        print(f"İndirim bağlama hatası: {e}")

print(" Tüm veriler başarıyla Neo4j'e yüklendi!")
