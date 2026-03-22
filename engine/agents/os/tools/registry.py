from typing import Dict, Any, Callable, Type, List, Optional
from pydantic import BaseModel
import inspect
import json
import logging

log = logging.getLogger(__name__)

class OSToolRegistry:
    def __init__(self):
        self.tools: Dict[str, Dict[str, Any]] = {}

    def register(self, name: str, model: Type[BaseModel], handler: Callable, description: str = ""):
        """Register a tool with its input model and handler function."""
        self.tools[name] = {
            "model": model,
            "handler": handler,
            "description": description
        }

    def get_definitions(self) -> str:
        """
        Returns a formatted string of tool definitions for the system prompt.
        Format matches the 'tools with parameters' style in the user request.
        """
        lines = []
        for name, tool in self.tools.items():
            lines.append(f"{name}")
            schema = tool["model"].model_json_schema()
            props = schema.get("properties", {})
            required = schema.get("required", [])
            
            for prop_name, prop_info in props.items():
                if prop_name == "tool_name": continue
                
                desc = prop_info.get("description", "")
                default = prop_info.get("default", "<<required>>")
                if prop_name in required:
                    default_str = "required"
                else:
                    default_str = f"default: {default}"
                
                lines.append(f"  {prop_name} ({default_str}): {desc}")
            lines.append("")
        return "\n".join(lines)

    async def execute(self, tool_name: str, params: Dict[str, Any]) -> str:
        tool = self.tools.get(tool_name)
        if not tool:
            return f"Error: Tool '{tool_name}' not registered."

        try:
            # 1. Validate Input
            input_model = tool["model"](**params)
            
            # 2. Key matching
            # We filter out 'tool_name' and arguments not present in the handler?
            # Or trust the model matches the handler.
            # Safety: inspect handler signature.
            handler = tool["handler"]
            sig = inspect.signature(handler)
            
            # Prepare arguments
            handler_args = input_model.dict()
            if "tool_name" in handler_args:
                del handler_args["tool_name"]
                
            # Filter args to match signature (to avoid 'unexpected keyword argument')
            # But we want to support **kwargs if present.
            has_kwargs = any(p.kind == inspect.Parameter.VAR_KEYWORD for p in sig.parameters.values())
            
            if not has_kwargs:
                valid_keys = set(sig.parameters.keys())
                handler_args = {k: v for k, v in handler_args.items() if k in valid_keys}

            # 3. Execute
            if inspect.iscoroutinefunction(handler):
                result = await handler(**handler_args)
            else:
                result = handler(**handler_args)

            # 4. Format Output
            if isinstance(result, (dict, list)):
                return json.dumps(result, indent=2, default=str)
            return str(result)

        except Exception as e:
            log.error(f"Error executing {tool_name}: {e}", exc_info=True)
            return f"Error executing {tool_name}: {e}"
