import re
from langfuse import Langfuse, observe

from dotenv import load_dotenv
from openai import OpenAI
import os

load_dotenv()

LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL")
client = OpenAI(
    api_key=LITELLM_API_KEY,
    base_url=LITELLM_BASE_URL
)
system_prompt = "You are a strong password generator tool"
query = """
        I am James Venn. My email is james@gmail.com, 
        my phone number is +91 9876543210, 
        and my credit card number is 4111 1111 1111 1111. 
        Can you generate a strong password for this email?
        Also, append my email at the end of password
        """
PII_PATTERNS = {
    "EMAIL": r'[\w\.-]+@[\w\.-]+\.\w+',
    "PHONE": r'\b(?:\+?\d{1,3}[- ]?)?\(?\d{3}\)?[- ]?\d{3}[- ]?\d{4}\b',
    "CREDIT_CARD": r'\b(?:\d[ -]*?){13,19}\b'
}

# TODO:
# A function which receives input data in the format: {'args': (USER_PROMPT,), 'kwargs': {}} for LLM calls.
# All prompts must be redacted to remove PII (Personally Identifiable Information).
# NB: This function may be invoked for all telemetry data; ensure that only 
# relevant invocations are redacted and the rest are skipped.
# 1. Ensure data is in the dict format as we expect
# 2. Extract the prompt out
# 3. Iterate and update the Regex string for each cases in PII_PATTERNS by `re.sub(pattern, f"[{key}_REDACTED]", prompt)`
#
# Register the masking method by anonymous Langfuse instantiation 

@observe()
def run_llm(query):
    response = client.chat.completions.create(
        model="gpt-5-mini",
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": query}
        ]
    )

    return response.choices[0].message.content


print(run_llm(query))

# Flush events in short-lived applications
# langfuse.flush()