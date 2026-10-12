from typing import Any
import httpx


class SupabaseRepository:
    def __init__(self, base_url: str, service_role_key: str, timeout: float = 20.0):
        self.base_url = base_url.rstrip("/") + "/rest/v1"
        self.client = httpx.Client(
            timeout=timeout,
            headers={
                "apikey": service_role_key,
                "Authorization": f"Bearer {service_role_key}",
                "Content-Type": "application/json",
            },
        )

    def close(self) -> None:
        self.client.close()

    def select(self, table: str, params: dict[str, str]) -> list[dict[str, Any]]:
        response = self.client.get(f"{self.base_url}/{table}", params=params)
        response.raise_for_status()
        data = response.json()
        if not isinstance(data, list):
            raise RuntimeError(f"Unexpected response from {table}")
        return data

    def update(self, table: str, match: dict[str, str], values: dict[str, Any]) -> None:
        response = self.client.patch(
            f"{self.base_url}/{table}",
            params=match,
            json=values,
            headers={"Prefer": "return=minimal"},
        )
        response.raise_for_status()

    def insert(
        self,
        table: str,
        values: dict[str, Any],
        *,
        on_conflict: str | None = None,
    ) -> dict[str, Any] | None:
        headers = {"Prefer": "return=representation"}
        params = {}
        if on_conflict:
            params["on_conflict"] = on_conflict
            headers["Prefer"] = "resolution=ignore-duplicates,return=representation"
        response = self.client.post(
            f"{self.base_url}/{table}",
            params=params,
            json=values,
            headers=headers,
        )
        response.raise_for_status()
        data = response.json()
        return data[0] if isinstance(data, list) and data else None
