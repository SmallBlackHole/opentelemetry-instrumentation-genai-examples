const { context } = require("@opentelemetry/api");

const { AIProjectClient } = require("@azure/ai-projects");
const { DefaultAzureCredential } = require("@azure/identity");

async function main() {
    const endpoint = process.env["AZURE_AI_FOUNDRY_PROJECT_ENDPOINT"];
    const project = new AIProjectClient(endpoint, new DefaultAzureCredential());
    project.enableTelemetry(destination="http://localhost:4317");
    const client = project.inference.chatCompletions({
        apiVersion: "2024-05-01-preview",
    });
    const response = await client.post({
        body: {
        model: "gpt-4.1",
        messages: [
            { role: "system", content: "You are a helpful assistant. You will talk like a pirate." }, // System role not supported for some models
            { role: "user", content: "How many feet are in a mile?" },
        ],
        },
        tracingOptions: { tracingContext: context.active() },
    });
    console.log("response = ", JSON.stringify(response, null, 2));
}

main();