from langgraph.graph import StateGraph, END
from graph.chains.router import question_router, RouteQuery
from graph.node_constants import RETRIEVE, GRADE_DOCUMENTS, GENERATE, WEBSEARCH, LLM_RESPONSE, KNOWLEGDE_GRAPH, EXTRACT
from graph.nodes import generate, grade_documents, retrieve, web_search, llm_response, knowledge_graph,extract
from graph.state import GraphState


def route_question(state: GraphState) -> str:
    print("---ROUTE QUESTION---")
    question = state["question"]


    route_query: RouteQuery = question_router.invoke({"question": question})
    datasource = route_query.datasource
    state["source"] = datasource


    if datasource == "websearch":
        print("---ROUTE QUESTION TO WEB SEARCH---")
        return WEBSEARCH
    elif datasource == "vectorstore":
        print("---ROUTE QUESTION TO RAG---")
        return RETRIEVE
    elif datasource == "discount":
        print("---ROUTE QUESTION TO DISCOUNT---")
        return KNOWLEGDE_GRAPH
    elif datasource == "size":
        print("---ROUTE QUESTION TO SIZE---")
        return KNOWLEGDE_GRAPH
    else:
        print("---ROUTE QUESTION TO LLM RESPONSE---")
        return LLM_RESPONSE


def decide_to_generate(state):
    if state.get("web_search", False):
        print("---DECISION: INCLUDE WEB SEARCH---")
        return WEBSEARCH
    else:
        print("---DECISION: GENERATE RESPONSE---")
        return GENERATE


def grade_generation_grounded_in_documents_and_question(state: GraphState) -> str:
    print("---CHECK HALLUCINATIONS---")
    score = state.get("generation_grade", "useful")
    if score == "useful":
        print("---DECISION: GENERATION ADDRESSES QUESTION---")
        return "useful"
    else:
        print("---DECISION: RE-TRY WEB SEARCH---")
        return "not useful"


workflow = StateGraph(GraphState)

workflow.add_node(EXTRACT,extract.extraction())
workflow.add_node(RETRIEVE, retrieve)
workflow.add_node(GRADE_DOCUMENTS, grade_documents)
workflow.add_node(GENERATE, generate)
workflow.add_node(WEBSEARCH, web_search)
workflow.add_node(LLM_RESPONSE, llm_response)
workflow.add_node(KNOWLEGDE_GRAPH, knowledge_graph.knowledge_graph())


workflow.set_entry_point(EXTRACT)


workflow.add_conditional_edges(
    EXTRACT,
    route_question,
    {
        WEBSEARCH: WEBSEARCH,
        RETRIEVE: RETRIEVE,
        KNOWLEGDE_GRAPH: KNOWLEGDE_GRAPH,
        LLM_RESPONSE: LLM_RESPONSE,
    },
)

workflow.add_edge(RETRIEVE, GRADE_DOCUMENTS)
workflow.add_conditional_edges(
    GRADE_DOCUMENTS,
    decide_to_generate,
    {
        WEBSEARCH: WEBSEARCH,
        GENERATE: GENERATE,
    },
)

workflow.add_conditional_edges(
    GENERATE,
    grade_generation_grounded_in_documents_and_question,
    {
        "useful": END,
        "not useful": WEBSEARCH,
        "not supported": GENERATE,
    },
)

workflow.add_edge(WEBSEARCH, GENERATE)
workflow.add_edge(LLM_RESPONSE, END)
workflow.add_edge(KNOWLEGDE_GRAPH, GENERATE)

app = workflow.compile()
app.get_graph().draw_mermaid_png(output_file_path="graph.png")