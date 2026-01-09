from typing import Any, Dict
from graph.chains.generation import generation_chain
from graph.state import GraphState
from langchain_community.graphs import Neo4jGraph
import os
from dotenv import load_dotenv
from graph.nodes.knowledge_graph import get_user_profile_str

load_dotenv()
graph = Neo4jGraph(
    url=os.getenv("NEO4J_URI"),
    username=os.getenv("NEO4J_USERNAME"),
    password=os.getenv("NEO4J_PASSWORD"),
    database=os.getenv("NEO4J_DATABASE")
)

def generate(state: GraphState) -> Dict[str, Any]:
    print("---GENERATE---")

    question = state["question"]
    documents = state["documents"]
    uid = state.get("uid")
    knowledge_graph_d = state["knowledge_graph_discount_result"]
    knowledge_graph_s = state["knowledge_graph_size_result"]

    user_profile = get_user_profile_str(uid, graph) if uid else ""

    generation = generation_chain.invoke({
        "context": documents,
        "question": question,
        "user_profile": user_profile,
        "knowledge_graph_discount_result": knowledge_graph_d,
        "knowledge_graph_size_result": knowledge_graph_s

    })

    return {
        "documents": documents,
        "question": question,
        "generation": generation,
        "generation_grade": "useful",
        "knowledge_graph_discount_result": knowledge_graph_d,
        "knowledge_graph_size_result": knowledge_graph_s
    }