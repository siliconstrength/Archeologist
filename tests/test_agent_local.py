import asyncio
import os
from agent_deploy.agent import root_agent

async def main():
    prompt = "On 2026-01-05, user `carol_ops` raised an issue impacting the Marketing application. The AdWords tracking pixel is failing. I need you to cross-reference this"
    
    print("Testing locally...")
    async for event in root_agent.run_live(prompt):
        print(event)

asyncio.run(main())
