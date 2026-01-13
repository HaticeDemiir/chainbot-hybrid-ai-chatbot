# ChainBot – Hybrid AI Customer Assistant

ChainBot is a multi-module, hybrid AI-powered chatbot developed as a computer engineering graduation project.  
The system dynamically routes user queries between multiple intelligent modules to provide accurate, contextual and personalized responses.

---

##  Project Overview

ChainBot is designed to simulate a real-world enterprise customer assistant scenario.  
It combines Retrieval-Augmented Generation (RAG), a Knowledge Graph, web search and a general-purpose LLM into a single, coordinated system.

The chatbot supports both:
- Corporate-specific queries (e.g. return policies, cancellations and size guides of a retail company)
- General-purpose conversations and information queries

The system is designed to be adaptable across different industries such as retail, e-commerce and customer support.

---

##  System Architecture

The system uses **LangGraph** to control conversational flow and dynamically select the appropriate response strategy.

![Architecture Diagram](system_architecture.png)

---

##  Core Features

- **Dynamic Routing with LangGraph**
  - Automatically decides whether a query should be handled by:
    - RAG (ChromaDB)
    - Knowledge Graph (Neo4j)
    - Web Search
    - General LLM response

- **Retrieval-Augmented Generation (RAG)**
  - Corporate documents are embedded and stored in **ChromaDB**
  - Document relevance is graded before response generation

- **Knowledge Graph Integration (Neo4j)**
  - User attributes are stored and updated in real time
  - Enables segmentation-based discount campaigns
  - Supports personalized size and product recommendations

- **User Profiling & Memory**
  - Demographic and conversational attributes are linked to a user ID
  - Context is preserved across the session for coherent dialogue

- **Web Search Module**
  - Handles questions outside the corporate knowledge base

- **Admin & Campaign Management**
  - Segment-based discount ratios can be dynamically updated

---

##  Technologies Used

- Python
- LangChain & LangGraph
- OpenAI API
- ChromaDB
- Neo4j
- Tavily Web Search API
- HTML / CSS / JavaScript

---

##  How It Works

1. When a user sends a message, it is first processed by the **Extract Node**.
   - User intent is identified.
   - Demographic and contextual attributes (such as gender, age, size preferences) are extracted.
   - Extracted information is stored in the shared graph state.

2. The updated state is passed to the **Routing Module** implemented with LangGraph.
   - The router decides which processing path to follow based on the extracted intent and context.

3. Based on the routing decision, one of the following modules is triggered:
   - **RAG Pipeline** for corporate documents stored in ChromaDB
   - **Knowledge Graph Query** (Neo4j) for user-specific data such as segmentation, discounts and size recommendations
   - **Web Search Module** for open-domain questions
   - **General LLM Response** for casual or conversational queries

4. The selected module generates a response.
5. User attributes and conversation memory are updated to preserve contextual continuity.
6. The final response is returned to the user.

---

##  Example Use Cases


- A customer asks about return or cancellation policies of a company  
  → The RAG module retrieves relevant corporate documents and generates a grounded response.

- A user asks for personalized size or product recommendations  
  → The Knowledge Graph is queried using stored user attributes.

- A user asks a general knowledge question unrelated to corporate content  
  → The Web Search module is triggered.

- A casual conversational message is sent  
  → The General LLM response path is used.
---

##  Limitations & Future Work

- User authentication and long-term persistence can be improved.
- A dedicated user interface can be developed for better user experience.
- Voice-based interaction can be integrated for hands-free usage.
- Multi-language support can be added for broader accessibility.

##  Team

This project was developed as a **team-based graduation project**.

- **Hatice Demir** 
- **Bahar Davutoğlu**
- **Zeynep Aktaş**

## Academic Note

This project was developed as a graduation project for academic purposes.
The architecture and datasets are representative and do not belong to any real company.


