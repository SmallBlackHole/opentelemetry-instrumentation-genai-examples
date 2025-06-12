import os

from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter

provider = TracerProvider()
otlp_exporter = OTLPSpanExporter(
    endpoint="http://localhost:4318/v1/traces",
)
processor = BatchSpanProcessor(otlp_exporter)
provider.add_span_processor(processor)
trace.set_tracer_provider(provider)

from opentelemetry.instrumentation.google_genai import GoogleGenAiSdkInstrumentor
from google.genai import Client

GoogleGenAiSdkInstrumentor().instrument()

client = Client(
    api_key=os.environ["GOOGLE_GENAI_KEY"],
)
response = client.models.generate_content(
    model="gemini-1.5-flash-002",
    contents="Write a short poem on OpenTelemetry.")
print(response)