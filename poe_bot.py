"""

Sample bot that wraps GPT-3.5-Turbo but makes responses use all-caps.

"""
from __future__ import annotations

import os
from datetime import datetime, timezone
from dotenv import load_dotenv
from typing import AsyncIterable, List

import fastapi_poe as fp
from fastapi_poe.types import PartialResponse
import modal
from modal import Image, Stub, asgi_app
from weavel import create_client, WeavelClient # ADD THIS LINE
load_dotenv()

weavel: WeavelClient = create_client() # ADD THIS LINE

class GPT35TurboAllCapsBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        responses: List[PartialResponse] = [] # ADD THIS LINE to save stream responses
                
        trace = weavel.open_trace(
            user_id=request.user_id, 
            trace_id=request.conversation_id
        ) # ADD THIS LINE to create conversation(trace) instance
        
        trace.log_message(
            "user", 
            request.query[-1].content, 
            timestamp=datetime.fromtimestamp(request.query[-1].timestamp / 1000000, timezone.utc)
        ) # ADD THIS LINE to log user message
        
        async for msg in fp.stream_request(
            request, "GPT-3.5-Turbo", request.access_key
        ):
            yield msg.model_copy(update={"text": msg.text})
            responses.append(msg) # ADD THIS LINE to save stream responses
            
        trace.log_message(
            "assistant",
            "".join([response.text for response in responses]),
            timestamp=datetime.now(timezone.utc),
        ) # ADD THIS LINE to log bot message

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(allow_attachments=True, server_bot_dependencies={"GPT-3.5-Turbo": 1})

REQUIREMENTS = ["fastapi-poe", "python-dotenv", "weavel>=0.4.0"] # ADD "weavel>=0.4.0"
image = Image.debian_slim().pip_install(*REQUIREMENTS)
stub = Stub("turbo-allcaps-poe")


@stub.function(
    image=image, 
    secrets=[
        modal.Secret.from_name("POE_ACCESS_KEY"),
        modal.Secret.from_name("WEAVEL_API_KEY"), # ADD WEAVEL_API_KEY in modal.com secrets or .env file
    ]
)
@asgi_app()
def fastapi_app():
    bot = GPT35TurboAllCapsBot()
    # Optionally, provide your Poe access key here:
    # 1. You can go to https://poe.com/create_bot?server=1 to generate an access key.
    # 2. We strongly recommend using a key for a production bot to prevent abuse,
    # but the starter examples disable the key check for convenience.
    # 3. You can also store your access key on modal.com and retrieve it in this function
    # by following the instructions at: https://modal.com/docs/guide/secrets
    POE_ACCESS_KEY = os.environ["POE_ACCESS_KEY"]
    app = fp.make_app(bot, access_key=POE_ACCESS_KEY)
    # app = fp.make_app(bot, allow_without_key=True)
    return app
