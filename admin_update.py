import pandas as pd
import ast
import os
from dotenv import load_dotenv
from langchain_community.graphs import Neo4jGraph

load_dotenv()

uri = os.getenv("NEO4J_URI")
username = os.getenv("NEO4J_USERNAME")
password = os.getenv("NEO4J_PASSWORD")
database = os.getenv("NEO4J_DATABASE")

graph = Neo4jGraph(
    url=uri,
    username=username,
    password=password,
    database=database
)


discounts_up = pd.read_csv("Datas/final_discount2.csv", sep=";")

def update():
        for _, row in discounts_up.iterrows():
            try:
                seg_id = int(row["final_segment_id"])
                category = row["Category"]
                ratio = float(row["Discount_Ratio"])
                predicted = float(row["Predicted_Ratio"])

                parameters = {
                    "Segment": seg_id,
                    "Category": category,
                    "Discount_Ratio": ratio,
                    "Predicted_Ratio": predicted
                }

                query = """
                        MATCH (fs:FinalSegment {id: $Segment})-[r:HAS_DISCOUNT]->(c:Category {name: $Category})
                        SET r.ratio = $Discount_Ratio,
                            r.predicted = $Predicted_Ratio
                        """

                graph.query(query, params=parameters)

            except Exception as e:
                print(f"Güncelleme hatası: {e}")

        print(" Tüm veriler başarıyla Neo4j'e yüklendi!")
