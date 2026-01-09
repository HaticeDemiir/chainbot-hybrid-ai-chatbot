from langchain_core.runnables import RunnableLambda
from langchain_community.graphs import Neo4jGraph
import os
from dotenv import load_dotenv
from graph.state import GraphState
from graph.chains.discount_chain import discount
from graph.chains.size_chain import size_chain
from graph.chains.router import question_router
load_dotenv()

graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE")
)


def knowledge_graph():
    def inner(state: GraphState):
        question = state.get("question", "")

        route = question_router.invoke({"question": question})
        source = route.datasource if route else None
        print(f"---KNOWLEDGE GRAPH: belirlenen kaynak türü: {source} ---")
        kg_dresults={}
        kg_sresults={}


        if source == "discount":
            result = discount().invoke(state)
            if result is not None:
                kg_dresults = result
            state["knowledge_graph_discount_result"] = kg_dresults
            state["discount_shown"] = True
        elif source == "size":
            result = size_chain().invoke(state)
            if result is not None:
                kg_sresults = result
            state["knowledge_graph_size_result"] = kg_sresults

        return state

    return RunnableLambda(inner)



def get_user_profile_str(uid: str, graph) -> str:

        query = """
        MATCH (u:UID {value: $uid})
        OPTIONAL MATCH (u)-[:HAS_NAME]->(n:Name)
        RETURN n.value AS name
        """
        try:
            result = graph.query(query, params={"uid": uid})
            if result and result[0].get("name"):
                return result[0]["name"]
        except Exception as e:
            print(f" İsim alınamadı: {e}")
        return ""


def create_user_from_segments(answers: dict) -> dict:
    try:
        age = int(answers.get("age"))
        customer_type = answers.get("customer_type", "").capitalize()
        income = answers.get("income", "").capitalize()
        shopping_count = int(answers.get("shopping_count"))
        total_spend = float(answers.get("total_spend"))

        cluster_ids = []
        queries = [
            ("MATCH (sc:SegmentCluster) WHERE sc.name STARTS WITH 'AgeCluster' AND sc.min <= $v AND $v <= sc.max RETURN sc.id AS cid", {"v": age}),
            ("MATCH (sc:SegmentCluster)-[:HAS_VALUE]->(val:Value) WHERE sc.name STARTS WITH 'CustomerSegment' AND val.name = $v RETURN sc.id AS cid", {"v": customer_type}),
            ("MATCH (sc:SegmentCluster)-[:HAS_VALUE]->(val:Value) WHERE sc.name STARTS WITH 'IncomeCluster' AND val.name = $v RETURN sc.id AS cid", {"v": income}),
            ("MATCH (sc:SegmentCluster) WHERE sc.name STARTS WITH 'ShoppingCountCluster' AND sc.min <= $v AND $v <= sc.max RETURN sc.id AS cid", {"v": shopping_count}),
            ("MATCH (sc:SegmentCluster) WHERE sc.name STARTS WITH 'TotalPurchaseCluster' AND sc.min <= $v AND $v <= sc.max RETURN sc.id AS cid", {"v": total_spend}),
        ]

        for query, param in queries:
            result = graph.query(query, params=param)
            if result and result[0].get("cid"):
                cluster_ids.append(result[0]["cid"])

        result = graph.query("MATCH (u:UID) RETURN MAX(toInteger(u.value)) AS max_uid")
        max_uid = result[0]["max_uid"] or 0
        new_uid = str(max_uid + 1).zfill(4)
        graph.query("CREATE (u:UID {value: $val})", {"val": new_uid})

        seg_match = graph.query("""
            UNWIND $ids AS cid
            MATCH (sc:SegmentCluster {id: cid})
            WITH collect(sc) AS cs
            MATCH (fs:FinalSegment)
            WHERE ALL(c IN cs WHERE (fs)-[:CONTAINS]->(c))
            RETURN fs.id AS segment_id
        """, {"ids": cluster_ids})

        if not seg_match:
            return {"generation": " Uygun segment bulunamadı."}

        seg_id = seg_match[0]["segment_id"]
        graph.query("""
            MATCH (u:UID {value: $uid})
            MATCH (fs:FinalSegment {id: $sid})
            MERGE (u)-[:HAS_SEGMENT]->(fs)
        """, {"uid": new_uid, "sid": seg_id})


        graph.query("""
                    MATCH (u:UID {value: $uid})
                    CREATE (a:Answers {
                        age: $age,
                        income: $income,
                        customer_type: $customer_type,
                        shopping_count: $shopping_count,
                        total_spend: $total_spend
                    })
                    MERGE (u)-[:HAS_ANSWER]->(a)
                """, {
            "uid": new_uid,
            "age": age,
            "income": income,
            "customer_type": customer_type,
            "shopping_count": shopping_count,
            "total_spend": total_spend
        })
        return {"uid": new_uid}

    except Exception as e:
        return {"generation": f" Segment tabanlı kullanıcı oluşturulamadı: {e}"}