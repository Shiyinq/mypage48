import asyncio
import json
import logging
import os
import time

import httpx

from ..config import RecorderConfig


class HealthChecker:
    def __init__(self, config: RecorderConfig):
        self.config = config
        self.log = logging.getLogger("theater")
        self.theater_dir = self.config.theater_dir
        self.state_file = os.path.join(self.theater_dir, "health_state.json")
        self.pending_dir = os.path.join(self.theater_dir, "pending_notifications")

        os.makedirs(self.theater_dir, exist_ok=True)
        os.makedirs(self.pending_dir, exist_ok=True)

    def _get_state(self) -> dict:
        if os.path.exists(self.state_file):
            try:
                with open(self.state_file, "r") as f:
                    return json.load(f)
            except Exception:
                return {}
        return {}

    def _save_state(self, state: dict):
        with open(self.state_file, "w") as f:
            json.dump(state, f, indent=2)

    async def _check_frontend(self, url: str) -> tuple[str, str]:
        """Returns ('UP'/'DOWN', status_code)."""
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                if response.status_code == 200:
                    return "UP", str(response.status_code)
                return "DOWN", str(response.status_code)
        except Exception as e:
            return "DOWN", "ERR"

    async def _check_backend(self, url: str) -> tuple[dict, str]:
        """Returns (detailed state dict, status_code)."""
        state = {"api": "DOWN", "database": "DOWN", "storage": "DOWN"}
        code = "ERR"
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.get(url)
                code = str(response.status_code)
                if response.status_code in (200, 503):
                    data = response.json()
                    state["api"] = "UP" if data.get("status") == "ok" else "DOWN"
                    state["database"] = (
                        "UP" if data.get("database") == "connected" else "DOWN"
                    )
                    state["storage"] = (
                        "UP" if data.get("storage") == "connected" else "DOWN"
                    )
        except Exception:
            pass
        return state, code

    async def _check_health(self):
        self.log.info("Checking API and Frontend health...")

        api_url = f"{self.config.api_base_url}/health"
        frontend_url = f"{self.config.frontend_base_url}/health"

        backend_status, backend_code = await self._check_backend(api_url)
        frontend_status, frontend_code = await self._check_frontend(frontend_url)

        current_state = self._get_state()
        changes = []

        def _check_change(service_key, service_name, new_status):
            old_status = current_state.get(service_key)
            if old_status and old_status != new_status:
                changes.append(
                    {
                        "service": service_name,
                        "old_state": old_status,
                        "new_state": new_status,
                    }
                )

        _check_change("api", "Backend API", backend_status["api"])
        _check_change("database", "Database", backend_status["database"])
        _check_change("storage", "Storage R2", backend_status["storage"])
        _check_change("frontend", "Frontend", frontend_status)

        new_state = {
            "api": backend_status["api"],
            "api_code": backend_code,
            "database": backend_status["database"],
            "storage": backend_status["storage"],
            "frontend": frontend_status,
            "frontend_code": frontend_code,
        }
        self._save_state(new_state)

        if changes:
            timestamp = int(time.time() * 1000)
            payload_file = os.path.join(self.pending_dir, f"health_{timestamp}.json")

            payload = {
                "type": "health",
                "changes": changes,
                "state": new_state,
            }

            with open(payload_file, "w") as f:
                json.dump(payload, f, indent=2)

            self.log.info("Prepared health notification payload: %s", payload_file)

    async def run(self, stop_event: asyncio.Event):
        self.log.info("Starting Health Checker...")
        while not stop_event.is_set():
            await self._check_health()

            try:
                await asyncio.wait_for(
                    stop_event.wait(), timeout=self.config.health_check_interval
                )
            except asyncio.TimeoutError:
                pass
