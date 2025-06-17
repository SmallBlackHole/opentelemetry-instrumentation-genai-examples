# pip install openai-agents logfire
import os
from agents import Agent, Runner, set_trace_processors, set_default_openai_client, set_tracing_disabled
import asyncio
import logfire
from agents import Agent, Runner, function_tool


@function_tool
def get_weather(city: str) -> str:
    return f"The weather in {city} is sunny."


agent = Agent(
    name="Hello world",
    instructions="You are a helpful agent.",
    tools=[get_weather],
)


async def main():
    result = await Runner.run(agent, input="What's the weather in Tokyo?")
    print(result.final_output)
    # The weather in Tokyo is sunny.


if __name__ == "__main__":
    # Configure OpenTelemetry endpoint (use HTTP port 4318)
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://localhost:4318/v1/traces"

    # Configure Logfire
    logfire.configure(
        service_name='openai_agent_with_tool',
        send_to_logfire=False,
        distributed_tracing=True,
    )

    # Instrument OpenAI Agents
    logfire.instrument_openai_agents()
    asyncio.run(main()) 