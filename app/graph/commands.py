"""Command log for undo/redo functionality."""
from typing import Dict, Any, List, Optional
from neo4j import Session
from datetime import datetime
import uuid
import structlog
from app.graph.connection import get_neo4j_session

logger = structlog.get_logger(__name__)


class Command:
    """Represents a reversible command."""
    def __init__(
        self,
        command_id: str,
        project_id: str,
        user_id: str,
        command_type: str,
        payload: Dict[str, Any],
        inverse_payload: Dict[str, Any]
    ):
        self.id = command_id
        self.project_id = project_id
        self.user_id = user_id
        self.type = command_type
        self.payload = payload
        self.inverse_payload = inverse_payload
        self.timestamp = datetime.utcnow().isoformat()
    
    def to_dict(self):
        return {
            "id": self.id,
            "project_id": self.project_id,
            "user_id": self.user_id,
            "type": self.type,
            "payload": self.payload,
            "inverse_payload": self.inverse_payload,
            "timestamp": self.timestamp
        }


class CommandLog:
    """Manages command log for undo/redo."""
    
    @staticmethod
    def log_command(
        project_id: str,
        user_id: str,
        command_type: str,
        payload: Dict[str, Any],
        inverse_payload: Dict[str, Any]
    ) -> str:
        """Log a command."""
        command_id = str(uuid.uuid4())
        
        with get_neo4j_session() as session:
            query = """
            MATCH (project:Project {id: $project_id})
            CREATE (cmd:Command {
                id: $command_id,
                userId: $user_id,
                type: $command_type,
                payload: $payload,
                inversePayload: $inverse_payload,
                timestamp: datetime()
            })
            CREATE (project)-[:HAS_COMMAND]->(cmd)
            RETURN cmd.id as id
            """
            result = session.run(
                query,
                project_id=project_id,
                command_id=command_id,
                user_id=user_id,
                command_type=command_type,
                payload=payload,
                inverse_payload=inverse_payload
            )
            record = result.single()
            if record:
                return record["id"]
            raise ValueError("Failed to log command")
    
    @staticmethod
    def get_commands(project_id: str, limit: int = 100) -> List[Dict[str, Any]]:
        """Get recent commands for a project."""
        with get_neo4j_session() as session:
            query = """
            MATCH (project:Project {id: $project_id})-[:HAS_COMMAND]->(cmd:Command)
            RETURN cmd
            ORDER BY cmd.timestamp DESC
            LIMIT $limit
            """
            result = session.run(query, project_id=project_id, limit=limit)
            commands = []
            for record in result:
                cmd = record["cmd"]
                commands.append({
                    "id": cmd["id"],
                    "user_id": cmd["userId"],
                    "type": cmd["type"],
                    "payload": cmd["payload"],
                    "inverse_payload": cmd["inversePayload"],
                    "timestamp": cmd["timestamp"]
                })
            return commands
    
    @staticmethod
    def get_last_command(project_id: str) -> Optional[Dict[str, Any]]:
        """Get the last command for undo."""
        commands = CommandLog.get_commands(project_id, limit=1)
        return commands[0] if commands else None

