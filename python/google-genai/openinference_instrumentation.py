import os

### Set up for OpenTelemetry tracing ###
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

# resource = Resource(attributes={
#     "service.name": "opentelemetry-instrumentation-google-genai-openinference"
# })
# provider = TracerProvider(resource=resource)
# otlp_exporter = OTLPSpanExporter(
#     endpoint="http://localhost:4318/v1/traces",
# )
# processor = BatchSpanProcessor(otlp_exporter)
# provider.add_span_processor(processor)
# trace.set_tracer_provider(provider)
from azure.monitor.opentelemetry import configure_azure_monitor
configure_azure_monitor(connection_string=os.environ.get("AI_CONNECTION_STRING"))

from openinference.instrumentation.google_genai import GoogleGenAIInstrumentor
GoogleGenAIInstrumentor().instrument()
### Set up for OpenTelemetry tracing ###

from google.genai import Client
client = Client(
    api_key=os.environ["GOOGLE_GENAI_KEY"],
)
response = client.models.generate_content(
    model="gemini-1.5-flash-002",
    contents="Write a short poem on OpenTelemetry.")
print(response)