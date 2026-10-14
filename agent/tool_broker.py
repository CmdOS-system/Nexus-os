"""Fail-closed tool broker. No shell execution is implemented."""
from dataclasses import dataclass
from typing import Callable
from nexus_agent import ToolPolicy

@dataclass(frozen=True)
class Tool:
    name: str
    handler: Callable
    schema: dict

class ToolBroker:
    def __init__(self, policy: ToolPolicy):
        if not isinstance(policy, ToolPolicy):
            raise TypeError("ToolPolicy required")
        self.policy = policy
        self._tools = {}

    def register(self, name: str, handler: Callable, schema: dict):
        if not isinstance(name, str) or not name.strip():
            raise ValueError("Tool name required")
        if name in self._tools:
            raise ValueError("Tool already registered")
        if not callable(handler):
            raise TypeError("Tool handler must be callable")
        if not isinstance(schema, dict):
            raise TypeError("Tool schema must be a dictionary")
        allowed = schema.get("properties", {})
        required = schema.get("required", [])
        if schema.get("type") != "object" or not isinstance(allowed, dict) or not isinstance(required, list):
            raise ValueError("Invalid tool schema")
        if not set(required).issubset(allowed):
            raise ValueError("Required fields must be declared")
        self._tools[name] = Tool(name, handler, schema)

    def invoke(self, name: str, arguments: dict, approved: bool = False):
        self.policy.authorize(name, approved=approved)
        try:
            tool = self._tools[name]
        except KeyError:
            raise LookupError("Tool is not registered") from None
        if not isinstance(arguments, dict):
            raise ValueError("Tool arguments must be an object")
        props = tool.schema["properties"]
        required = set(tool.schema.get("required", []))
        if set(arguments) - set(props):
            raise ValueError("Unexpected tool argument")
        if required - set(arguments):
            raise ValueError("Missing required tool argument")
        for key, value in arguments.items():
            expected = props[key].get("type")
            if expected == "string" and not isinstance(value, str):
                raise ValueError("Invalid tool argument type")
            if expected == "boolean" and type(value) is not bool:
                raise ValueError("Invalid tool argument type")
            if expected == "integer" and (type(value) is not int):
                raise ValueError("Invalid tool argument type")
        return tool.handler(**arguments)

    def names(self):
        return tuple(sorted(self._tools))
