
import sys
import json
import asyncio
import websockets
import getpass
import os
import logging

from mapa import Map
from ai_agent import AI_Agent

# Next 2 lines are not needed for AI agent
import pygame

pygame.init()

wslogger = logging.getLogger("websockets")
wslogger.setLevel(logging.WARN)

async def agent_loop(server_address="localhost:8000", agent_name="ai_agent"):
    async with websockets.connect(f"ws://{server_address}/player") as websocket:

        # Receive information about static game properties
        await websocket.send(json.dumps({"cmd": "join", "name": agent_name}))
        msg = await websocket.recv()
        game_properties = json.loads(msg)

        ai = AI_Agent(game_properties)

        while True:
            try:
                state = json.loads(await websocket.recv())  # receive game state, this must be called timely or your game will get out of sync with the server

                ai.next_move(state)
                
            except websockets.exceptions.ConnectionClosedOK:
                print("Server has cleanly disconnected us")
                return

# DO NOT CHANGE THE LINES BELLOW
# You can change the default values using the command line, example:
# $ NAME='bombastico' python3 client.py
loop = asyncio.get_event_loop()
SERVER = os.environ.get("SERVER", "localhost")
PORT = os.environ.get("PORT", "8000")
NAME = os.environ.get("NAME", getpass.getuser())
loop.run_until_complete(agent_loop(f"{SERVER}:{PORT}", NAME))
