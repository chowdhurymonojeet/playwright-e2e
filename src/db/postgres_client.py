from __future__ import annotations

from typing import TYPE_CHECKING, Any

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

if TYPE_CHECKING:
    from src.services.test_context import TestContext


class PostgresClient:
    """Async, read-only SQL adapter for database validation."""

    def __init__(
        self,
        dsn: str,
        *,
        echo: bool = False,
        context: TestContext | None = None,
    ) -> None:
        if not dsn:
            raise ValueError("Database DSN is required to create PostgresClient")
        self.engine: AsyncEngine = create_async_engine(dsn, echo=echo)
        self.context = context

    async def fetch_one(self, query: str, **params: Any) -> dict[str, Any] | None:
        # Inject test_run_id filter if context available and query has WHERE clause
        if self.context and "WHERE" in query.upper():
            # Add test_run_id filter to existing WHERE
            query = query.replace(
                "WHERE",
                f"WHERE test_run_id = :test_run_id AND",
                1,  # Only replace first occurrence
            )
            params["test_run_id"] = self.context.run_id

        async with self.engine.connect() as connection:
            result = await connection.execute(text(query), params)
            row = result.mappings().first()
            return dict(row) if row else None

    async def fetch_all(self, query: str, **params: Any) -> list[dict[str, Any]]:
        # Inject test_run_id filter if context available and query has WHERE clause
        if self.context and "WHERE" in query.upper():
            query = query.replace(
                "WHERE",
                f"WHERE test_run_id = :test_run_id AND",
                1,
            )
            params["test_run_id"] = self.context.run_id

        async with self.engine.connect() as connection:
            result = await connection.execute(text(query), params)
            rows = result.mappings().all()
            return [dict(row) for row in rows]

    async def aclose(self) -> None:
        await self.engine.dispose()
