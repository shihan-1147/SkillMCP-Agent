# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [1.0.0] - 2024-01-19

### Added

#### Core Infrastructure
- **Config Management**: Pydantic-based settings with environment variable support
- **Logging System**: Structured logging with configurable levels
- **Exception Handling**: Custom exception hierarchy for better error handling

#### Agent Core
- **AgentOrchestrator**: Central orchestrator for task execution
- **Planner**: Intent recognition and task decomposition
- **Executor**: Task execution engine
- **Reasoner**: Response synthesis from tool outputs
- **Memory**: Conversation history management
- **AgentTracer**: Complete execution tracing with timeline visualization
- **ToolRecorder**: Tool call recording with statistics and reporting

#### Skills Layer
- **BaseSkill**: Abstract skill base class
- **SkillRegistry**: Automatic skill registration via decorators
- Built-in Skills:
  - `travel_skill`: Travel planning assistance
  - `weather_skill`: Weather query handling
  - `knowledge_skill`: Knowledge base Q&A
  - `summarize_skill`: Text summarization
  - `direct_answer_skill`: Direct answer generation

#### MCP (Model Context Protocol)
- **MCPServer**: MCP-compliant tool server
- **MCPClient**: Client for tool discovery and invocation
- **BaseTool**: Abstract tool base class with JSON Schema parameter validation
- Built-in Tools:
  - `train_query`: 12306 train ticket queries (mock)
  - `weather_query`: Weather API integration (mock)
  - `system_time`: System time and date calculations
  - `rag_retriever`: RAG knowledge retrieval

#### RAG (Retrieval-Augmented Generation)
- **RAGPipeline**: End-to-end RAG pipeline
- **DocumentLoader**: Multi-format document loading (PDF, DOCX, MD, TXT)
- **TextChunker**: Intelligent text chunking with overlap
- **Embedder**: Embedding abstraction with multiple backends
  - `OllamaEmbedder`: Local Ollama embedding
  - `OpenAIEmbedder`: OpenAI API embedding
  - `MockEmbedder`: Testing mock
- **VectorStore**: FAISS-based vector storage
- **Retriever**: Similarity-based document retrieval

#### API Layer
- **FastAPI Application**: High-performance async API
- **Chat Endpoint**: `/api/v1/chat` for conversations
- **Stream Endpoint**: `/api/v1/chat/stream` for SSE streaming
- **Health Endpoint**: `/api/v1/health` for monitoring
- **Session Management**: Stateful conversation sessions

#### Frontend
- **Vue 3 + Vite**: Modern frontend stack
- **Element Plus**: UI component library
- **ConsoleView**: Main chat interface
- **MessageBubble**: Chat message rendering
- **StructuredCard**: Structured data display (weather, train tickets)
- **AgentProgress**: Execution progress indicator
- **DebugPanel**: Developer tools panel

#### Documentation
- **README.md**: Comprehensive project documentation
- **EXTENSION_GUIDE.md**: Guide for extending skills and tools
- **.env.example**: Environment configuration template

### Technical Highlights
- Fully async architecture with Python 3.10+
- Multi-model support: Ollama (local) and OpenAI (cloud)
- Hot-pluggable skill and tool registration
- Complete execution tracing for debugging
- Production-ready project structure

---

## [Unreleased]

### Planned
- [ ] LLM-powered intent classification
- [ ] Real API integrations (weather, 12306)
- [ ] Persistent RAG index storage
- [ ] Multi-user session isolation
- [ ] WebSocket streaming support
- [ ] Docker containerization
- [ ] Kubernetes deployment manifests
