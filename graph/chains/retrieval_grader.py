from langchain_core.prompts import ChatPromptTemplate
from langchain_core.pydantic_v1 import BaseModel, Field
from langchain_openai import ChatOpenAI

llm = ChatOpenAI(model="gpt-3.5-turbo", temperature=0.1)

class GradeDocuments(BaseModel):
    """Binary score for relevance check on retrieved documents."""

    binary_score: str = Field(
        description="Documents are relevant to the question, 'yes' or 'no'"
    )

structured_llm_grader = llm.with_structured_output(GradeDocuments)

system = """You are a relevance grader working for an LC Waikiki assistant.
Your job is to decide if a retrieved document answers the user's question.

Instructions:
- Focus on SEMANTIC MEANING rather than exact keyword match.
- Consider different question variations, rewordings, and synonyms.
- If the document **partially or generally answers** the question, return "yes".
- If the document is entirely unrelated or completely off-topic, return "no".

Examples:
Q: "How do I return a product?" — Relevant if the document includes return instructions, even if phrased differently.
Q: "Where is my order?" — Relevant if the document explains order tracking, status, or shipment.

Answer strictly with "yes" or "no".
"""

grade_prompt = ChatPromptTemplate.from_messages(
    [
        ("system", system),
        ("human", "Document:\n\n{document}\n\nQuestion:\n{question}"),
    ]
)

retrieval_grader = grade_prompt | structured_llm_grader
