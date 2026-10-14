"""In-memory conversation management. No persistence or network access."""
from dataclasses import dataclass, field

@dataclass
class Conversation:
    max_turns: int = 12
    messages: list = field(default_factory=list)

    def __post_init__(self):
        if not isinstance(self.max_turns, int) or isinstance(self.max_turns, bool) or self.max_turns < 1:
            raise ValueError("max_turns must be a positive integer")

    def add(self, role: str, content: str):
        if role not in ("user", "assistant") or not isinstance(content, str) or not content.strip():
            raise ValueError("Invalid conversation message")
        self.messages.append({"role": role, "content": content})
        self.messages = self.messages[-2 * self.max_turns:]

    def clear(self):
        self.messages.clear()

    def snapshot(self):
        return [dict(item) for item in self.messages]
