import time
from datetime import datetime
import logging
import threading

logging.basicConfig(level=logging.INFO)

class Message:
    """用于封装每一条对话消息"""
    def __init__(self, content, role=None, agent_id=None, agent_name=None, model=None, vendor=None, timestamp=None):
        self.role = role
        self.content = content
        self.agent_id = agent_id  # 对话来源智能体的 ID
        self.agent_name = agent_name  # 对话来源智能体的名称
        self.model = model  # 使用的模型
        self.vendor = vendor  # 使用的供应商
        self.timestamp = timestamp or datetime.now(datetime.timezone.utc).isoformat()  # 使用 UTC 格式时间

    def __repr__(self):
        return f"{self.role}: {self.content[:50]}... (Agent: {self.agent_name} ID: {self.agent_id}, Model: {self.model}, Vendor: {self.vendor}, Timestamp: {self.timestamp})"

class MemCore:
    """管理 AI 对话历史，支持默认和自定义角色"""
    
    _DEFAULT_ROLES = {"system", "user", "assistant"}

    def __init__(self, system_message=None, max_history_size=1000):
        """初始化对话历史，可选 system_message"""
        self._lock = threading.Lock()
        self.messages = []
        self.max_history_size = max_history_size
        self._roles = set(self._DEFAULT_ROLES)  # 允许的角色集合
        if system_message:
            self._add_message("system", system_message, None, None, None, None)

    def _add_message(self, role, content, agent_id=None, agent_name=None, model=None, vendor=None, timestamp=None):
        """内部方法：添加消息"""
        
        message = Message(role, content, agent_id, agent_name, model, vendor, timestamp)
        
        self.add_message(message)

    def add_message(self, message: Message):
        """内部方法：添加消息"""
        if message.role not in self._roles:
            raise ValueError(f"Invalid role: {message.role}. Allowed roles: {self._roles}")
        
        with self._lock:
            if len(self.messages) >= self.max_history_size:
                self.messages.pop(0)
            logging.info(f"Adding message: {message}")
            self.messages.append(message)

    def add_user_message(self, content, agent_id=None, agent_name=None, model=None, vendor=None, timestamp=None):
        """添加用户消息"""
        self._add_message("user", content, agent_id, agent_name, model, vendor, timestamp)

    def add_assistant_message(self, content, agent_id=None, agent_name=None, model=None, vendor=None, timestamp=None):
        """添加 AI 回复"""
        self._add_message("assistant", content, agent_id, agent_name, model, vendor, timestamp)

    def add_custom_message(self, role, content, agent_id=None, agent_name=None, model=None, vendor=None, timestamp=None):
        """添加自定义角色的消息"""
        if role not in self._roles:
            raise ValueError(f"Role '{role}' is not registered. Use `register_role()` first.")
        self._add_message(role, content, agent_id, agent_name, model, vendor, timestamp)

    def register_role(self, role):
        """注册新角色"""
        if role in self._DEFAULT_ROLES:
            raise ValueError(f"Role '{role}' is already a default role and cannot be redefined.")
        self._roles.add(role)

    def get_last_message(self):
        """获取当前对话历史"""
        return self.messages[-1] if self.messages else None

    def get_messages(self):
        """获取当前对话历史"""
        return self.messages
    
    def get_messages_for_api(self, max_messages=None):
        """
        获取一个格式化后的消息列表，适用于向 AI API 接口发送的消息格式
        返回的是一个列表，其中每个消息包含角色、内容以及其他必要的字段。
        如果设置了 max_messages，则返回最多 max_messages 条消息，并确保 system 消息被包含。
        """
        # 先提取所有消息，按照时间排序
        api_messages = []
        system_message = None  # 如果有 system 消息，我们会特别处理它

        for message in self.messages:
            # 如果消息的 role 不是 "system" 和 "assistant"，则设置为 "user"
            role = message.role if message.role in {"system", "assistant"} else "user"
            
            # 保存 system 消息，用于后续确保其被包含
            if role == "system" and not system_message:
                system_message = message
            
            # 确保没有重复插入 system 消息
            if role != "system":
                api_message = {
                    "role": role,
                    "content": message.content
                }
                api_messages.append(api_message)
        
        # 限制最大消息条数，从后往前裁剪
        if max_messages:
            # 如果最大条数大于当前消息数，则直接返回
            if len(api_messages) > max_messages:
                api_messages = api_messages[-max_messages:]

        # 确保 system 消息被包含（如果存在的话），并且只插入一次
        if system_message and not any(msg['role'] == 'system' for msg in api_messages):
            api_messages.insert(0, {
                "role": "system",
                "content": system_message.content
            })

        return api_messages

    def reset(self, system_message=None):
        """重置对话历史"""
        self.messages = []
        if system_message:
            self._add_message("system", system_message, None, None, None, None)