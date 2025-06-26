from typing import Any, Callable, Set

import os, sys, time, json
from azure.core.settings import settings

settings.tracing_implementation = "opentelemetry"
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor, ConsoleSpanExporter
from azure.ai.projects import AIProjectClient
from azure.identity import DefaultAzureCredential
from azure.ai.agents.models import (
    FunctionTool,
    ToolSet,
    ListSortOrder,
    BingGroundingTool
)
from azure.ai.agents.telemetry import trace_function
from azure.ai.agents.telemetry import AIAgentsInstrumentor

# os.environ["PROJECT_ENDPOINT"] = "<YOUR_PROJECT_ENDPOINT>"  # Replace with your Azure AI Foundry project endpoint
os.environ["MODEL_DEPLOYMENT_NAME"] = "gpt-4.1"
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true" 
# Optional: only needed if you want to use Azure Monitor tracing
# os.environ["AI_CONNECTION_STRING"] = "<YOUR_AI_CONNECTION_STRING>"  # Replace with your Application Insights connection string

if not os.environ.get("REMOTE_TRACING"):
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    resource = Resource(attributes={SERVICE_NAME: "foundry-agent-with-tools"})

    # Setup tracing to console
    span_exporter = ConsoleSpanExporter()
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)
    tracer = trace.get_tracer(__name__)

    # Setup tracing to OTLP endpoint
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317")
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    # Start instrument AI agent
    AIAgentsInstrumentor().instrument()
else:
    from azure.monitor.opentelemetry import configure_azure_monitor
    application_insights_connection_string = os.environ["AI_CONNECTION_STRING"]
    configure_azure_monitor(connection_string=application_insights_connection_string)

scenario = os.path.basename(__file__)
tracer = trace.get_tracer(__name__)

project_client = AIProjectClient(
    endpoint=os.environ["PROJECT_ENDPOINT"],
    credential=DefaultAzureCredential(),
)


# The trace_func decorator will trace the function call and enable adding additional attributes
# to the span in the function implementation. Note that this will trace the function parameters and their values.
@trace_function()
def fetch_weather(location: str) -> str:
    """
    Fetches the weather information for the specified location.

    :param location (str): The location to fetch weather for.
    :return: Weather information as a JSON string.
    :rtype: str
    """
    # In a real-world scenario, you'd integrate with a weather API.
    # Here, we'll mock the response.
    mock_weather_data = {"New York": "Sunny, 25°C", "London": "Cloudy, 18°C", "Tokyo": "Rainy, 22°C"}

    # Adding attributes to the current span
    span = trace.get_current_span()
    span.set_attribute("requested_location", location)

    weather = mock_weather_data.get(location, "Weather data not available for this location.")
    weather_json = json.dumps({"weather": weather})
    return weather_json


# Statically defined user functions for fast reference
user_functions: Set[Callable[..., Any]] = {
    fetch_weather,
}

# Initialize function tool with user function
functions = FunctionTool(functions=user_functions)
toolset = ToolSet()
toolset.add(functions)

# conn_id = os.environ["AZURE_BING_CONNECTION_ID"]
# bing = BingGroundingTool(connection_id=conn_id)

with tracer.start_as_current_span(scenario + "(built-in tools)"):
    with project_client:
        agents_client = project_client.agents

        # To enable tool calls executed automatically
        agents_client.enable_auto_function_calls(toolset)

        # Create an agent and run user's request with function calls
        agent = agents_client.create_agent(
            model=os.environ["MODEL_DEPLOYMENT_NAME"],
            name="my-agent",
            instructions="You are a helpful agent",
            toolset=toolset,
            # tools=bing.definitions
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

        # run = agents_client.runs.create_and_process(thread_id=thread.id, agent_id=agent.id, toolset=toolset)
        # print(f"Run completed with status: {run.status}")

        # manually control the run for better debugging
        run = project_client.agents.runs.create(thread_id=thread.id, agent_id=agent.id)
        print(f"Created run, ID: {run.id}")

        # Poll the run status until it is completed or requires action
        while run.status in ["queued", "in_progress", "requires_action"]:
            time.sleep(1)
            run = project_client.agents.runs.get(thread_id=thread.id, run_id=run.id)

            if run.status == "requires_action":
                tool_calls = run.required_action.submit_tool_outputs.tool_calls
                tool_outputs = []
                for tool_call in tool_calls:
                    if tool_call.type == "function" and tool_call.function.name == "fetch_weather":
                        output = fetch_weather("New York")
                        tool_outputs.append({"tool_call_id": tool_call.id, "output": output})
                project_client.agents.runs.submit_tool_outputs(thread_id=thread.id, run_id=run.id, tool_outputs=tool_outputs)

        print(f"Run completed with status: {run.status}")

        # Delete the agent when done
        agents_client.delete_agent(agent.id)
        print("Deleted agent")

        # Fetch and log all messages
        messages = agents_client.messages.list(thread_id=thread.id, order=ListSortOrder.ASCENDING)
        for msg in messages:
            if msg.text_messages:
                last_text = msg.text_messages[-1]
                print(f"{msg.role}: {last_text.text.value}")