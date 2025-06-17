# pip install openai-agents logfire
import os
from agents import Agent, Runner, set_trace_processors, set_default_openai_client, set_tracing_disabled
import asyncio
import logfire

spanish_agent = Agent(
    name="Spanish agent",
    instructions="You only speak Spanish.",
)

english_agent = Agent(
    name="English agent",
    instructions="You only speak English",
)

triage_agent = Agent(
    name="Triage agent",
    instructions="Handoff to the appropriate agent based on the language of the request.",
    handoffs=[spanish_agent, english_agent],
)


async def main():
    result = await Runner.run(triage_agent, input="Hola, ¿cómo estás?")
    print(result.final_output)
    # ¡Hola! Estoy bien, gracias por preguntar. ¿Y tú, cómo estás?


if __name__ == "__main__":
    # Configure OpenTelemetry endpoint (use HTTP port 4318)
    os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://localhost:4318/v1/traces"

    # Configure Logfire
    logfire.configure(
        service_name='openai_agent_with_handoff',
        send_to_logfire=False,
        distributed_tracing=True
    )

    # Instrument OpenAI Agents
    logfire.instrument_openai_agents()
    
    asyncio.run(main())