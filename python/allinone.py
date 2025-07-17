from dotenv import load_dotenv
load_dotenv()
import sys
import os
import anthropic
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"
os.environ["AZURE_SDK_TRACING_IMPLEMENTATION"] = "opentelemetry"

### Set up for OpenTelemetry tracing ###
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

def test_anthropic():
    from opentelemetry.instrumentation.anthropic import AnthropicInstrumentor
    AnthropicInstrumentor().instrument()

    name = "anthropic (python, traceloop)"
    with trace.get_tracer(name).start_as_current_span(name):
        client = anthropic.Anthropic(
            api_key=os.environ["ANTHROPIC_API_KEY"],
        )

        response = client.messages.create(
            max_tokens=1000,
            model='claude-3-haiku-20240307',
            system='You are a helpful assistant.',
            messages=[{'role': 'user', 'content': 'Please write me a limerick about Python logging.'}],
        )
        print(response.content[0].text)

def test_foundry_agents():
    from opentelemetry import trace
    from azure.ai.agents.telemetry import AIAgentsInstrumentor
    AIAgentsInstrumentor().instrument(True)
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
        endpoint=os.environ["PROJECT_ENDPOINT"],
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


    with tracer.start_as_current_span("foundry_agents"):
        with project_client:
            agents_client = project_client.agents

            agents_client.enable_auto_function_calls(toolset)

            agent = agents_client.create_agent(
                model="gpt-4.1-mini",
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

def test_azure_ai_inference():
    from azure.ai.inference import ChatCompletionsClient
    from azure.ai.inference.models import UserMessage
    from azure.ai.inference.models import TextContentItem
    from azure.core.credentials import AzureKeyCredential

    with trace.get_tracer("azure_ai_inference").start_as_current_span("azure_ai_inference"):
        client = ChatCompletionsClient(
            endpoint = "https://models.inference.ai.azure.com",
            credential = AzureKeyCredential(os.environ["GITHUB_TOKEN"]),
            api_version = "2024-08-01-preview",
        )

        response = client.complete(
            messages = [
                UserMessage(content = [
                    TextContentItem(text = "hi"),
                ]),
            ],
            model = "gpt-4o",
            tools = [],
            response_format = "text",
            temperature = 1,
            top_p = 1,
        )

        print(response.choices[0].message.content)

def test_google_genai():
    from opentelemetry.instrumentation.google_genai import GoogleGenAiSdkInstrumentor
    GoogleGenAiSdkInstrumentor().instrument(enable_content_recording=True)
    ### Set up for OpenTelemetry tracing ###

    with trace.get_tracer("google-genai (python)").start_as_current_span("google-genai (python)"):
        from google.genai import Client
        client = Client(
            api_key=os.environ["GOOGLE_GENAI_KEY"],
        )
        response = client.models.generate_content(
            model="gemini-2.0-flash",
            contents="Write a short poem on OpenTelemetry.", config={"temperature": 0.9})
        print(response)

def test_openai():
    from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
    OpenAIInstrumentor().instrument()
    import openai
    with trace.get_tracer("openai").start_as_current_span("openai"):
        client = openai.Client(
            base_url='http://localhost:11434/v1',
            api_key='unused'
        )

        response = client.chat.completions.create(
            model='phi3',
            messages=[
                {'role': 'system', 'content': 'You are a helpful assistant.'},
                {'role': 'user', 'content': 'Please write me a limerick about Python logging.'},
            ],
        )
        print(response.choices[0].message)

if __name__ == "__main__":
    trace_method = None
    if len(sys.argv) > 1:
        trace_method = sys.argv[1]
    if not trace_method:
        trace_method = os.environ.get("TRACE_METHOD", "local")
    if trace_method == "local":
        resource = Resource(attributes={
            "service.name": "all-in-one",
        })
        provider = TracerProvider(resource=resource)
        otlp_exporter = OTLPSpanExporter(
            endpoint="http://localhost:4318/v1/traces",
        )
        processor = BatchSpanProcessor(otlp_exporter)
        provider.add_span_processor(processor)
        trace.set_tracer_provider(provider)
    elif trace_method == "azure":
        from azure.monitor.opentelemetry import configure_azure_monitor
        configure_azure_monitor(connection_string=os.environ.get("AI_CONNECTION_STRING"))
    else:
        raise ValueError(f"Unknown trace method: {trace_method}")
    test_anthropic()
    test_foundry_agents()
    test_azure_ai_inference()
    test_google_genai()
    test_openai()