from typing import List, Union, Generator, Iterator, Optional
from pprint import pprint
import requests
import json
from pydantic import BaseModel, Field


class Pipeline:
    class Valves(BaseModel):
        api_endpoint: str = Field(
            default="http://flowise:3030", description="Flowise API endpoint"
        )
        chatflow_id: str = Field(default="", description="Flowise chatflow ID")
        api_key: Optional[str] = Field(default=None, description="Flowise API key")
        debug: bool = Field(default=True, description="Enable debug logging")

    def __init__(self):
        self.name = "Flowise Pipeline"
        self.valves = self.Valves()

    async def on_startup(self):
        print(f"on_startup: {__name__}")
        pass

    async def on_shutdown(self):
        print(f"on_shutdown: {__name__}")
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"inlet: {__name__}")
        if self.valves.debug:
            print(f"inlet: {__name__} - body:")
            pprint(body)
            print(f"inlet: {__name__} - user:")
            pprint(user)
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"outlet: {__name__}")
        if self.valves.debug:
            print(f"outlet: {__name__} - body:")
            pprint(body)
            print(f"outlet: {__name__} - user:")
            pprint(user)
        return body

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe: {__name__}")

        if self.valves.debug:
            print(f"pipe: {__name__} - received message from user: {user_message}")

        url = f"{self.valves.api_endpoint}/api/v1/prediction/{self.valves.chatflow_id}"
        headers = {"Content-Type": "application/json"}

        if self.valves.api_key:
            headers["Authorization"] = f"Bearer {self.valves.api_key}"

        data = {"question": user_message}

        response = requests.post(url, headers=headers, json=data)
        if response.status_code == 200:
            try:
                json_response = response.json()
                # Try different possible response fields
                result = json_response.get("text", json_response.get("answer", ""))
                yield result
            except json.JSONDecodeError as e:
                print(f"Failed to parse JSON response. Error: {str(e)}")
                yield "Error in JSON parsing."
        else:
            yield f"Flowise request failed with status code: {response.status_code}"
