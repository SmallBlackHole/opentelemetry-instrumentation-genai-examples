import os

### Set up for OpenTelemetry tracing ###
os.environ["AZURE_TRACING_GEN_AI_CONTENT_RECORDING_ENABLED"] = "true"
os.environ["AZURE_SDK_TRACING_IMPLEMENTATION"] = "opentelemetry"

# from opentelemetry import trace
# from opentelemetry.sdk.resources import Resource
# from opentelemetry.sdk.trace import TracerProvider
# from opentelemetry.sdk.trace.export import BatchSpanProcessor
# from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# resource = Resource(attributes={
#     "service.name": "opentelemetry-instrumentation-azure-ai-inference"
# })
# provider = TracerProvider(resource=resource)
# otlp_exporter = OTLPSpanExporter(
#     endpoint="http://localhost:4318/v1/traces",
# )
# processor = BatchSpanProcessor(otlp_exporter)
# provider.add_span_processor(processor)
# trace.set_tracer_provider(provider)

# from azure.ai.inference.tracing import AIInferenceInstrumentor
# AIInferenceInstrumentor().instrument()
from azure.ai.projects import enable_telemetry
enable_telemetry(destination="http://localhost:4317")
### Set up for OpenTelemetry tracing ###

from azure.ai.inference import ChatCompletionsClient
from azure.ai.inference.models import UserMessage
from azure.ai.inference.models import TextContentItem
from azure.core.credentials import AzureKeyCredential

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
