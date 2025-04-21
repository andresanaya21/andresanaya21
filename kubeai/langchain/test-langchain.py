from langchain_openai import ChatOpenAI

llm = ChatOpenAI(
    model="gemma2-2b-cpu",
    temperature=0,
    max_tokens=None,
    timeout=None,
    max_retries=2,
    api_key="thisIsIgnored",
    base_url="http://localhost:8100/openai/v1",
)

messages = [
    (
        "system",
        "You are a helpful assistant that translates English to French. Translate the user sentence.",
    ),
    ("human", "I love programming."),
]
ai_msg = llm.invoke(messages)
print(ai_msg.content)
