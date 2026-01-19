"""
长期记忆模块
存储跨会话的持久化信息
"""

from datetime import datetime
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field

from src.core.logging import get_logger

logger = get_logger("memory.long_term")


class MemoryEntry(BaseModel):
    """记忆条目"""

    entry_id: str
    content: str
    category: str = "general"  # general, fact, preference, task_history
    importance: float = 0.5  # 0-1 重要性评分
    created_at: datetime = Field(default_factory=datetime.now)
    accessed_at: datetime = Field(default_factory=datetime.now)
    access_count: int = 0
    metadata: Dict[str, Any] = Field(default_factory=dict)


class LongTermMemory:
    """
    长期记忆
    - 存储用户偏好
    - 存储历史任务摘要
    - 存储重要事实

    注：当前使用内存存储，生产环境应替换为持久化存储
    """

    def __init__(self):
        """初始化长期记忆"""
        self._memories: Dict[str, MemoryEntry] = {}
        self._memory_index: Dict[str, List[str]] = {
            "general": [],
            "fact": [],
            "preference": [],
            "task_history": [],
        }
        logger.debug("LongTermMemory initialized")

    def store(
        self,
        content: str,
        category: str = "general",
        importance: float = 0.5,
        metadata: Dict[str, Any] = None,
    ) -> str:
        """
        存储记忆

        Args:
            content: 记忆内容
            category: 类别
            importance: 重要性评分
            metadata: 元数据

        Returns:
            记忆条目ID
        """
        entry_id = (
            f"mem_{datetime.now().strftime('%Y%m%d%H%M%S')}_{len(self._memories)}"
        )
        entry = MemoryEntry(
            entry_id=entry_id,
            content=content,
            category=category,
            importance=importance,
            metadata=metadata or {},
        )

        self._memories[entry_id] = entry
        if category in self._memory_index:
            self._memory_index[category].append(entry_id)
        else:
            self._memory_index[category] = [entry_id]

        logger.debug(f"Stored memory: {entry_id} in category '{category}'")
        return entry_id

    def retrieve(
        self,
        category: Optional[str] = None,
        limit: int = 10,
        min_importance: float = 0.0,
    ) -> List[MemoryEntry]:
        """
        检索记忆

        Args:
            category: 类别过滤
            limit: 返回数量限制
            min_importance: 最小重要性阈值

        Returns:
            记忆条目列表
        """
        if category:
            entry_ids = self._memory_index.get(category, [])
        else:
            entry_ids = list(self._memories.keys())

        # 获取并过滤
        entries = []
        for eid in entry_ids:
            entry = self._memories.get(eid)
            if entry and entry.importance >= min_importance:
                # 更新访问信息
                entry.accessed_at = datetime.now()
                entry.access_count += 1
                entries.append(entry)

        # 按重要性和访问时间排序
        entries.sort(key=lambda e: (e.importance, e.accessed_at), reverse=True)

        return entries[:limit]

    def get_by_id(self, entry_id: str) -> Optional[MemoryEntry]:
        """根据ID获取记忆"""
        return self._memories.get(entry_id)

    def update_importance(self, entry_id: str, importance: float) -> bool:
        """更新记忆重要性"""
        if entry_id in self._memories:
            self._memories[entry_id].importance = importance
            return True
        return False

    def delete(self, entry_id: str) -> bool:
        """删除记忆"""
        if entry_id in self._memories:
            entry = self._memories.pop(entry_id)
            if entry.category in self._memory_index:
                self._memory_index[entry.category].remove(entry_id)
            logger.debug(f"Deleted memory: {entry_id}")
            return True
        return False

    def store_task_summary(self, task_id: str, query: str, result: str) -> str:
        """
        存储任务历史摘要

        Args:
            task_id: 任务ID
            query: 用户查询
            result: 执行结果

        Returns:
            记忆条目ID
        """
        content = f"任务: {query}\n结果: {result[:500]}"
        return self.store(
            content=content,
            category="task_history",
            importance=0.6,
            metadata={"task_id": task_id},
        )

    def store_user_preference(self, preference: str, importance: float = 0.7) -> str:
        """存储用户偏好"""
        return self.store(
            content=preference, category="preference", importance=importance
        )

    def get_relevant_history(self, query: str, limit: int = 3) -> List[str]:
        """
        获取与查询相关的历史记录

        注：当前使用简单的关键词匹配，生产环境应使用向量检索

        Args:
            query: 查询内容
            limit: 返回数量

        Returns:
            相关历史内容列表
        """
        # 简单实现：返回最近的任务历史
        entries = self.retrieve(category="task_history", limit=limit)
        return [e.content for e in entries]

    def clear(self) -> None:
        """清空所有记忆"""
        self._memories.clear()
        for key in self._memory_index:
            self._memory_index[key] = []
        logger.debug("LongTermMemory cleared")

    def get_stats(self) -> Dict[str, Any]:
        """获取记忆统计信息"""
        return {
            "total_count": len(self._memories),
            "by_category": {cat: len(ids) for cat, ids in self._memory_index.items()},
        }
