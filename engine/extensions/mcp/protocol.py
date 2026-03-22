from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, Field, ConfigDict

class JsonRpcRequest(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    method: str
    params: Optional[Dict[str, Any]] = None

class JsonRpcResponse(BaseModel):
    jsonrpc: str = "2.0"
    id: Union[str, int]
    result: Optional[Any] = None
    error: Optional[Dict[str, Any]] = None

class JsonRpcNotification(BaseModel):
    jsonrpc: str = "2.0"
    method: str
    params: Optional[Dict[str, Any]] = None

class ToolInputSchema(BaseModel):
    type: str = "object"
    properties: Dict[str, Any] = Field(default_factory=dict)
    required: List[str] = Field(default_factory=list)

class Tool(BaseModel):
    name: str
    description: str = ""
    inputSchema: ToolInputSchema = Field(default_factory=ToolInputSchema)

class CallToolRequestParams(BaseModel):
    name: str
    arguments: Dict[str, Any]

class CallToolResult(BaseModel):
    content: List[Dict[str, Any]]
    isError: bool = False

class ClientCapabilities(BaseModel):
    roots: Optional[Dict[str, Any]] = None
    sampling: Optional[Dict[str, Any]] = None

class InitializeParams(BaseModel):
    protocolVersion: str = "2024-11-05"
    capabilities: ClientCapabilities = Field(default_factory=ClientCapabilities)
    clientInfo: Dict[str, str] = Field(default_factory=lambda: {"name": "dexpert-engine", "version": "0.1.0"})

class ServerCapabilities(BaseModel):
    tools: Optional[Dict[str, Any]] = None
    resources: Optional[Dict[str, Any]] = None
    prompts: Optional[Dict[str, Any]] = None

class InitializeResult(BaseModel):
    protocolVersion: str
    capabilities: ServerCapabilities
    serverInfo: Dict[str, str]
