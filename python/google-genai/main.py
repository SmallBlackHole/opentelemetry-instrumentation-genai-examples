import os

### Set up for OpenTelemetry tracing ###
from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

resource = Resource(attributes={
    "service.name": "opentelemetry-instrumentation-google-genai"
})
provider = TracerProvider(resource=resource)
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4318/v1/traces",
)
processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

# from azure.monitor.opentelemetry import configure_azure_monitor
# configure_azure_monitor(connection_string=os.environ.get("AI_CONNECTION_STRING"))

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