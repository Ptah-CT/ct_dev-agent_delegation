"""SQLite database for orchestrator state persistence."""

import sqlite3
from pathlib import Path
from typing import Optional
import logfire
from contextlib import contextmanager


class Database:
    """SQLite database manager for orchestrator."""
    
    def __init__(self, db_path: str = "data/orchestrator.db"):
        """Initialize database.
        
        Args:
            db_path: Path to SQLite database file
        """
        self.db_path = Path(db_path)
        self.db_path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
    
    def _init_schema(self):
        """Initialize database schema."""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            
            # Agents table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS agents (
                    agent_id TEXT PRIMARY KEY,
                    role TEXT NOT NULL,
                    status TEXT NOT NULL,
                    port INTEGER,
                    pid INTEGER,
                    health_check_url TEXT,
                    created_at TEXT NOT NULL,
                    last_health_check TEXT,
                    current_delegation_id TEXT,
                    metadata TEXT
                )
            """)
            
            # Delegations table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS delegations (
                    delegation_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    task_id TEXT NOT NULL,
                    status TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    started_at TEXT,
                    completed_at TEXT,
                    instructions TEXT NOT NULL,
                    context TEXT,
                    timeout_seconds INTEGER NOT NULL,
                    result TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            # Delegation events (audit trail)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS delegation_events (
                    event_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    delegation_id TEXT NOT NULL,
                    timestamp TEXT NOT NULL,
                    event_type TEXT NOT NULL,
                    delegator TEXT NOT NULL,
                    delegatee_agent_id TEXT NOT NULL,
                    outcome TEXT,
                    deviation_reason TEXT,
                    responsibility_chain TEXT,
                    FOREIGN KEY (delegation_id) REFERENCES delegations(delegation_id)
                )
            """)
            
            # Server instances table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS server_instances (
                    instance_id TEXT PRIMARY KEY,
                    agent_id TEXT NOT NULL,
                    hostname TEXT NOT NULL,
                    port INTEGER NOT NULL,
                    pid INTEGER,
                    status TEXT NOT NULL,
                    started_at TEXT NOT NULL,
                    stopped_at TEXT,
                    health_metrics TEXT,
                    FOREIGN KEY (agent_id) REFERENCES agents(agent_id)
                )
            """)
            
            # Constitution checks table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS constitution_checks (
                    check_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TEXT NOT NULL,
                    operation_type TEXT NOT NULL,
                    principles_checked TEXT NOT NULL,
                    violations TEXT,
                    approved INTEGER NOT NULL,
                    justification TEXT
                )
            """)
            
            # Create indices for common queries
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_agents_status 
                ON agents(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_delegations_status 
                ON delegations(status)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_delegations_agent 
                ON delegations(agent_id)
            """)
            
            cursor.execute("""
                CREATE INDEX IF NOT EXISTS idx_events_delegation 
                ON delegation_events(delegation_id)
            """)
            
            # Enable WAL mode for better concurrency
            cursor.execute("PRAGMA journal_mode=WAL")
            
            conn.commit()
            logfire.info("Database schema initialized", db_path=str(self.db_path))
    
    @contextmanager
    def get_connection(self):
        """Get database connection context manager.
        
        Yields:
            SQLite connection
        """
        conn = sqlite3.connect(self.db_path, timeout=30.0)
        conn.row_factory = sqlite3.Row
        try:
            yield conn
        finally:
            conn.close()
    
    def execute(self, query: str, params: tuple = ()) -> sqlite3.Cursor:
        """Execute query and return cursor.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Cursor with results
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            conn.commit()
            return cursor
    
    def fetchone(self, query: str, params: tuple = ()) -> Optional[dict]:
        """Fetch one result.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            Result dict or None
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            row = cursor.fetchone()
            return dict(row) if row else None
    
    def fetchall(self, query: str, params: tuple = ()) -> list[dict]:
        """Fetch all results.
        
        Args:
            query: SQL query
            params: Query parameters
            
        Returns:
            List of result dicts
        """
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(query, params)
            rows = cursor.fetchall()
            return [dict(row) for row in rows]


# Global database instance
_db: Optional[Database] = None


def get_database() -> Database:
    """Get global database instance.
    
    Returns:
        Database instance
    """
    global _db
    if _db is None:
        _db = Database()
    return _db


if __name__ == "__main__":
    # CLI for database migration
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "migrate":
        db = Database()
        print(f"✓ Database schema initialized: {db.db_path}")
    else:
        print("Usage: python database.py migrate")
