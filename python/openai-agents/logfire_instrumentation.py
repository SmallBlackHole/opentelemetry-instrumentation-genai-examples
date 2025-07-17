from agents import Agent, InputGuardrail, GuardrailFunctionOutput, Runner
from pydantic import BaseModel
import asyncio
import os

### Set up for OpenTelemetry tracing ###
import logfire
os.environ["OTEL_EXPORTER_OTLP_TRACES_ENDPOINT"] = "http://localhost:4318/v1/traces"
# os.environ["OPENAI_API_KEY"] = "unused"  # Set a dummy key since we're using a local server
logfire.configure(
    service_name="opentelemetry-instrumentation-openai-agents-logfire",
    send_to_logfire=False,
)
logfire.instrument_openai_agents()
### Set up for OpenTelemetry tracing ###

from agents import Agent, Runner, OpenAIChatCompletionsModel, AsyncOpenAI


# from agents import set_default_openai_key
# set_default_openai_key(os.environ["OPENAI_API_KEY"])

class HomeworkOutput(BaseModel):
    is_homework: bool
    reasoning: str

# Configure the model
model = OpenAIChatCompletionsModel( 
    model="qwen3",
    openai_client=AsyncOpenAI(base_url="http://localhost:11434/v1", api_key="unused")
)

guardrail_agent = Agent(
    name="Guardrail check",
    instructions="Check if the user is asking about homework.",
    output_type=HomeworkOutput,
    model=model,
)

math_tutor_agent = Agent(
    name="Math Tutor",
    handoff_description="Specialist agent for math questions",
    instructions="You provide help with math problems. Explain your reasoning at each step and include examples",
    model=model,
)

history_tutor_agent = Agent(
    name="History Tutor",
    handoff_description="Specialist agent for historical questions",
    instructions="You provide assistance with historical queries. Explain important events and context clearly.",
    model=model,
)


async def homework_guardrail(ctx, agent, input_data):
    result = await Runner.run(guardrail_agent, input_data, context=ctx.context)
    final_output = result.final_output_as(HomeworkOutput)
    return GuardrailFunctionOutput(
        output_info=final_output,
        tripwire_triggered=not final_output.is_homework,
    )

triage_agent = Agent(
    name="Triage Agent",
    instructions="You determine which agent to use based on the user's homework question",
    handoffs=[history_tutor_agent, math_tutor_agent],
    input_guardrails=[
        InputGuardrail(guardrail_function=homework_guardrail),
    ],
    model=model,
)

async def main():
    result = await Runner.run(triage_agent, "who was the first president of the united states?")
    print(result.final_output)

if __name__ == "__main__":
    asyncio.run(main())