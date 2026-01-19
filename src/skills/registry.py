"""
技能注册中心
管理所有技能的注册、发现和加载
"""

import importlib
from pathlib import Path
from typing import Any, Dict, List, Optional, Type

import yaml

from src.core.logging import get_logger

from .base import BaseSkill

logger = get_logger("skills.registry")


class SkillRegistry:
    """
    技能注册中心

    职责：
    - 自动发现和加载技能
    - 管理技能生命周期
    - 提供技能查询接口
    """

    def __init__(self):
        """初始化注册中心"""
        self._skills: Dict[str, BaseSkill] = {}
        self._skill_configs: Dict[str, Dict[str, Any]] = {}
        logger.debug("SkillRegistry initialized")

    def register(self, skill: BaseSkill, config: Dict[str, Any] = None) -> None:
        """
        注册技能

        Args:
            skill: 技能实例
            config: 技能配置
        """
        name = skill.name
        self._skills[name] = skill
        self._skill_configs[name] = config or skill.get_metadata()
        logger.info(f"Skill registered: {name}")

    def unregister(self, name: str) -> bool:
        """注销技能"""
        if name in self._skills:
            del self._skills[name]
            del self._skill_configs[name]
            logger.info(f"Skill unregistered: {name}")
            return True
        return False

    def get(self, name: str) -> Optional[BaseSkill]:
        """获取技能实例"""
        return self._skills.get(name)

    def get_config(self, name: str) -> Optional[Dict[str, Any]]:
        """获取技能配置"""
        return self._skill_configs.get(name)

    def list_skills(self) -> List[Dict[str, Any]]:
        """列出所有技能"""
        return [
            {
                "name": name,
                "description": skill.description,
                "required_tools": skill.required_tools,
            }
            for name, skill in self._skills.items()
        ]

    def get_skills_for_planner(self) -> Dict[str, Dict[str, Any]]:
        """获取供 Planner 使用的技能描述"""
        return {
            name: {"description": skill.description, "tools": skill.required_tools}
            for name, skill in self._skills.items()
        }

    def get_all(self) -> Dict[str, BaseSkill]:
        """获取所有技能"""
        return self._skills.copy()

    def has_skill(self, name: str) -> bool:
        """检查技能是否存在"""
        return name in self._skills

    def __contains__(self, name: str) -> bool:
        return self.has_skill(name)

    def __len__(self) -> int:
        return len(self._skills)


# 全局技能注册中心实例
skill_registry = SkillRegistry()
