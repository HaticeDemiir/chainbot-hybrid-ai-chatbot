from typing import List, TypedDict, Optional


class UserAttributes(TypedDict, total=False):
    name:Optional[str]
    age: Optional[int]
    size: Optional[str]
    shoe_size: Optional[str]
    gender: Optional[str]
    interests: Optional[str]



class GraphState(TypedDict):
    """
    Represents the state of our graph.

    Attributes:
        question: Soru
        generation: LLM generation
        web_search: Arama yapılıp yapılmayacağı
        documents: Belgeler listesi
        uid: Kullanıcı ID'si
        user_data: Dışarıdan gelen bilgiler (sorulardan gelen)
        source: Hangi datasource seçildi ("vectorstore", "discount", "beden", ...)
    """
    question: str
    generation: str
    web_search: bool
    documents: List[str]
    uid: Optional[str]
    user_attributes: Optional[UserAttributes]
    user_data: Optional[str]
    source: Optional[str]
    knowledge_graph_discount_result: Optional[str]
    knowledge_graph_size_result: Optional[str]
    discount_shown:bool
    generation_grade: str