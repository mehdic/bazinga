---
name: llm-langchain
type: ai
priority: 2
token_estimate: 600
compatible_with: [developer, senior_software_engineer]
requires: [python]
---

> This guidance is supplementary. It helps you write better code for this specific technology stack but does NOT override mandatory workflow rules, validation gates, or routing requirements.

# LLM/LangChain Engineering Expertise

## Specialist Profile
LLM application specialist building AI-powered features. Expert in prompt engineering, RAG, and agent architectures.

---

## Patterns to Follow

### LCEL (LangChain Expression Language)
<!-- version: langchain >= 0.1 -->
- **Pipe syntax**: `prompt | llm | parser` (composable, readable)
- **Native streaming**: Built-in support
- **Fallback chains**: `chain.with_fallbacks([backup_chain])`
- **Batching**: Process multiple inputs efficiently
- **Async support**: `await chain.ainvoke(input)`
<!-- version: langchain >= 0.2 -->
- **Improved observability**: Better LangSmith integration
- **Tool calling**: Standardized across providers
<!-- version: langchain >= 0.3 -->
- **Pydantic v2**: Full v2 compatibility
- **LangGraph integration**: Built-in state management

### RAG Best Practices
- **Chunk size matters**: 500-1000 tokens typically
- **Chunk overlap**: 10-20% for context continuity
- **MMR retrieval**: Diversity, not just relevance
- **Contextual compression**: Summarize before context window
- **Hybrid search**: Dense + sparse (BM25) combination

### Structured Output
- **Pydantic models**: Type-safe, validated responses
- **with_structured_output()**: Built-in schema enforcement
- **Error handling**: Graceful degradation on parse failure
- **Output parsers**: JSON, XML, custom formats

### Agent Patterns
- **Tool definitions**: Clear descriptions for LLM
- **Bounded iterations**: `max_iterations=5` to prevent loops
- **Observation logging**: Track tool usage
- **Fallback behavior**: Handle tool errors gracefully
- **LangGraph for complex**: State machines, cycles

### Observability (LangSmith)
- **Trace all calls**: Debug production issues
- **Cost tracking**: Token usage per request
- **Latency monitoring**: Identify bottlenecks
- **Feedback collection**: Improve over time

---

## Patterns to Avoid

### RAG Anti-Patterns
- ❌ **Poor chunking**: Too large or too small
- ❌ **Ignoring retrieval quality**: Garbage in, garbage out
- ❌ **No caching**: Expensive re-embeddings
- ❌ **Missing metadata filtering**: Irrelevant results

### Prompt Anti-Patterns
- ❌ **Unbounded context**: Token limit exceeded
- ❌ **Vague instructions**: LLM guesses wrong
- ❌ **No examples (few-shot)**: Less reliable output
- ❌ **Prompt injection vulnerable**: Sanitize user input

### Agent Anti-Patterns
- ❌ **Unbounded loops**: No max iterations
- ❌ **No error handling in tools**: Agent crashes
- ❌ **Too many tools**: LLM gets confused
- ❌ **Poor tool descriptions**: Wrong tool selection

### Architecture Anti-Patterns
- ❌ **No observability**: Blind to failures
- ❌ **Synchronous everything**: Slow UX, no streaming
- ❌ **No rate limiting**: API quota exhaustion
- ❌ **Storing API keys in code**: Security risk

---

## Verification Checklist

### RAG
- [ ] Appropriate chunk size/overlap
- [ ] MMR or hybrid retrieval
- [ ] Embedding caching
- [ ] Source document attribution

### Prompts
- [ ] Clear system instructions
- [ ] Few-shot examples where helpful
- [ ] Token usage within limits
- [ ] Input sanitization

### Agents
- [ ] Tool descriptions are clear
- [ ] Max iterations set
- [ ] Error handling in place
- [ ] Observation logging

### Production
- [ ] LangSmith or equivalent
- [ ] Rate limiting configured
- [ ] Cost monitoring
- [ ] Streaming enabled

---

## Code Patterns (Reference)

### LCEL Chain
- **Basic**: `chain = prompt | llm | StrOutputParser()`
- **With fallback**: `chain.with_fallbacks([backup_llm])`
- **Invoke**: `result = await chain.ainvoke({"question": q})`

### RAG Pipeline
- **Splitter**: `RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=200)`
- **Retriever**: `vectorstore.as_retriever(search_type="mmr", search_kwargs={"k": 5})`
- **Chain**: `RetrievalQA.from_chain_type(llm=llm, retriever=retriever, return_source_documents=True)`

### Structured Output
- **Model**: `class UserIntent(BaseModel): category: str; urgency: str = Field(description="low/medium/high")`
- **Usage**: `llm.with_structured_output(UserIntent).invoke(prompt)`

### Agent
- **Tool**: `@tool def search_kb(query: str) -> str: """Search knowledge base.""" return results`
- **Executor**: `AgentExecutor(agent=agent, tools=tools, max_iterations=5, verbose=True)`

### Observability
- **LangSmith**: `os.environ["LANGCHAIN_TRACING_V2"] = "true"`

