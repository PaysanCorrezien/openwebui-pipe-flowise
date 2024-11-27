from typing import List, Union, Generator, Iterator, Optional, Dict
from pprint import pprint
import requests
import json
from pydantic import BaseModel, Field, validator


class Pipeline:
    class Valves(BaseModel):
        api_endpoint: str = Field(
            default="http://flowise:3030", description="Flowise API endpoint"
        )
        chatflow_id: str = Field(default="", description="Flowise chatflow ID")
        api_key: Optional[str] = Field(default=None, description="Flowise API key")
        override_config: Optional[str] = Field(
            default=None,
            description='Optional JSON configuration to override Flowise settings. Example: { "analytics": { "langFuse": { "userId": "user1" } }, "temperature": 0.7, "maxTokens": 500 }',
        )
        debug: bool = Field(default=False, description="Enable debug logging")

        @validator("override_config")
        def validate_json(cls, v):
            if v is None:
                return v
            try:
                config = json.loads(v)
                if not isinstance(config, dict):
                    raise ValueError("Override config must be a JSON object")
                return v
            except json.JSONDecodeError as e:
                raise ValueError(f"Invalid JSON format: {str(e)}")

    def __init__(self):
        self.name = "Flowise Pipeline"
        self.valves = self.Valves()

    def debug_log(self, message: str, data: any = None):
        """Helper method for consistent debug logging"""
        if self.valves.debug:
            print(f"[DEBUG] {message}")
            if data is not None:
                if isinstance(data, str):
                    print(f"[DEBUG] {data}")
                else:
                    print(f"[DEBUG] {json.dumps(data, indent=2)}")

    async def on_startup(self):
        print(f"on_startup: {__name__}")

    async def on_shutdown(self):
        print(f"on_shutdown: {__name__}")

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        self.debug_log("Inlet called", body)
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        self.debug_log("Outlet called", body)
        return body

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        self.debug_log("Pipe started", f"Message: {user_message}")

        url = f"{self.valves.api_endpoint}/api/v1/prediction/{self.valves.chatflow_id}"
        headers = {"Content-Type": "application/json"}

        if self.valves.api_key:
            headers["Authorization"] = f"Bearer {self.valves.api_key}"

        payload = {"question": user_message, "streaming": True}

        # Add override config if provided
        if self.valves.override_config:
            try:
                override_config = json.loads(self.valves.override_config)
                payload["overrideConfig"] = override_config
                self.debug_log("Using override config", override_config)
            except json.JSONDecodeError as e:
                self.debug_log("Error parsing override config", str(e))

        # Add message history if available
        if messages and len(messages) > 1:
            history = []
            for msg in messages[:-1]:  # Exclude the current message
                role = "userMessage" if msg["role"] == "user" else "apiMessage"
                history.append({"role": role, "content": msg["content"]})
            payload["history"] = history
            self.debug_log("Added message history", history)

        try:
            self.debug_log("Starting Flowise request", payload)
            response = requests.post(url, json=payload, headers=headers, stream=True)
            response.raise_for_status()

            if body.get("stream", True):
                self.debug_log("Processing streaming response")
                for line in response.iter_lines():
                    if line:
                        line_str = line.decode("utf-8")
                        if line_str.startswith("data:"):
                            event_str = line_str.replace("data:", "").strip()
                            if event_str == "[DONE]":
                                self.debug_log("Stream completed")
                                continue

                            try:
                                event = json.loads(event_str)
                                if event.get("event") == "token":
                                    token = event.get("data", "")
                                    self.debug_log("Token", token)
                                    yield token
                            except json.JSONDecodeError as e:
                                self.debug_log("JSON decode error", str(e))
                                continue
            else:
                self.debug_log("Non-streaming mode")
                data = response.json()
                return data.get("text", data.get("answer", ""))
        except Exception as e:
            error_msg = f"Error in pipe: {str(e)}"
            self.debug_log("Error occurred", error_msg)
            return f"Error: {str(e)}"
