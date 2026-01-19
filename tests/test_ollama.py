"""
Ollama 连接测试

测试本地 Ollama 服务是否正常工作
"""
import asyncio
import sys
from pathlib import Path

# 确保路径正确
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


async def test_ollama():
    """测试 Ollama 服务"""
    print("=" * 60)
    print("🧪 Testing Ollama Connection")
    print("=" * 60)
    
    # 1. 测试配置
    print("\n📋 Test 1: Configuration")
    from src.core.config import get_settings
    settings = get_settings()
    print(f"  ✅ LLM Provider: {settings.llm_provider}")
    print(f"  ✅ Ollama Base URL: {settings.ollama_base_url}")
    print(f"  ✅ Ollama Model: {settings.ollama_model}")
    print(f"  ✅ Embedding Provider: {settings.rag_embedder_type}")
    print(f"  ✅ Embedding Model: {settings.ollama_embedding_model}")
    print(f"  ✅ Embedding Dimension: {settings.embedding_dimension}")
    
    # 2. 测试 Ollama 客户端
    print("\n📋 Test 2: Ollama LLM Client")
    from src.core.ollama import get_ollama_client
    
    client = get_ollama_client()
    
    # 检查模型列表
    try:
        models = await client.list_models()
        print(f"  ✅ Available models: {len(models)}")
        for model in models[:5]:
            print(f"     - {model}")
        if len(models) > 5:
            print(f"     ... and {len(models) - 5} more")
    except Exception as e:
        print(f"  ❌ Failed to list models: {e}")
        print("  ⚠️ 请确保 Ollama 服务正在运行: ollama serve")
        return False
    
    # 检查目标模型
    model_available = await client.check_model(settings.ollama_model)
    if model_available:
        print(f"  ✅ Model '{settings.ollama_model}' is available")
    else:
        print(f"  ⚠️ Model '{settings.ollama_model}' not found")
        print(f"     Run: ollama pull {settings.ollama_model}")
    
    # 3. 测试 LLM 对话
    print("\n📋 Test 3: LLM Chat")
    try:
        response = await client.chat(
            messages=[
                {"role": "user", "content": "你好，请用一句话介绍你自己。"}
            ],
            temperature=0.7,
            max_tokens=100
        )
        
        if response["success"]:
            print(f"  ✅ LLM Response: {response['content'][:100]}...")
        else:
            print(f"  ❌ LLM Error: {response.get('error')}")
    except Exception as e:
        print(f"  ❌ LLM Chat failed: {e}")
    
    # 4. 测试 Embedding
    print("\n📋 Test 4: Ollama Embedding")
    from src.rag.embedder import get_embedder, set_embedder
    
    # 重置 embedder
    set_embedder(None)
    
    try:
        embedder = get_embedder("ollama")
        
        # 测试单个文本
        text = "这是一个测试文本，用于验证 Ollama Embedding 功能。"
        embedding = await embedder.embed_text(text)
        
        print(f"  ✅ Embedding dimension: {len(embedding)}")
        print(f"  ✅ First 5 values: {embedding[:5]}")
        
        # 测试批量文本
        texts = [
            "什么是 Agent？",
            "MCP 协议是什么？",
            "RAG 如何工作？"
        ]
        embeddings = await embedder.embed_texts(texts)
        print(f"  ✅ Batch embedding: {len(embeddings)} texts embedded")
        
    except Exception as e:
        print(f"  ❌ Embedding failed: {e}")
        print("  ⚠️ 请确保已拉取 embedding 模型: ollama pull qwen3-embedding:latest")
    
    # 5. 测试 RAG Pipeline
    print("\n📋 Test 5: RAG Pipeline with Ollama")
    try:
        from src.rag import get_rag_pipeline
        from src.rag.embedder import OllamaEmbedder
        
        # 重置 embedder
        set_embedder(None)
        
        rag = get_rag_pipeline()
        
        # 加载测试文档
        docs_dir = Path(settings.documents_dir)
        if docs_dir.exists():
            await rag.load_documents(docs_dir)
            print(f"  ✅ Loaded documents: {rag.stats.get('total_chunks', 0)} chunks")
            
            # 测试检索
            results = await rag.retrieve("什么是 Agent", top_k=2)
            print(f"  ✅ Retrieved {len(results)} results")
            
            for i, r in enumerate(results[:2], 1):
                print(f"     {i}. Score: {r.score:.4f} - {r.chunk.content[:50]}...")
        else:
            print(f"  ⚠️ Documents directory not found: {docs_dir}")
            
    except Exception as e:
        print(f"  ❌ RAG Pipeline failed: {e}")
        import traceback
        traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Ollama tests completed!")
    print("=" * 60)
    
    print("\n📝 如果遇到问题，请检查：")
    print("  1. Ollama 服务是否运行: ollama serve")
    print("  2. 模型是否已下载:")
    print(f"     ollama pull {settings.ollama_model}")
    print(f"     ollama pull {settings.ollama_embedding_model}")
    
    return True


if __name__ == "__main__":
    asyncio.run(test_ollama())
