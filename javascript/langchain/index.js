/** Set up for OpenTelemetry tracing **/
const { initialize } = require("@traceloop/node-server-sdk");
initialize({
    appName: "opentelemetry-instrumentation-langchain-traceloop",
    baseUrl: "http://localhost:4318",
    disableBatch: true,
});
/** Set up for OpenTelemetry tracing **/

const { ChatOpenAI } = require("@langchain/openai");

async function main() {
    const llm = new ChatOpenAI({ model: "phi3", temperature: 0, configuration: { baseURL: "http://localhost:11434/v1" }, openAIApiKey: "unused" });
    const aiMsg = await llm.invoke([
    {
        role: "system",
        content:
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    },
    {
        role: "user",
        content: "I love programming.",
    },
    ]);
    console.log(aiMsg);
}

main();