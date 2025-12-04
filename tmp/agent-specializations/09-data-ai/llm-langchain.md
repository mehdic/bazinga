---
name: llm-langchain
type: ai
priority: 2
token_estimate: 400
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> **PRECEDENCE**: Base agent workflow rules take precedence over this guidance.

# LLM/LangChain Engineering Expertise

## Specialist Profile
LLM application specialist building AI-powered features. Expert in prompt engineering, RAG, and agent architectures.

## Implementation Guidelines

### RAG Pipeline

```python
# src/rag/retriever.py
from langchain_openai import OpenAIEmbeddings, ChatOpenAI
from langchain_community.vectorstores import Chroma
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.chains import RetrievalQA

def create_rag_chain(documents: list[Document]):
    # Split documents
    splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
    )
    chunks = splitter.split_documents(documents)

    # Create vector store
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    vectorstore = Chroma.from_documents(
        documents=chunks,
        embedding=embeddings,
        persist_directory="./chroma_db",
    )

    # Create retriever
    retriever = vectorstore.as_retriever(
        search_type="mmr",
        search_kwargs={"k": 5, "fetch_k": 10},
    )

    # Create chain
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)

    return RetrievalQA.from_chain_type(
        llm=llm,
        chain_type="stuff",
        retriever=retriever,
        return_source_documents=True,
    )
```

### Structured Output

```python
# src/extraction/structured.py
from langchain_openai import ChatOpenAI
from langchain_core.pydantic_v1 import BaseModel, Field

class UserIntent(BaseModel):
    """Extracted user intent from message."""
    category: str = Field(description="Intent category: support, sales, feedback")
    urgency: str = Field(description="Urgency level: low, medium, high")
    summary: str = Field(description="Brief summary of the request")
    entities: list[str] = Field(description="Key entities mentioned")

def extract_intent(message: str) -> UserIntent:
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
    structured_llm = llm.with_structured_output(UserIntent)

    return structured_llm.invoke(
        f"Extract the user intent from this message:\n\n{message}"
    )
```

### Agent with Tools

```python
# src/agents/support_agent.py
from langchain.agents import create_openai_functions_agent, AgentExecutor
from langchain_core.tools import tool
from langchain_openai import ChatOpenAI

@tool
def search_knowledge_base(query: str) -> str:
    """Search the support knowledge base for relevant articles."""
    results = kb_search(query, limit=3)
    return "\n".join([f"- {r.title}: {r.summary}" for r in results])

@tool
def get_user_orders(user_id: str) -> str:
    """Get recent orders for a user."""
    orders = db.orders.find(user_id=user_id, limit=5)
    return json.dumps([o.to_dict() for o in orders])

@tool
def create_ticket(summary: str, priority: str) -> str:
    """Create a support ticket."""
    ticket = support.create_ticket(summary=summary, priority=priority)
    return f"Created ticket #{ticket.id}"

def create_support_agent():
    llm = ChatOpenAI(model="gpt-4-turbo-preview", temperature=0)
    tools = [search_knowledge_base, get_user_orders, create_ticket]

    prompt = hub.pull("hwchase17/openai-functions-agent")
    agent = create_openai_functions_agent(llm, tools, prompt)

    return AgentExecutor(
        agent=agent,
        tools=tools,
        verbose=True,
        max_iterations=5,
    )
```

## Patterns to Avoid
- ❌ Unbounded context windows
- ❌ No output validation
- ❌ Missing rate limiting
- ❌ Prompt injection vulnerabilities

## Verification Checklist
- [ ] Structured outputs with Pydantic
- [ ] Chunking strategy for RAG
- [ ] Tool error handling
- [ ] Token usage monitoring
- [ ] Response validation
