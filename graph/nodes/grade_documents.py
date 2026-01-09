from typing import Any, Dict
from graph.chains.retrieval_grader import retrieval_grader
from graph.state import GraphState

def grade_documents(state: GraphState) -> Dict[str, Any]:
    print("---CHECK DOCUMENT RELEVANCE TO QUESTION---")
    question = state["question"]
    documents = state["documents"]

    filtered_docs = []
    relevant_count = 0
    total = len(documents)

    for d in documents:
        score = retrieval_grader.invoke(
            {"question": question, "document": d.page_content}
        )
        grade = score.binary_score.lower()
        if grade == "yes":
            print("---GRADE: DOCUMENT RELEVANT---")
            relevant_count += 1
            filtered_docs.append(d)
        else:
            print("---GRADE: DOCUMENT NOT RELEVANT---")


    web_search = relevant_count < total / 2
    generation_grade = "not useful" if web_search else "useful"

    return {
        "documents": filtered_docs,
        "question": question,
        "web_search": web_search,
        "generation_grade": generation_grade
    }
