### Set up for OpenTelemetry tracing ###
from opentelemetry import trace, _logs
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk._logs import LoggerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk._logs.export import BatchLogRecordProcessor
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
import os
from opentelemetry import _events
from typing import Optional
os.environ["OTEL_LOGS_EXPORTER"] = "console"

resource = Resource(attributes={
    "service.name": "opentelemetry-instrumentation-openai"
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

from opentelemetry.instrumentation.openai_v2 import OpenAIInstrumentor
OpenAIInstrumentor().instrument()

### Set up for OpenTelemetry tracing ###

import os
import openai

with trace.get_tracer("openai").start_as_current_span("openai"):
    client = openai.Client(
        base_url='http://localhost:11434/v1',
        api_key='unused'
        # api_key=os.environ["OPENAI_API_KEY"],
    )

    response = client.chat.completions.create(
        model='phi3',
        messages=[
            {'role': 'system', 'content': 'You are a helpful assistant.'},
            {'role': 'user', 'content': 'Please write me a limerick about Python logging.'},
        ],
    )
    print(response.choices[0].message)