class ChatHistory:
    """管理 AI 对话历史，支持默认和自定义角色"""

    _DEFAULT_ROLES = {"system", "user", "assistant"}

    def __init__(self, system_message=None):
        """初始化对话历史，可选 system_message"""
        self.messages = []
        self._roles = set(self._DEFAULT_ROLES)  # 允许的角色集合
        if system_message:
            self._add_message("system", system_message)

    def _add_message(self, role, content):
        """内部方法：添加消息"""
        if role not in self._roles:
            raise ValueError(f"Invalid role: {role}. Allowed roles: {self._roles}")
        self.messages.append({"role": role, "content": content})

    def add_user_message(self, content):
        """添加用户消息"""
        self._add_message("user", content)

    def add_assistant_message(self, content):
        """添加 AI 回复"""
        self._add_message("assistant", content)

    def add_custom_message(self, role, content):
        """添加自定义角色的消息"""
        if role not in self._roles:
            raise ValueError(f"Role '{role}' is not registered. Use `register_role()` first.")
        self._add_message(role, content)

    def register_role(self, role):
        """注册新角色"""
        if role in self._DEFAULT_ROLES:
            raise ValueError(f"Role '{role}' is already a default role and cannot be redefined.")
        self._roles.add(role)

    def get_messages(self):
        """获取当前对话历史"""
        return self.messages

    def reset(self, system_message=None):
        """重置对话历史"""
        self.messages = []
        if system_message:
            self._add_message("system", system_message)