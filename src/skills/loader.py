"""
技能加载器
自动发现、加载和初始化技能
"""
from typing import Dict, Any, List, Optional, TYPE_CHECKING
from pathlib import Path

from .base import BaseSkill
from .registry import SkillRegistry, skill_registry
from .direct_answer import DirectAnswerSkill
from .travel import TravelQuerySkill
from .weather import WeatherQuerySkill
from .knowledge import KnowledgeSearchSkill
from .summarize import SummarizeSkill
from src.core.logging import get_logger

if TYPE_CHECKING:
    from src.llm.base import BaseLLM
    from src.rag.retriever import RAGRetriever

logger = get_logger("skills.loader")


class SkillLoader:
    """
    技能加载器
    
    职责：
    - 自动发现可用技能
    - 初始化技能实例
    - 注册到技能注册中心
    """
    
    # 内置技能类映射
    BUILTIN_SKILLS = {
        "direct_answer": DirectAnswerSkill,
        "travel_query": TravelQuerySkill,
        "weather_query": WeatherQuerySkill,
        "knowledge_search": KnowledgeSearchSkill,
        "summarize": SummarizeSkill,
    }
    
    def __init__(
        self,
        registry: SkillRegistry = None,
        llm: "BaseLLM" = None,
        retriever: "RAGRetriever" = None
    ):
        """
        初始化加载器
        
        Args:
            registry: 技能注册中心
            llm: LLM 实例（供需要的技能使用）
            retriever: RAG 检索器（供知识检索技能使用）
        """
        self.registry = registry or skill_registry
        self.llm = llm
        self.retriever = retriever
        self._loaded_skills: Dict[str, BaseSkill] = {}
        logger.debug("SkillLoader initialized")
    
    def load_all(self) -> Dict[str, BaseSkill]:
        """
        加载所有内置技能
        
        Returns:
            已加载的技能字典
        """
        logger.info("Loading all built-in skills...")
        
        for skill_name, skill_class in self.BUILTIN_SKILLS.items():
            try:
                skill = self._create_skill_instance(skill_name, skill_class)
                self.registry.register(skill)
                self._loaded_skills[skill_name] = skill
                logger.debug(f"Loaded skill: {skill_name}")
            except Exception as e:
                logger.error(f"Failed to load skill {skill_name}: {e}")
        
        logger.info(f"Loaded {len(self._loaded_skills)} skills")
        return self._loaded_skills
    
    def load_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """
        加载单个技能
        
        Args:
            skill_name: 技能名称
            
        Returns:
            技能实例
        """
        if skill_name in self._loaded_skills:
            return self._loaded_skills[skill_name]
        
        skill_class = self.BUILTIN_SKILLS.get(skill_name)
        if not skill_class:
            logger.warning(f"Unknown skill: {skill_name}")
            return None
        
        try:
            skill = self._create_skill_instance(skill_name, skill_class)
            self.registry.register(skill)
            self._loaded_skills[skill_name] = skill
            return skill
        except Exception as e:
            logger.error(f"Failed to load skill {skill_name}: {e}")
            return None
    
    def _create_skill_instance(
        self,
        skill_name: str,
        skill_class: type
    ) -> BaseSkill:
        """
        创建技能实例
        
        根据技能类型传入不同的依赖
        """
        # 需要 LLM 的技能
        if skill_name in ("direct_answer", "summarize"):
            return skill_class(llm=self.llm)
        
        # 需要 RAG 检索器的技能
        if skill_name == "knowledge_search":
            skill = skill_class()
            if self.retriever:
                skill.set_retriever(self.retriever)
            return skill
        
        # 其他技能
        return skill_class()
    
    def unload_skill(self, skill_name: str) -> bool:
        """卸载技能"""
        if skill_name in self._loaded_skills:
            self.registry.unregister(skill_name)
            del self._loaded_skills[skill_name]
            logger.info(f"Unloaded skill: {skill_name}")
            return True
        return False
    
    def reload_skill(self, skill_name: str) -> Optional[BaseSkill]:
        """重新加载技能"""
        self.unload_skill(skill_name)
        return self.load_skill(skill_name)
    
    def get_loaded_skills(self) -> Dict[str, BaseSkill]:
        """获取已加载的技能"""
        return self._loaded_skills.copy()
    
    def list_available_skills(self) -> List[str]:
        """列出所有可用技能名称"""
        return list(self.BUILTIN_SKILLS.keys())
    
    def get_skills_summary(self) -> List[Dict[str, Any]]:
        """获取技能摘要信息"""
        return [
            {
                "name": name,
                "description": skill.description,
                "required_tools": skill.required_tools,
                "loaded": name in self._loaded_skills
            }
            for name, skill in self.BUILTIN_SKILLS.items()
            for skill in [skill()]  # 临时实例化获取描述
        ]


def load_default_skills(
    llm: "BaseLLM" = None,
    retriever: "RAGRetriever" = None
) -> SkillRegistry:
    """
    加载默认技能的便捷函数
    
    Args:
        llm: LLM 实例
        retriever: RAG 检索器
        
    Returns:
        已填充的技能注册中心
    """
    loader = SkillLoader(llm=llm, retriever=retriever)
    loader.load_all()
    return loader.registry
