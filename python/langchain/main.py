import os
os.environ["LANGSMITH_OTEL_ENABLED"] = "true"
os.environ["LANGSMITH_TRACING"] = "true"
os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4318"

from langchain_openai import ChatOpenAI
from langchain_core.prompts import ChatPromptTemplate

# Create a chain
prompt = ChatPromptTemplate.from_template("Tell me a joke about {topic}")
model = ChatOpenAI()
chain = prompt | model

# Run the chain
result = chain.invoke({"topic": "programming"})
print(result.content)