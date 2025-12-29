"""Neo4j connection management."""
import os
from typing import Optional
from neo4j import GraphDatabase, Driver, Session
import structlog
from contextlib import contextmanager

from app.core.config import settings

logger = structlog.get_logger(__name__)

_neo4j_driver: Optional[Driver] = None


def get_neo4j_driver() -> Driver:
    """Get or create Neo4j driver instance."""
    global _neo4j_driver
    
    if _neo4j_driver is None:
        uri = os.getenv("NEO4J_URI", settings.NEO4J_URI)
        user = os.getenv("NEO4J_USER", settings.NEO4J_USER)
        password = os.getenv("NEO4J_PASSWORD", settings.NEO4J_PASSWORD)
        
        # Check if Neo4j service is available before trying to connect
        import socket
        from urllib.parse import urlparse
        
        try:
            parsed = urlparse(uri)
            host = parsed.hostname or "localhost"
            port = parsed.port or 7687
            
            # Try to connect to the port to see if Neo4j is running
            sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
            sock.settimeout(2)  # 2 second timeout
            result = sock.connect_ex((host, port))
            sock.close()
            
            if result != 0:
                # Port is not open, Neo4j is likely not running
                logger.warning(
                    f"Neo4j port {port} on {host} is not accessible. "
                    f"Neo4j is not running. "
                    f"To start Neo4j, run: docker-compose up -d neo4j"
                )
                raise ConnectionError(
                    f"Neo4j is not running on {host}:{port}. "
                    f"Please start Neo4j with: docker-compose up -d neo4j"
                )
        except socket.gaierror as e:
            logger.warning(f"Could not resolve Neo4j host {host}: {e}")
            raise ConnectionError(f"Could not resolve Neo4j host {host}: {e}") from e
        except ConnectionError:
            # Re-raise our own ConnectionError
            raise
        except Exception as e:
            # If socket check fails, still try to connect (might be a different issue)
            logger.debug(f"Socket check failed, will try direct connection: {e}")
        
        try:
            _neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
            # Verify connection with timeout
            _neo4j_driver.verify_connectivity(timeout=5)
            logger.info("Neo4j connection established", uri=uri, user=user)
        except Exception as e:
            error_msg = str(e)
            logger.error(
                "Failed to connect to Neo4j",
                error=error_msg,
                uri=uri,
                host=host if 'host' in locals() else 'unknown',
                port=port if 'port' in locals() else 'unknown'
            )
            
            # Provide helpful error message
            if "Connection refused" in error_msg or "refused" in error_msg.lower():
                raise ConnectionError(
                    f"Neo4j is not running on {host}:{port}. "
                    f"To start Neo4j:\n"
                    f"  1. Ensure docker-compose.yml has neo4j service\n"
                    f"  2. Run: docker-compose up -d neo4j\n"
                    f"  3. Wait for Neo4j to start (check logs: docker-compose logs neo4j)\n"
                    f"  4. Verify Neo4j is running: docker-compose ps neo4j"
                ) from e
            else:
                raise ConnectionError(f"Neo4j connection failed: {error_msg}") from e
    
    return _neo4j_driver


def close_neo4j_driver():
    """Close Neo4j driver connection."""
    global _neo4j_driver
    
    if _neo4j_driver is not None:
        try:
            _neo4j_driver.close()
            logger.info("Neo4j connection closed")
        except Exception as e:
            logger.error("Error closing Neo4j connection", error=str(e))
        finally:
            _neo4j_driver = None


@contextmanager
def get_neo4j_session(database: str = "neo4j"):
    """Get a Neo4j session with automatic cleanup."""
    try:
        driver = get_neo4j_driver()
        session = driver.session(database=database)
        try:
            yield session
        finally:
            session.close()
    except ConnectionError:
        # Re-raise connection errors
        raise
    except Exception as e:
        # If we can't get a driver or session, raise a more specific error
        # that can be caught by callers
        error_msg = str(e)
        if "connection" in error_msg.lower() or "refused" in error_msg.lower() or "ServiceUnavailable" in error_msg:
            raise ConnectionError(f"Neo4j is not available: {error_msg}") from e
        raise

