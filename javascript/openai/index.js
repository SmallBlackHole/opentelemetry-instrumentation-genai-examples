/** Set up for OpenTelemetry tracing **/
const { initialize } = require("@traceloop/node-server-sdk");
initialize({
    appName: "opentelemetry-instrumentation-openai-traceloop",
    baseUrl: "http://localhost:4318",
    disableBatch: true,
});
/** Set up for OpenTelemetry tracing **/

const { OpenAI } = require("openai");

async function main() {
    const client = new OpenAI({baseURL: "http://localhost:11434/v1", apiKey: "unused"});
    const completion = await client.chat.completions.create({
        model: "phi3",
        messages: [
            {
                role: "user",
                content: "Write a one-sentence bedtime story about a unicorn.",
            },
        ],
    });

    console.log(completion.choices[0].message.content);
}

main();