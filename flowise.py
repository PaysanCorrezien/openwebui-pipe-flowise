from typing import List, Union, Generator, Iterator, Optional
from pprint import pprint
import requests
import json


class Pipeline:
    def __init__(self):
        self.name = "Flowise Pipeline"
        self.api_endpoint = "http://flowise:3030"  # Set your Flowise endpoint
        self.chatflow_id = ""  # Set your chatflow ID
        self.api_key = None  # Optional: Set your API key
        self.debug = True

    async def on_startup(self):
        print(f"on_startup: {__name__}")
        pass

    async def on_shutdown(self):
        print(f"on_shutdown: {__name__}")
        pass

    async def inlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"inlet: {__name__}")
        if self.debug:
            print(f"inlet: {__name__} - body:")
            pprint(body)
            print(f"inlet: {__name__} - user:")
            pprint(user)
        return body

    async def outlet(self, body: dict, user: Optional[dict] = None) -> dict:
        print(f"outlet: {__name__}")
        if self.debug:
            print(f"outlet: {__name__} - body:")
            pprint(body)
            print(f"outlet: {__name__} - user:")
            pprint(user)
        return body

    def pipe(
        self, user_message: str, model_id: str, messages: List[dict], body: dict
    ) -> Union[str, Generator, Iterator]:
        print(f"pipe: {__name__}")

        if self.debug:
            print(f"pipe: {__name__} - received message from user: {user_message}")

        url = f"{self.api_endpoint}/api/v1/prediction/{self.chatflow_id}"
        headers = {"Content-Type": "application/json"}

        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"

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
