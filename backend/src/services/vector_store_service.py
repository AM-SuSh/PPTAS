"""
向量存储服务 - 用于存储和检索 PPT/PDF 切片
支持基于语义的相关性检索
"""

import os
import uuid
from typing import List, Dict, Any, Optional
from datetime import datetime

from langchain_core.documents import Document
from langchain_openai import OpenAIEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter

# 优先使用新的 langchain-chroma，如果不存在则回退到旧版本
try:
    from langchain_chroma import Chroma
except ImportError:
    try:
        from langchain_community.vectorstores import Chroma
    except ImportError:
        raise ImportError("需要安装 langchain-chroma 或 langchain-community")

from src.agents.base import LLMConfig


class VectorStoreService:
    """向量存储服务 - 存储 PPT/PDF 切片并支持语义检索"""
    
    def __init__(self, llm_config: LLMConfig, vector_db_path: str = "./ppt_vector_db"):
        """
        初始化向量存储服务
        
        Args:
            llm_config: LLM 配置（用于创建 embeddings）
            vector_db_path: 向量数据库存储路径
        """
        self.llm_config = llm_config
        self.vector_db_path = vector_db_path
        # 初始化 embeddings
        # 注意：某些 API 可能不支持 model 参数，先尝试不指定
        try:
            self.embeddings = OpenAIEmbeddings(
                api_key=llm_config.api_key,
                base_url=llm_config.base_url,
                model="BAAI/bge-large-zh-v1.5"
            )
        except Exception:
            # 如果指定模型失败，尝试不指定模型（使用默认）
            self.embeddings = OpenAIEmbeddings(
                api_key=llm_config.api_key,
                base_url=llm_config.base_url
            )
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=400,
            chunk_overlap=50,
            length_function=len,
        )
        self.vectorstore: Optional[Chroma] = None
        try:
            self._initialize_vectorstore()
        except Exception as e:
            print(f"❌ 向量数据库服务初始化失败: {e}")
            print(f"   提示: 向量存储功能将不可用，但其他功能正常")
            # 不抛出异常，允许服务继续运行（存储功能会失败，但不影响其他功能）
            self.vectorstore = None
    
    def _initialize_vectorstore(self):
        """初始化向量数据库"""
        max_retries = 3
        last_error = None
        
        for attempt in range(max_retries):
            try:
                # 确保目录存在
                os.makedirs(self.vector_db_path, exist_ok=True)
                
                # 尝试加载现有的向量数据库或创建新的
                if os.path.exists(self.vector_db_path) and os.listdir(self.vector_db_path):
                    # 目录存在且不为空，尝试加载
                    try:
                        self.vectorstore = Chroma(
                            persist_directory=self.vector_db_path,
                            embedding_function=self.embeddings
                        )
                        # 验证初始化是否成功
                        if self.vectorstore is not None:
                            print(f"✅ 向量数据库初始化成功 (路径: {self.vector_db_path})")
                            return
                    except Exception as load_error:
                        print(f"⚠️  加载现有数据库失败，尝试创建新的: {load_error}")
                        # 如果加载失败，删除旧目录重新创建
                        import shutil
                        try:
                            shutil.rmtree(self.vector_db_path)
                            os.makedirs(self.vector_db_path, exist_ok=True)
                        except:
                            pass
                
                # 创建新的向量数据库
                self.vectorstore = Chroma(
                    persist_directory=self.vector_db_path,
                    embedding_function=self.embeddings
                )
                
                # 验证初始化是否成功
                if self.vectorstore is not None:
                    print(f"✅ 向量数据库初始化成功 (路径: {self.vector_db_path})")
                    return
                else:
                    raise Exception("向量数据库对象创建失败")
                    
            except Exception as e:
                last_error = e
                print(f"⚠️  初始化向量数据库失败 (尝试 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    import time
                    time.sleep(0.5)  # 等待后重试
                else:
                    # 最后一次尝试失败，抛出异常
                    print(f"❌ 向量数据库初始化最终失败: {e}")
                    raise Exception(f"向量数据库初始化失败: {e}") from last_error
        
        # 如果所有重试都失败
        raise Exception(f"向量数据库初始化失败，已重试 {max_retries} 次: {last_error}")
    
    def _create_document_id(self, file_name: str, page_num: int, chunk_index: int = 0) -> str:
        """创建文档 ID"""
        return f"{file_name}_{page_num}_{chunk_index}_{uuid.uuid4().hex[:8]}"
    
    def _slide_to_text(self, slide: Dict[str, Any]) -> str:
        """将幻灯片数据转换为文本用于向量化"""
        text_parts = []
        
        # 添加标题
        if slide.get("title"):
            text_parts.append(f"标题: {slide['title']}")
        
        # 添加内容点
        if slide.get("raw_points"):
            for point in slide["raw_points"]:
                if isinstance(point, dict):
                    text_parts.append(point.get("text", ""))
                elif isinstance(point, str):
                    text_parts.append(point)
        
        # 添加类型信息
        if slide.get("type"):
            text_parts.append(f"类型: {slide['type']}")
        
        return "\n".join(text_parts)
    
    def store_document_slides(
        self,
        file_name: str,
        file_type: str,  # "pdf" 或 "pptx"
        slides: List[Dict[str, Any]],
        metadata: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        存储文档的所有幻灯片到向量数据库
        
        Args:
            file_name: 文件名
            file_type: 文件类型 ("pdf" 或 "pptx")
            slides: 幻灯片列表（来自 DocumentParserService）
            metadata: 额外的元数据
        
        Returns:
            存储结果统计
        """
        if not self.vectorstore:
            error_msg = (
                "向量数据库未初始化。可能的原因：\n"
                "1. API Key 配置错误或无效\n"
                "2. Embedding API 调用失败\n"
                "3. 数据库目录权限问题\n"
                "4. 依赖包未正确安装（需要 langchain-chroma 或 langchain-community）\n"
                "请查看上面的错误日志获取详细信息"
            )
            print(f"❌ {error_msg}")
            raise Exception("向量数据库未初始化")
        
        documents = []
        metadatas = []
        ids = []
        
        total_chunks = 0
        
        for slide in slides:
            # 将幻灯片转换为文本
            slide_text = self._slide_to_text(slide)
            
            if not slide_text.strip():
                continue
            
            # 如果文本较长，进行分块
            chunks = self.text_splitter.split_text(slide_text)
            
            for chunk_index, chunk in enumerate(chunks):
                if not chunk.strip():
                    continue
                
                # 创建文档
                doc = Document(
                    page_content=chunk,
                    metadata={
                        "file_name": file_name,
                        "file_type": file_type,
                        "page_num": slide.get("page_num", 0),
                        "slide_title": slide.get("title", ""),
                        "slide_type": slide.get("type", "content"),
                        "chunk_index": chunk_index,
                        "total_chunks": len(chunks),
                        "stored_at": datetime.now().isoformat(),
                        **(metadata or {})
                    }
                )
                
                doc_id = self._create_document_id(file_name, slide.get("page_num", 0), chunk_index)
                
                documents.append(doc)
                metadatas.append(doc.metadata)
                ids.append(doc_id)
                total_chunks += 1

        if documents:
            # --- 修改部分：分批次写入，应对 API 限制 ---
            batch_size = 3  # 根据报错信息，这里设为 3（甚至可以设为 1 最稳妥）
            print(f"📦 正在分批存储向量，每批 {batch_size} 条，总计 {len(documents)} 条...")

            for i in range(0, len(documents), batch_size):
                batch_docs = documents[i: i + batch_size]
                batch_ids = ids[i: i + batch_size]
                try:
                    self.vectorstore.add_documents(
                        documents=batch_docs,
                        ids=batch_ids
                    )
                    # print(f"  ✅ 已完成 {min(i + batch_size, len(documents))}/{len(documents)}")
                except Exception as batch_error:
                    print(f"  ❌ 批次 {i // batch_size + 1} 存储失败: {batch_error}")
                    # 如果某一批失败，可以选择继续或跳过

            # 部分旧版本 Chroma 需要手动 persist，新版本已自动持久化
            try:
                self.vectorstore.persist()
            except:
                pass
        
        return {
            "file_name": file_name,
            "file_type": file_type,
            "total_slides": len(slides),
            "total_chunks": total_chunks,
            "stored_at": datetime.now().isoformat()
        }
    
    def search_similar_slides(
        self,
        query: str,
        top_k: int = 5,
        file_name: Optional[str] = None,
        file_type: Optional[str] = None,
        min_score: float = 0.0
    ) -> List[Dict[str, Any]]:
        """
        基于语义搜索相似的幻灯片切片
        
        Args:
            query: 查询文本
            top_k: 返回前 k 个结果
            file_name: 可选，限制搜索特定文件
            file_type: 可选，限制搜索特定文件类型
            min_score: 最小相似度分数（0-1）
        
        Returns:
            搜索结果列表，每个结果包含：
            - content: 文本内容
            - metadata: 元数据（文件、页码等）
            - score: 相似度分数
        """
        if not self.vectorstore:
            return []
        
        # 构建过滤条件
        where = {}
        if file_name:
            where["file_name"] = file_name
        if file_type:
            where["file_type"] = file_type
        
        try:
            # 使用相似度搜索
            if where:
                results = self.vectorstore.similarity_search_with_score(
                    query,
                    k=top_k,
                    filter=where
                )
            else:
                results = self.vectorstore.similarity_search_with_score(
                    query,
                    k=top_k
                )
            
            # 格式化结果
            formatted_results = []
            for doc, score in results:
                # 相似度分数转换为 0-1 范围（ChromaDB 使用距离，需要转换）
                similarity_score = 1 / (1 + score) if score > 0 else 1.0
                
                if similarity_score >= min_score:
                    formatted_results.append({
                        "content": doc.page_content,
                        "metadata": doc.metadata,
                        "score": similarity_score,
                        "distance": score
                    })
            
            return formatted_results
        except Exception as e:
            print(f"⚠️  搜索失败: {e}")
            return []
    
    def search_by_file(self, file_name: str) -> List[Dict[str, Any]]:
        """
        获取特定文件的所有切片
        
        Args:
            file_name: 文件名
        
        Returns:
            该文件的所有切片
        """
        if not self.vectorstore:
            return []
        
        try:
            # 使用元数据过滤
            results = self.vectorstore.get(
                where={"file_name": file_name}
            )
            
            formatted_results = []
            if results and "documents" in results:
                for i, doc_content in enumerate(results["documents"]):
                    metadata = results["metadatas"][i] if "metadatas" in results else {}
                    formatted_results.append({
                        "content": doc_content,
                        "metadata": metadata
                    })
            
            return formatted_results
        except Exception as e:
            print(f"⚠️  按文件搜索失败: {e}")
            return []
    
    def delete_file_slides(self, file_name: str) -> bool:
        """
        删除特定文件的所有切片
        
        Args:
            file_name: 文件名
        
        Returns:
            是否成功删除
        """
        if not self.vectorstore:
            return False
        
        try:
            # 获取该文件的所有 ID
            results = self.vectorstore.get(
                where={"file_name": file_name}
            )
            
            if results and "ids" in results:
                ids_to_delete = results["ids"]
                if ids_to_delete:
                    self.vectorstore.delete(ids=ids_to_delete)
                    self.vectorstore.persist()
                    return True
            
            return False
        except Exception as e:
            print(f"⚠️  删除文件切片失败: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """
        获取向量数据库统计信息
        
        Returns:
            统计信息
        """
        if not self.vectorstore:
            return {"total_documents": 0, "collections": []}
        
        try:
            # 获取所有文档
            all_results = self.vectorstore.get()
            
            total_docs = len(all_results.get("ids", [])) if all_results else 0
            
            # 统计文件类型
            file_types = {}
            file_names = set()
            
            if all_results and "metadatas" in all_results:
                for metadata in all_results["metadatas"]:
                    file_type = metadata.get("file_type", "unknown")
                    file_types[file_type] = file_types.get(file_type, 0) + 1
                    file_names.add(metadata.get("file_name", "unknown"))
            
            return {
                "total_documents": total_docs,
                "total_files": len(file_names),
                "file_types": file_types,
                "vector_db_path": self.vector_db_path
            }
        except Exception as e:
            print(f"⚠️  获取统计信息失败: {e}")
            return {"total_documents": 0, "error": str(e)}

