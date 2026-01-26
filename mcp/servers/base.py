"""
Base MCP Server Implementation for Healthcare
Provides common functionality for all MCP servers
"""

from abc import ABC, abstractmethod
from typing import Any, Callable
from pydantic import BaseModel
from fastapi import FastAPI, HTTPException, Header, Request
from fastapi.middleware.cors import CORSMiddleware
import logging
import time
import uuid
from datetime import datetime
from functools import wraps

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ============================================================================
# MCP Protocol Types
# ============================================================================

class MCPToolDefinition(BaseModel):
    """Definition of an MCP tool"""
    name: str
    description: str
    input_schema: dict
    output_schema: dict
    category: str = "general"
    requires_patient_context: bool = True


class MCPRequest(BaseModel):
    """Standard MCP request format"""
    tool_name: str
    arguments: dict
    request_id: str = None
    patient_id: str = None
    user_id: str = None
    session_id: str = None

    def __init__(self, **data):
        if not data.get("request_id"):
            data["request_id"] = str(uuid.uuid4())
        super().__init__(**data)


class MCPResponse(BaseModel):
    """Standard MCP response format"""
    request_id: str
    tool_name: str
    success: bool
    data: Any = None
    error: str = None
    metadata: dict = {}
    execution_time_ms: float = 0
    timestamp: str = None

    def __init__(self, **data):
        if not data.get("timestamp"):
            data["timestamp"] = datetime.utcnow().isoformat()
        super().__init__(**data)


class AuditLogEntry(BaseModel):
    """HIPAA-compliant audit log entry"""
    timestamp: datetime
    request_id: str
    user_id: str
    patient_id: str
    tool_name: str
    action: str
    resource_type: str
    resource_id: str = None
    success: bool
    error_message: str = None
    ip_address: str = None
    user_agent: str = None


# ============================================================================
# Base MCP Server
# ============================================================================

class BaseMCPServer(ABC):
    """
    Base class for all MCP servers in the healthcare platform.
    Provides common functionality like:
    - Tool registration
    - Authentication
    - Audit logging
    - Error handling
    - HIPAA compliance
    """

    def __init__(self, name: str, description: str, version: str = "1.0.0"):
        self.name = name
        self.description = description
        self.version = version
        self.tools: dict[str, Callable] = {}
        self.tool_definitions: dict[str, MCPToolDefinition] = {}
        self.app = self._create_app()
        self._register_routes()

    def _create_app(self) -> FastAPI:
        """Create FastAPI application with middleware"""
        app = FastAPI(
            title=f"MCP Server: {self.name}",
            description=self.description,
            version=self.version
        )

        app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

        return app

    def _register_routes(self):
        """Register standard MCP routes"""

        @self.app.get("/")
        async def root():
            return {
                "server": self.name,
                "description": self.description,
                "version": self.version,
                "tools_count": len(self.tools)
            }

        @self.app.get("/tools")
        async def list_tools():
            """List all available tools"""
            return {
                "tools": [
                    {
                        "name": name,
                        "description": defn.description,
                        "category": defn.category,
                        "requires_patient_context": defn.requires_patient_context
                    }
                    for name, defn in self.tool_definitions.items()
                ]
            }

        @self.app.get("/tools/{tool_name}/schema")
        async def get_tool_schema(tool_name: str):
            """Get schema for a specific tool"""
            if tool_name not in self.tool_definitions:
                raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")
            return self.tool_definitions[tool_name].dict()

        @self.app.post("/tools/{tool_name}")
        async def invoke_tool(
            tool_name: str,
            request: Request,
            authorization: str = Header(default=None)
        ):
            """Invoke a tool"""
            if tool_name not in self.tools:
                raise HTTPException(status_code=404, detail=f"Tool {tool_name} not found")

            start_time = time.time()
            body = await request.json()

            mcp_request = MCPRequest(
                tool_name=tool_name,
                arguments=body.get("arguments", body),
                patient_id=body.get("patient_id"),
                user_id=body.get("user_id"),
                session_id=body.get("session_id")
            )

            try:
                # Execute tool
                result = await self.tools[tool_name](mcp_request)
                execution_time = (time.time() - start_time) * 1000

                # Audit log
                await self._audit_log(mcp_request, True)

                return MCPResponse(
                    request_id=mcp_request.request_id,
                    tool_name=tool_name,
                    success=True,
                    data=result,
                    execution_time_ms=execution_time
                )

            except Exception as e:
                logger.error(f"Tool {tool_name} failed: {str(e)}")
                await self._audit_log(mcp_request, False, str(e))

                return MCPResponse(
                    request_id=mcp_request.request_id,
                    tool_name=tool_name,
                    success=False,
                    error=str(e),
                    execution_time_ms=(time.time() - start_time) * 1000
                )

        @self.app.get("/health")
        async def health():
            return {"status": "healthy", "server": self.name}

    def register_tool(
        self,
        name: str,
        description: str,
        input_schema: dict,
        output_schema: dict,
        category: str = "general",
        requires_patient_context: bool = True
    ):
        """Decorator to register a tool"""
        def decorator(func: Callable):
            self.tool_definitions[name] = MCPToolDefinition(
                name=name,
                description=description,
                input_schema=input_schema,
                output_schema=output_schema,
                category=category,
                requires_patient_context=requires_patient_context
            )

            @wraps(func)
            async def wrapper(request: MCPRequest):
                return await func(request)

            self.tools[name] = wrapper
            return wrapper
        return decorator

    async def _audit_log(self, request: MCPRequest, success: bool, error: str = None):
        """Log access for HIPAA compliance"""
        entry = AuditLogEntry(
            timestamp=datetime.utcnow(),
            request_id=request.request_id,
            user_id=request.user_id or "system",
            patient_id=request.patient_id or "unknown",
            tool_name=request.tool_name,
            action="tool_invocation",
            resource_type=self.name,
            success=success,
            error_message=error
        )
        logger.info(f"AUDIT: {entry.dict()}")
        # In production, persist to audit database

    @abstractmethod
    def setup_tools(self):
        """Override to register tools specific to this server"""
        pass
