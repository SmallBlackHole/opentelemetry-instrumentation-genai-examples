/** Set up for OpenTelemetry tracing **/
const { initialize } = require("@traceloop/node-server-sdk");
initialize({
    appName: "opentelemetry-instrumentation-anthropic-traceloop",
    baseUrl: "http://localhost:4318",
    disableBatch: true,
});
/** Set up for OpenTelemetry tracing **/

const Anthropic = require("@anthropic-ai/sdk");

const client = new Anthropic({ apiKey: process.env["ANTHROPIC_API_KEY"] });

async function main() {
  const message = await client.messages.create({
    max_tokens: 1024,
    messages: [{ role: "user", content: "Hello, Claude" }],
    model: "claude-3-5-sonnet-latest",
  });
  console.log(message.content);
}

main();