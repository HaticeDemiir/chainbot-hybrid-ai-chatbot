from graph.state import GraphState
from neo4j import GraphDatabase
from langchain_community.graphs import Neo4jGraph
import os
from langchain_core.runnables import RunnableLambda
from graph.chains.extract_user_attributes import extract_chain


graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE")
)



def extract_user_attributes(state: GraphState) -> dict:
    question = state.get("question", "")

    uid = state.get("uid")
    if not uid:
        return {}

    print(f"---USER ID VAR ({uid}): Attribute extraction yapılacak---")
    try:
        result = extract_chain.invoke({"question": question})
        if not result or not isinstance(result, dict):
            print(" Çıkarım yapılacak özellik yok.")
            return {}

        filtered = {k: v for k, v in result.items() if v not in [None, "", 0]}
        print("Çıkarımlar alındı:", filtered)
        return filtered

    except Exception as e:
        print(f" Çıkarım sırasında hata oluştu: {e}")
        return {}






def create_user_attribute_nodes(tx, uid, attributes):
    from datetime import date

    try:
        shoe_size = int(attributes.get("shoe_size")) if attributes.get("shoe_size") is not None else None
    except ValueError:
        shoe_size = None

    try:
        birth_year = date.today().year - int(attributes.get("age")) if attributes.get("age") is not None else None
    except ValueError:
        birth_year = None

    interests = attributes.get("interests")
    if interests and not isinstance(interests, list):
        interests = [interests]
    elif not interests:
        interests = None


    if shoe_size is not None:
        tx.run("""
            MERGE (u:UID {value: $uid})
            WITH u
            OPTIONAL MATCH (u)-[r:HAS_SHOE_SIZE]->(:ShoeSize)
            DELETE r
            WITH u
            MERGE (sh:ShoeSize {numara: $shoe_size})
            MERGE (u)-[:HAS_SHOE_SIZE]->(sh)
        """, uid=uid, shoe_size=shoe_size)

    if interests:
        tx.run("""
            MERGE (u:UID {value: $uid})
            WITH u
            OPTIONAL MATCH (u)-[r:HAS_INTEREST]->(:Interest)
            DELETE r
            WITH u
            UNWIND $interests AS interest
            MERGE (i:Interest {name: interest})
            MERGE (u)-[:HAS_INTEREST]->(i)
        """, uid=uid, interests=interests)

    if attributes.get("size"):
        tx.run("""
            MATCH (u:UID {value: $uid})-[:HAS_NAME]->(n:Name)
            WHERE n.gender IS NOT NULL
            WITH u, n.gender AS gender_raw, $size AS size
            WITH u, size, apoc.text.capitalize(gender_raw) AS gender, apoc.text.capitalize(gender_raw) + "_" + size AS size_name
            OPTIONAL MATCH (u)-[r:HAS_SIZE]->(:Size)
            DELETE r
            MERGE (s:Size {name: size_name})
            SET s.gender = gender,
                s.beden = size
            MERGE (u)-[:HAS_SIZE]->(s)
        """, uid=uid, size=attributes.get("size"))

    if birth_year is not None:
        tx.run("""
            MERGE (u:UID {value: $uid})
            WITH u
            OPTIONAL MATCH (u)-[r:HAS_BIRTHDATE]->(:BirthYear)
            DELETE r
            WITH u
            MERGE (b:BirthYear {value: $birth_year})
            MERGE (u)-[:HAS_BIRTHDATE]->(b)
        """, uid=uid, birth_year=birth_year)

    if attributes.get("name"):
        gender = attributes.get("gender")
        if gender:
            gender = gender.capitalize()
            tx.run("""
                MERGE (u:UID {value: $uid})
                WITH u
                OPTIONAL MATCH (u)-[r:HAS_NAME]->(:Name)
                DELETE r
                WITH u
                MERGE (n:Name {value: $name})
                SET n.gender = $gender
                MERGE (u)-[:HAS_NAME]->(n)
            """, uid=uid, name=attributes.get("name"),gender = gender)
        else:
            tx.run("""
                MERGE (u:UID {value: $uid})
                WITH u
                OPTIONAL MATCH (u)-[r:HAS_NAME]->(:Name)
                DELETE r
                WITH u
                MERGE (n:Name {value: $name})
                MERGE (u)-[:HAS_NAME]->(n)
            """, uid=uid, name=attributes.get("name"))


def neo4j_update(uid, attributes):
    if uid and attributes:
        print("kaydedilecekler:", attributes)
        print("Bilgileriniz kaydediliyor...")
        merged = {}
        for attr in attributes:
            for key, value in attr.items():
                if value not in [None, "", 0]:
                    merged[key] = value

        driver = GraphDatabase.driver(
            os.getenv("NEO4J_URI"),
            auth=(os.getenv("NEO4J_USERNAME"), os.getenv("NEO4J_PASSWORD"))
        )
        with driver.session(database=os.getenv("NEO4J_DATABASE")) as session:
            session.execute_write(
                create_user_attribute_nodes,
                uid,
                merged
            )
        driver.close()
        print("Bilgiler başarıyla kaydedildi.")




def extraction():
    def inner(state: GraphState):
        extraction_list = []
        uid = state.get("uid")
        if "uid" in state:
            attributes = extract_user_attributes(state)
            if attributes:
                print("✔ Çıkarımlar alındı:", attributes)
                extraction_list.append(attributes)
                if uid and extraction_list:
                    neo4j_update(uid, extraction_list)
        return state

    return RunnableLambda(inner)