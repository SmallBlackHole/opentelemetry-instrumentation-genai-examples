# pip install azure-ai-inference[opentelemetry]
# pip install opentelemetry azure-core-tracing-opentelemetry opentelemetry-sdk opentelemetry-exporter-otlp
import os
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor, BatchSpanProcessor, ConsoleSpanExporter

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import SystemMessage, UserMessage, CompletionsFinishReason
from azure.core.credentials import AzureKeyCredential

# Set to 'true' for detailed traces, including chat request and response messages.
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"
# Optiona: only needed if you want to use Azure Monitor tracing
# os.environ["AI_CONNECTION_STRING"] = "<YOUR_AI_CONNECTION_STRING>"  # Replace with your Application Insights connection string

from azure.core.settings import settings
settings.tracing_implementation = "opentelemetry"

if not os.environ.get("REMOTE_TRACING"):
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource
    resource = Resource(attributes={SERVICE_NAME: "az-ai-inference-with-tools"})

    # Setup tracing to console
    span_exporter = ConsoleSpanExporter()
    tracer_provider = TracerProvider(resource=resource)
    tracer_provider.add_span_processor(SimpleSpanProcessor(span_exporter))
    trace.set_tracer_provider(tracer_provider)

    # Setup tracing to OTLP endpoint
    from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
    otlp_exporter = OTLPSpanExporter(endpoint="http://localhost:4317", insecure=True)
    trace.get_tracer_provider().add_span_processor(
        BatchSpanProcessor(otlp_exporter)
    )

    # Start instrument inferencing
    from azure.ai.inference.tracing import AIInferenceInstrumentor
    AIInferenceInstrumentor().instrument()
else:
    from azure.monitor.opentelemetry import configure_azure_monitor
    configure_azure_monitor(connection_string=os.environ.get("AI_CONNECTION_STRING"))

scenario = os.path.basename(__file__)
tracer = trace.get_tracer(__name__)

def get_temperature(city: str) -> str:
    # Adding attributes to the current span
    span = trace.get_current_span()
    span.set_attribute("requested_city", city)

    if city == "Seattle":
        return "75"
    elif city == "New York City":
        return "80"
    else:
        return "Unavailable"

def get_weather(city: str) -> str:
    if city == "Seattle":
        return "Nice weather"
    elif city == "New York City":
        return "Good weather"
    else:
        return "Unavailable"

def chat_completion_with_function_call(key, endpoint):
    import json
    from azure.ai.inference.models import (
        ToolMessage,
        AssistantMessage,
        ChatCompletionsToolCall,
        ChatCompletionsToolDefinition,
        FunctionDefinition,
    )

    weather_description = ChatCompletionsToolDefinition(
        function=FunctionDefinition(
            name="get_weather",
            description="Returns description of the weather in the specified city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city for which weather info is requested",
                    },
                },
                "required": ["city"],
            },
        )
    )

    temperature_in_city = ChatCompletionsToolDefinition(
        function=FunctionDefinition(
            name="get_temperature",
            description="Returns the current temperature for the specified city",
            parameters={
                "type": "object",
                "properties": {
                    "city": {
                        "type": "string",
                        "description": "The name of the city for which temperature info is requested",
                    },
                },
                "required": ["city"],
            },
        )
    )

    client = ChatCompletionsClient(endpoint=endpoint, credential=AzureKeyCredential(key), model="gpt-4.1")
    messages = [
        SystemMessage("You are a helpful assistant."),
        UserMessage("What is the weather and temperature in Seattle?"),
    ]

    response = client.complete(messages=messages, tools=[weather_description, temperature_in_city], model="gpt-4.1")

    if response.choices[0].finish_reason == CompletionsFinishReason.TOOL_CALLS:
        # Append the previous model response to the chat history
        messages.append(AssistantMessage(tool_calls=response.choices[0].message.tool_calls))
        # The tool should be of type function call.
        if response.choices[0].message.tool_calls is not None and len(response.choices[0].message.tool_calls) > 0:
            for tool_call in response.choices[0].message.tool_calls:
                if type(tool_call) is ChatCompletionsToolCall:
                    function_args = json.loads(tool_call.function.arguments.replace("'", '"'))
                    print(f"Calling function `{tool_call.function.name}` with arguments {function_args}")
                    callable_func = globals()[tool_call.function.name]
                    function_response = callable_func(**function_args)
                    print(f"Function response = {function_response}")
                    # Provide the tool response to the model, by appending it to the chat history
                    messages.append(ToolMessage(function_response, tool_call_id=tool_call.id))
                    # With the additional tools information on hand, get another response from the model
            response = client.complete(messages=messages, tools=[weather_description, temperature_in_city])

    print(f"Model response = {response.choices[0].message.content}")


def main():
    try:
        # GitHub models endpoint and key
        endpoint = "https://models.inference.ai.azure.com"
        key = os.environ["GITHUB_TOKEN"]
    except KeyError:
        print("Missing environment variable 'AZURE_AI_CHAT_ENDPOINT' or 'AZURE_AI_CHAT_KEY'")
        print("Set them before running this sample.")
        exit()

    # with tracer.start_as_current_span(scenario):
    chat_completion_with_function_call(key, endpoint)

if __name__ == "__main__":
    main()