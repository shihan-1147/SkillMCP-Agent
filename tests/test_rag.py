"""
RAG 子系统测试脚本

演示完整的 RAG 工作流程：
1. 加载文档
2. 切分文本
3. 向量化
4. 存储到 FAISS
5. 检索相关内容
6. 注入到 Prompt
"""
import asyncio
import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_rag_pipeline():
    """测试完整的 RAG 管道"""
    print("=" * 60)
    print("RAG 子系统测试")
    print("=" * 60)
    
    # 导入 RAG 组件
    from src.rag import (
        DocumentLoader,
        TextChunker,
        ChunkStrategy,
        RAGPipeline,
        get_rag_pipeline,
    )
    from src.rag.embedder import MockEmbedder
    from src.rag.store import FAISSStore
    
    # 1. 测试文档加载
    print("\n[1] 测试文档加载")
    print("-" * 40)
    
    loader = DocumentLoader()
    docs_dir = project_root / "data" / "documents"
    
    if docs_dir.exists():
        documents = loader.load_directory(docs_dir)
        print(f"从 {docs_dir} 加载了 {len(documents)} 个文档:")
        for doc in documents:
            print(f"  - {doc.title} ({len(doc)} 字符)")
    else:
        print(f"文档目录不存在: {docs_dir}")
        # 创建测试文档
        test_doc = loader.load_text(
            content="""
            # 测试文档
            
            这是一个测试文档，用于验证 RAG 系统的功能。
            
            ## 关于 AI Agent
            
            AI Agent 是能够自主执行任务的智能系统。
            它包含规划器、执行器、记忆系统等核心组件。
            
            ## 关于 RAG
            
            RAG 是检索增强生成技术，可以让 AI 基于外部知识回答问题。
            """,
            source="test_doc",
            title="测试文档"
        )
        documents = [test_doc]
        print(f"创建了测试文档: {test_doc.title}")
    
    # 2. 测试文本切分
    print("\n[2] 测试文本切分")
    print("-" * 40)
    
    chunker = TextChunker(
        chunk_size=300,
        overlap=30,
        strategy=ChunkStrategy.MARKDOWN
    )
    
    all_chunks = []
    for doc in documents:
        chunks = chunker.chunk_document(doc)
        all_chunks.extend(chunks)
        print(f"  {doc.title}: {len(chunks)} 个块")
    
    print(f"\n总共 {len(all_chunks)} 个文本块")
    
    if all_chunks:
        print(f"\n示例块 (第1个):")
        print(f"  ID: {all_chunks[0].id}")
        print(f"  长度: {len(all_chunks[0])} 字符")
        print(f"  内容预览: {all_chunks[0].content[:100]}...")
    
    # 3. 测试向量化
    print("\n[3] 测试向量化")
    print("-" * 40)
    
    embedder = MockEmbedder(dimension=384)
    print(f"使用 MockEmbedder, 维度: {embedder.dimension}")
    
    # 向量化所有块
    embedded_chunks = await embedder.embed_chunks(all_chunks)
    
    embedded_count = sum(1 for c in embedded_chunks if c.has_embedding)
    print(f"成功向量化 {embedded_count}/{len(embedded_chunks)} 个块")
    
    if embedded_chunks and embedded_chunks[0].embedding:
        print(f"向量维度: {len(embedded_chunks[0].embedding)}")
        print(f"向量前5个值: {embedded_chunks[0].embedding[:5]}")
    
    # 4. 测试向量存储
    print("\n[4] 测试 FAISS 存储")
    print("-" * 40)
    
    store = FAISSStore(dimension=embedder.dimension)
    store.add(embedded_chunks)
    
    print(f"存储统计: {store.get_stats()}")
    
    # 5. 测试检索
    print("\n[5] 测试向量检索")
    print("-" * 40)
    
    test_queries = [
        "什么是 AI Agent?",
        "RAG 是如何工作的?",
        "MCP 协议的作用是什么?",
    ]
    
    for query in test_queries:
        print(f"\n查询: '{query}'")
        
        # 向量化查询
        query_embedding = await embedder.embed_text(query)
        
        # 检索
        results = store.search(query_embedding, top_k=3)
        
        print(f"找到 {len(results)} 个结果:")
        for r in results:
            print(f"  [{r.score:.4f}] {r.chunk.metadata.get('title', 'Unknown')}")
            print(f"           {r.chunk.content[:60]}...")
    
    # 6. 测试完整 RAG Pipeline
    print("\n[6] 测试完整 RAG Pipeline")
    print("-" * 40)
    
    rag = RAGPipeline(
        embedder=MockEmbedder(dimension=384),
        chunk_size=300,
        chunk_overlap=30
    )
    
    # 加载文档
    if docs_dir.exists():
        count = await rag.load_documents(docs_dir)
        print(f"Pipeline 加载了 {count} 个文档")
    else:
        await rag.add_document(
            content="AI Agent 是能够自主执行任务的智能系统。",
            title="AI Agent 简介"
        )
        print("Pipeline 添加了测试文档")
    
    # 检索
    query = "Agent 有哪些核心组件?"
    results = await rag.retrieve(query, top_k=3)
    
    print(f"\n查询: '{query}'")
    print(f"检索到 {len(results)} 个结果")
    
    # 获取上下文
    context = rag.get_context_for_prompt(results)
    print(f"\n生成的上下文 ({len(context)} 字符):")
    print("-" * 40)
    print(context[:500] + "..." if len(context) > 500 else context)
    
    # 7. 构建增强 Prompt
    print("\n[7] 构建增强 Prompt")
    print("-" * 40)
    
    augmented_prompt = rag.build_augmented_prompt(query, results)
    print(f"增强 Prompt ({len(augmented_prompt)} 字符):")
    print("-" * 40)
    print(augmented_prompt[:800] + "..." if len(augmented_prompt) > 800 else augmented_prompt)
    
    # 8. 测试保存和加载
    print("\n[8] 测试索引持久化")
    print("-" * 40)
    
    index_path = project_root / "data" / "rag_index"
    
    # 保存
    rag.save(str(index_path))
    print(f"索引已保存到: {index_path}")
    
    # 创建新 Pipeline 并加载
    rag2 = RAGPipeline(embedder=MockEmbedder(dimension=384))
    rag2.load(str(index_path))
    print(f"索引已加载, 统计: {rag2.get_stats()}")
    
    # 验证加载后的检索
    results2 = await rag2.retrieve("什么是 RAG?", top_k=2)
    print(f"加载后检索测试: 找到 {len(results2)} 个结果")
    
    print("\n" + "=" * 60)
    print("✅ RAG 子系统测试完成!")
    print("=" * 60)


