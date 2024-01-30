"""

Sample bot that wraps GPT-3.5-Turbo but makes responses use all-caps.

"""
from __future__ import annotations

import os
from dotenv import load_dotenv
from typing import AsyncIterable

import fastapi_poe as fp
import modal
from modal import Image, Stub, asgi_app
from weavel import create_poe_client
load_dotenv()

weavel = create_poe_client() # TODO

class GPT35TurboAllCapsBot(fp.PoeBot):
    async def get_response(
        self, request: fp.QueryRequest
    ) -> AsyncIterable[fp.PartialResponse]:
        responses = [] # TODO
        async for msg in fp.stream_request(
            request, "GPT-3.5-Turbo", request.access_key
        ):
            yield msg.model_copy(update={"text": msg.text.upper()})
            responses.append(msg) # TODO
        weavel.log(request, responses) # TODO
            

    async def get_settings(self, setting: fp.SettingsRequest) -> fp.SettingsResponse:
        return fp.SettingsResponse(allow_attachments=True, server_bot_dependencies={"GPT-3.5-Turbo": 1})


REQUIREMENTS = ["fastapi-poe==0.0.24", "python-dotenv", "weavel"]
image = Image.debian_slim().pip_install(*REQUIREMENTS)
stub = Stub("turbo-allcaps-poe")


@stub.function(
    image=image, 
    secret=[
        modal.Secret.from_name("POE_ACCESS_KEY"),
        modal.Secret.from_name("WEAVEL_API_KEY"),
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
