# simple_function_call.py
import asyncio
import contextlib
from datetime import datetime
from threading import Thread
from typing import Optional
from uuid import uuid4

from uagents import Agent, Context, Protocol
from datetime import datetime
from uuid import uuid4
from uagents.setup import fund_agent_if_low
from uagents_core.contrib.protocols.chat import (
   ChatAcknowledgement,
   ChatMessage,
   EndSessionContent,
   StartSessionContent,
   TextContent,
   chat_protocol_spec,
)
# === your hosted agent address ===
TARGET = "agent1qvguu6dz0l66adu9czgawz2r3s8mvgm3awn5tn8wfxjmpq0mwwxcwtuqpm9"

# Use a stable seed so your client identity is constant (mailbox persists)
CLIENT_SEED = "fetch-fn-client-seed-v1"
client = Agent(
    name="fn-client",
    seed=CLIENT_SEED,
    mailbox=True,                # receive replies via Agentverse mailbox
    publish_agent_details=False, # caller doesn't need to be discoverable
)
chat_proto = Protocol(spec=chat_protocol_spec)

# async def _call_async(text: str, timeout: float = 30.0) -> str:
#     """
#     Send a ChatMessage to the hosted agent and return the first text reply.
#     Uses a tiny ephemeral uAgents client; NO Envelope usage.
#     """
#     loop = asyncio.get_running_loop()
#     fut: asyncio.Future[str] = loop.create_future()

#     client = Agent(
#         name="fn-client",
#         seed=CLIENT_SEED,
#         mailbox=True,                # receive replies via Agentverse mailbox
#         publish_agent_details=False, # caller doesn't need to be discoverable
#     )

#     @client.on_event("startup")
#     async def _startup(ctx: Context):
#         # Give mailbox a brief moment to initialize.
#         # On the very first run, open the inspector link printed in logs
#         # and click "Create mailbox" for fn-client, then re-run.
#         await asyncio.sleep(0.6)
#         await ctx.send(
#             TARGET,
#             ChatMessage(
#                 timestamp=datetime.now(),
#                 msg_id=uuid4(),
#                 content=[TextContent(type="text", text=text)],
#             ),
#         )

#     @client.on_message(ChatAcknowledgement)
#     async def _on_ack(ctx: Context, sender: str, msg: ChatAcknowledgement):
#         # optional: ctx.logger.debug(f"ack {msg.acknowledged_msg_id}")
#         pass

#     @client.on_message(ChatMessage)
#     async def _on_reply(ctx: Context, sender: str, msg: ChatMessage):
#         parts = [c.text for c in msg.content if isinstance(c, TextContent)]
#         if not fut.done():
#             fut.set_result(("\n".join(parts)).strip() or "<no text>")

#     task = asyncio.create_task(client.run_async())
#     try:
#         reply = await asyncio.wait_for(fut, timeout)
#         return reply
#     finally:
#         # Gentle shutdown; avoid deep await to sidestep Windows recursion on cancel
#         task.cancel()
#         with contextlib.suppress(Exception):
#             await asyncio.sleep(0)

# def call_agent(text: str, timeout: float = 60.0) -> str:
#     """
#     Synchronous function-call API. Safe to use from scripts or notebooks.
#     Works even if you're already inside an event loop (e.g., FastAPI) by
#     running the async part in a helper thread.
#     """
#     try:
#         # If there's already a running loop, offload to a thread.
#         asyncio.get_running_loop()
#         result_holder = {}
#         error_holder = {}

#         def runner():
#             try:
#                 result_holder["v"] = asyncio.run(_call_async(text, timeout))
#             except Exception as e:
#                 error_holder["e"] = e

#         t = Thread(target=runner, daemon=True)
#         t.start()
#         t.join()
#         if "e" in error_holder:
#             raise error_holder["e"]
#         return result_holder["v"]

#     except RuntimeError:
#         # No event loop; run directly.
#         return asyncio.run(_call_async(text, timeout))

# Utility function to wrap plain text into a ChatMessage
def create_text_chat(text: str, end_session: bool = False) -> ChatMessage:
    content = [TextContent(type="text", text=text)]
    return ChatMessage(
        timestamp=datetime.utcnow(),
        msg_id=uuid4(),
        content=content,
        )

@client.on_event('startup')
async def startup_handler(ctx : Context):
    ctx.logger.info(f'My name is {ctx.agent.name} and my address  is {ctx.agent.address}')
    await ctx.send(
                TARGET,
                ChatMessage(
                    timestamp=datetime.now(),
                    msg_id=uuid4(),
                    content=[TextContent(type="text", text="flgfdjngljdn")],
                ),
            )

@chat_proto.on_message(ChatMessage)
async def handle_message(ctx: Context, sender: str, msg: ChatMessage):
   ctx.logger.info(f"Received message from {sender}")
  
   # Always send back an acknowledgement when a message is received
   await ctx.send(sender, ChatAcknowledgement(timestamp=datetime.utcnow(), acknowledged_msg_id=msg.msg_id))


   # Process each content item inside the chat message
   for item in msg.content:
       # Marks the start of a chat session
       if isinstance(item, StartSessionContent):
           ctx.logger.info(f"Session started with {sender}")
      
       # Handles plain text messages (from another agent or ASI:One)
       elif isinstance(item, TextContent):
           ctx.logger.info(f"Text message from {sender}: {item.text}")
           print(f"Text message from {sender}: {item.text}")
           #Add your logic
           # Example: respond with a message describing the result of a completed task
           response_message = create_text_chat("Hello from Agent")
           await ctx.send(sender, response_message)


       # Marks the end of a chat session
       elif isinstance(item, EndSessionContent):
           ctx.logger.info(f"Session ended with {sender}")
       # Catches anything unexpected
       else:
           ctx.logger.info(f"Received unexpected content type from {sender}")

client.include(chat_proto, publish_manifest=True)

if __name__ == "__main__":
    client.run()
