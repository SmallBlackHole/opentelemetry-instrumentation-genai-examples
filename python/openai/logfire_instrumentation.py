import openai
import logfire
import os

os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://localhost:4318/v1/traces"
logfire.configure(
    service_name="opentelemetry-instrumentation-openai-logfire",
    send_to_logfire=False,
)
logfire.instrument_openai()

client = openai.Client()

response = client.chat.completions.create(
    model='gpt-4o',
    messages=[
        {'role': 'system', 'content': 'You are a helpful assistant.'},
        {'role': 'user', 'content': 'Please write me a limerick about Python logging.'},
    ],
)
print(response.choices[0].message)