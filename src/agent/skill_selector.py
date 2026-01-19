"""
技能选择器
根据任务步骤选择合适的技能
"""

from typing import TYPE_CHECKING, Any, Dict, List, Optional

from src.core.exceptions import SkillNotFoundException
from src.core.logging import get_logger

if TYPE_CHECKING:
    from src.skills.base import BaseSkill

logger = get_logger("agent.skill_selector")


class SkillSelector:
    """
    技能选择器

    职责：
    - 管理可用技能的注册
    - 根据步骤需求选择合适的技能
    - 验证技能可用性
    """

    def __init__(self):
        """初始化技能选择器"""
        self._skills: Dict[str, "BaseSkill"] = {}
        self._skill_metadata: Dict[str, Dict[str, Any]] = {}
        logger.debug("SkillSelector initialized")

    def register_skill(
        self, name: str, skill: "BaseSkill", metadata: Dict[str, Any] = None
    ) -> None:
        """
        注册技能

        Args:
            name: 技能名称
            skill: 技能实例
            metadata: 技能元数据
        """
        self._skills[name] = skill
        self._skill_metadata[name] = metadata or {
            "description": getattr(skill, "description", ""),
            "tools": getattr(skill, "required_tools", []),
        }
        logger.info(f"Registered skill: {name}")

    def unregister_skill(self, name: str) -> bool:
        """
        注销技能

        Args:
            name: 技能名称

        Returns:
            是否成功注销
        """
        if name in self._skills:
            del self._skills[name]
            del self._skill_metadata[name]
            logger.info(f"Unregistered skill: {name}")
            return True
        return False

    def get_skill(self, name: str) -> Optional["BaseSkill"]:
        """
        获取技能实例

        Args:
            name: 技能名称

        Returns:
            技能实例，不存在则返回 None
        """
        return self._skills.get(name)

    def select_skill(self, skill_name: str, fallback: bool = True) -> "BaseSkill":
        """
        选择技能

        Args:
            skill_name: 请求的技能名称
            fallback: 是否使用后备技能

        Returns:
            技能实例

        Raises:
            SkillNotFoundException: 技能未找到且不使用后备
        """
        # 直接匹配
        if skill_name in self._skills:
            logger.debug(f"Selected skill: {skill_name}")
            return self._skills[skill_name]

        # 尝试模糊匹配
        skill_name_lower = skill_name.lower()
        for name, skill in self._skills.items():
            if skill_name_lower in name.lower() or name.lower() in skill_name_lower:
                logger.debug(f"Fuzzy matched skill: {name} for request: {skill_name}")
                return skill

        # 后备到 direct_answer
        if fallback and "direct_answer" in self._skills:
            logger.warning(
                f"Skill '{skill_name}' not found, falling back to direct_answer"
            )
            return self._skills["direct_answer"]

        raise SkillNotFoundException(
            message=f"技能 '{skill_name}' 未找到",
            details={"available_skills": list(self._skills.keys())},
        )

    def get_all_skills(self) -> Dict[str, "BaseSkill"]:
        """获取所有注册的技能"""
        return self._skills.copy()

    def get_skills_for_planner(self) -> Dict[str, Dict[str, Any]]:
        """
        获取供 Planner 使用的技能描述

        Returns:
            技能名称到描述的映射
        """
        return self._skill_metadata.copy()

    def list_skills(self) -> List[Dict[str, Any]]:
        """
        列出所有技能信息

        Returns:
            技能信息列表
        """
        return [
            {
                "name": name,
                "description": meta.get("description", ""),
                "tools": meta.get("tools", []),
            }
            for name, meta in self._skill_metadata.items()
        ]

    def validate_skill_availability(self, skill_names: List[str]) -> Dict[str, bool]:
        """
        验证技能可用性

        Args:
            skill_names: 技能名称列表

        Returns:
            技能名称到可用性的映射
        """
        return {name: name in self._skills for name in skill_names}

    def __contains__(self, name: str) -> bool:
        """检查技能是否已注册"""
        return name in self._skills

    def __len__(self) -> int:
        """返回注册的技能数量"""
        return len(self._skills)
