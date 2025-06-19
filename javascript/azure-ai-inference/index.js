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
        "service.name": "opentelemetry-instrumentation-azure-ai-inference",
    }),
    spanProcessors: [
        new SimpleSpanProcessor(exporter)
    ],
});
provider.register();

const { registerInstrumentations } = require("@opentelemetry/instrumentation");
const { createAzureSdkInstrumentation } = require("@azure/opentelemetry-instrumentation-azure-sdk");

registerInstrumentations({
  instrumentations: [createAzureSdkInstrumentation()],
});
/** Set up for OpenTelemetry tracing **/

const { AzureKeyCredential } = require("@azure/core-auth");
const ModelClient  = require("@azure-rest/ai-inference").default;

async function main() {
    const endpoint = "https://models.inference.ai.azure.com";
    const credential = new AzureKeyCredential(process.env["GITHUB_TOKEN"]);
    const client = ModelClient(endpoint, credential);

    const messages = [
    { role: "user", content: "hi" },
    ];

    const response = await client.path("/chat/completions").post({
        body: {
            model: "gpt-4o-mini",
            messages,
            stream: false,
        },
        /** Set up for OpenTelemetry tracing **/
        tracingOptions: { tracingContext: context.active() },
        /** Set up for OpenTelemetry tracing **/
    });
    console.log(response.body.choices);
}

main();