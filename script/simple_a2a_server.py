import uvicorn
from fastapi.middleware.cors import CORSMiddleware

from a2a.server.apps.jsonrpc.fastapi_app import A2AFastAPIApplication
from a2a.server.request_handlers import DefaultRequestHandler
from a2a.server.tasks import InMemoryTaskStore
from a2a.types import (
    AgentCapabilities,
    AgentCard,
    AgentSkill,
)
from a2a.server.agent_execution import AgentExecutor, RequestContext
from a2a.server.events import EventQueue
from a2a.utils.message import new_agent_text_message


class SimpleAgent:
    async def invoke(self) -> str:
        return 'Hi there!'


class SimpleAgentExecutor(AgentExecutor):
    def __init__(self):
        self.agent = SimpleAgent()

    async def execute(self, context: RequestContext, event_queue: EventQueue) -> None:
        result = await self.agent.invoke()
        await event_queue.enqueue_event(new_agent_text_message(result))

    async def cancel(self, context: RequestContext, event_queue: EventQueue) -> None:
        raise Exception('cancel not supported')


def main():
    skill = AgentSkill(
        id='simple_hello',
        name='Simple Hello',
        description='Returns a simple hello message',
        tags=['hello', 'simple'],
        examples=['say hello'],
    )

    agent_card = AgentCard(
        name='Simple A2A Agent',
        description='A minimal A2A agent server',
        url='http://localhost:8080/',
        version='1.0.0',
        defaultInputModes=['text'],
        defaultOutputModes=['text'],
        capabilities=AgentCapabilities(streaming=True),
        skills=[skill],
        supportsAuthenticatedExtendedCard=False,
    )

    request_handler = DefaultRequestHandler(
        agent_executor=SimpleAgentExecutor(),
        task_store=InMemoryTaskStore(),
    )

    server = A2AFastAPIApplication(
        agent_card=agent_card,
        http_handler=request_handler,
    )

    app = server.build()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # Change this to specific origins in production
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    uvicorn.run(app, host='0.0.0.0', port=8080)


if __name__ == '__main__':
    main() 