import os

### Set up for OpenTelemetry tracing ###
os.environ["AZURE_SDK_TRACING_IMPLEMENTATION"] = "opentelemetry"
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

resource = Resource(attributes={
    "service.name": "opentelemetry-instrumentation-azure-ai-agents"
})
provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4318/v1/traces",
)
processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

from azure.ai.agents.telemetry import AIAgentsInstrumentor
AIAgentsInstrumentor().instrument()
### Set up for OpenTelemetry tracing ###

from typing import Any, Callable, Set
import json

from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import (
    FunctionTool,
    ToolSet,
    ListSortOrder,
)
from azure.ai.agents.telemetry import trace_function

scenario = os.path.basename(__file__)
tracer = trace.get_tracer(__name__)

project_client = AIProjectClient(
    endpoint=os.environ["AZURE_AI_FOUNDRY_PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)

@trace_function()
def fetch_weather(location: str) -> str:
    mock_weather_data = {"New York": "Sunny, 25°C", "London": "Cloudy, 18°C", "Tokyo": "Rainy, 22°C"}

    span = trace.get_current_span()
    span.set_attribute("requested_location", location)

    weather = mock_weather_data.get(location, "Weather data not available for this location.")
    weather_json = json.dumps({"weather": weather})
    return weather_json


user_functions: Set[Callable[..., Any]] = {
    fetch_weather,
}

functions = FunctionTool(functions=user_functions)
toolset = ToolSet()
toolset.add(functions)


with tracer.start_as_current_span(scenario):
    with project_client:
        agents_client = project_client.agents

        agents_client.enable_auto_function_calls(toolset)

        agent = agents_client.create_agent(
            model="gpt-4.1",
            name="my-agent",
            instructions="You are a helpful agent",
            toolset=toolset,
        )
        print(f"Created agent, ID: {agent.id}")

        thread = agents_client.threads.create()
        print(f"Created thread, ID: {thread.id}")

        message = agents_client.messages.create(
            thread_id=thread.id,
            role="user",
            content="Hello, what is the weather in New York?",
        )
        print(f"Created message, ID: {message.id}")

        run = agents_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id, toolset=toolset)
        print(f"Run completed with status: {run.status}")

        agents_client.delete_agent(agent.id)
        print("Deleted agent")

        messages = agents_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
        for msg in messages:
            if msg.text_messages:
                last_text = msg.text_messages[-1]
                print(f"{msg.role}: {last_text.text.value}")