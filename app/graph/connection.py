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
        
        try:
            _neo4j_driver = GraphDatabase.driver(uri, auth=(user, password))
            # Verify connection
            _neo4j_driver.verify_connectivity()
            logger.info("Neo4j connection established", uri=uri, user=user)
        except Exception as e:
            logger.error("Failed to connect to Neo4j", error=str(e), uri=uri)
            # Raise ConnectionError so callers can handle it
            raise ConnectionError(f"Neo4j is not available: {str(e)}") from e
    
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

