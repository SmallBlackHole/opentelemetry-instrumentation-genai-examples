/** Set up for OpenTelemetry tracing **/
const { context } = require("@opentelemetry/api");
const { resourceFromAttributes } = require("@opentelemetry/resources");
const {
  NodeTracerProvider,
  SimpleSpanProcessor,
} = require("@opentelemetry/sdk-trace-node");
const { OTLPTraceExporter } = require('@opentelemetry/exporter-trace-otlp-proto');

const exporter = new OTLPTraceExporter({
    url: "http://localhost:4318/v1/traces",
});
const provider = new NodeTracerProvider({
    resource: resourceFromAttributes({
        "service.name": "opentelemetry-instrumentation-azure-ai-projects",
    }),
    spanProcessors: [
        new SimpleSpanProcessor(exporter),
    ],
});
provider.register();

const { registerInstrumentations } = require("@opentelemetry/instrumentation");
const { createAzureSdkInstrumentation } = require("@azure/opentelemetry-instrumentation-azure-sdk");

registerInstrumentations({
  instrumentations: [createAzureSdkInstrumentation()],
});
/** Set up for OpenTelemetry tracing **/

const { AIProjectClient } = require("@azure/ai-projects");
const { DefaultAzureCredential } = require("@azure/identity");

async function main() {
    const endpoint = process.env["AZURE_AI_FOUNDRY_PROJECT_ENDPOINT"];
    const project = new AIProjectClient(endpoint, new DefaultAzureCredential());
    const client = project.inference.chatCompletions({
        apiVersion: "2024-05-01-preview",
    });
    const response = await client.post({
        body: {
        model: "gpt-4.1-mini",
        messages: [
            { role: "system", content: "You are a helpful assistant. You will talk like a pirate." }, // System role not supported for some models
            { role: "user", content: "How many feet are in a mile?" },
        ],
        },
        /** Set up for OpenTelemetry tracing **/
        tracingOptions: { tracingContext: context.active() },
        /** Set up for OpenTelemetry tracing **/
    });
    console.log("response = ", JSON.stringify(response, null, 2));
}

main();