"""
基礎 Agent 類別
所有專家 Agent 的父類別
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Any
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentMessage:
    """Agent 之間的訊息格式"""
    sender: str
    receiver: str
    message_type: str  # query, response, suggestion, alert
    content: Dict[str, Any]
    timestamp: str
    priority: int = 1  # 1-5, 5 最高


class BaseAgent(ABC):
    """基礎 Agent 類別"""

    def __init__(self, agent_name: str, role: str):
        """
        初始化 Agent

        Args:
            agent_name: Agent 名稱
            role: Agent 角色
        """
        self.agent_name = agent_name
        self.role = role
        self.message_history = []
        self.knowledge_base = {}

    @abstractmethod
    def analyze(self, data: Dict) -> Dict:
        """
        分析數據

        Args:
            data: 輸入數據

        Returns:
            分析結果
        """
        pass

    @abstractmethod
    def make_decision(self, analysis_result: Dict) -> Dict:
        """
        做出決策

        Args:
            analysis_result: 分析結果

        Returns:
            決策建議
        """
        pass

    def send_message(self, receiver: str, message_type: str, content: Dict, priority: int = 1) -> AgentMessage:
        """發送訊息給其他 Agent"""
        message = AgentMessage(
            sender=self.agent_name,
            receiver=receiver,
            message_type=message_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            priority=priority
        )
        self.message_history.append(message)
        return message

    def receive_message(self, message: AgentMessage) -> Dict:
        """接收訊息並處理"""
        self.message_history.append(message)
        return self._process_message(message)

    @abstractmethod
    def _process_message(self, message: AgentMessage) -> Dict:
        """處理接收到的訊息"""
        pass

    def get_message_history(self, last_n: int = 10) -> List[AgentMessage]:
        """取得訊息歷史"""
        return self.message_history[-last_n:]