async def test_agent_with_rag():
    """测试 Agent 如何调用 RAG Skill"""
    print("\n" + "=" * 60)
    print("Agent 调用 RAG Skill 示例")
    print("=" * 60)
    
    from src.rag import RAGPipeline
    from src.rag.embedder import MockEmbedder
    from src.mcp.tools import RAGRetrieverTool
    
    # 1. 初始化 RAG Pipeline
    docs_dir = Path(__file__).parent.parent / "data" / "documents"
    
    rag = RAGPipeline(embedder=MockEmbedder(dimension=384))
    
    if docs_dir.exists():
        await rag.load_documents(docs_dir)
    else:
        await rag.add_document(
            content="AI Agent 包含规划器、执行器、记忆系统等组件。",
            title="Agent 组件"
        )
    
    # 2. 创建 RAG 工具并连接 Pipeline
    rag_tool = RAGRetrieverTool()
    rag_tool.set_rag_pipeline(rag)
    
    # 3. 模拟 Agent 调用工具
    print("\n模拟 Agent 调用 rag_retriever 工具:")
    print("-" * 40)
    
    result = await rag_tool.execute(
        query="AI Agent 有哪些核心组件?",
        top_k=3
    )
    
    if result["success"]:
        print(f"查询: {result['data']['query']}")
        print(f"来源: {result['data'].get('source', 'unknown')}")
        print(f"结果数: {result['data']['total']}")
        print("\n检索到的文档:")
        for doc in result["data"]["documents"][:3]:
            print(f"  - [{doc['score']:.3f}] {doc.get('title', 'N/A')}")
            print(f"    {doc['content'][:80]}...")
    
    # 4. 展示如何将结果注入到 Agent Prompt
    print("\n将检索结果注入到 Agent Prompt:")
    print("-" * 40)
    
    # 格式化上下文
    documents = result["data"]["documents"]
    context_parts = []
    for doc in documents[:3]:
        context_parts.append(f"[{doc.get('title', '未知来源')}]\n{doc['content']}")
    
    context = "\n\n---\n\n".join(context_parts)
    
    agent_prompt = f"""你是一个智能助手。请基于以下参考资料回答用户问题。

## 参考资料

{context}

## 用户问题

AI Agent 有哪些核心组件?

## 要求
1. 优先使用参考资料中的信息
2. 如果资料不足，可以补充但需说明
3. 回答要简洁清晰"""
    
    print(agent_prompt[:1000] + "..." if len(agent_prompt) > 1000 else agent_prompt)
    
    print("\n" + "=" * 60)
    print("✅ Agent + RAG 集成示例完成!")
    print("=" * 60)


if __name__ == "__main__":
    print("开始 RAG 测试...\n")
    
    # 运行测试
    asyncio.run(test_rag_pipeline())
    asyncio.run(test_agent_with_rag())
