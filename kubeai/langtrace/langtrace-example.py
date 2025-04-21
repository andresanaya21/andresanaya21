# Replace this with your langtrace API key by visiting http://localhost:3000
langtrace_api_key="43e10292bbf279ba8f7f6bf5e8ab7699d957dbbac3835cd63c3eed3abbd66110"

from langtrace_python_sdk import langtrace
from langtrace_python_sdk.utils.with_root_span import with_langtrace_root_span
# Paste this code after your langtrace init function

from openai import OpenAI

langtrace.init(
    api_key=langtrace_api_key,
    api_host="http://localhost:3000/api/trace",
)

base_url = "http://localhost:8100/openai/v1"
model = "gemma2-2b-cpu"

@with_langtrace_root_span()
def example():
    client = OpenAI(base_url=base_url, api_key="ignored-by-kubeai")
    response = client.chat.completions.create(
        model=model,
        messages=[
            {
                "role": "system",
                "content": "How many states of matter are there?"
            }
        ],
    )
    print(response.choices[0].message.content)

example()
