import anthropic
import logfire
import os

os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://localhost:4318/v1/traces"
logfire.configure(
    service_name="test_anthropic_logfire",
    send_to_logfire=False,
)
logfire.instrument_anthropic()

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