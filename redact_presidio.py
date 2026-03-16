from langfuse import Langfuse, observe

from dotenv import load_dotenv
from openai import OpenAI
import os
from presidio_analyzer import AnalyzerEngine
from presidio_anonymizer import AnonymizerEngine
from presidio_anonymizer.entities import OperatorConfig

# Initialize the 3rd-party engines once (outside the function)
analyzer = AnalyzerEngine()
anonymizer = AnonymizerEngine()

load_dotenv()

LITELLM_API_KEY = os.getenv("LITELLM_API_KEY")
LITELLM_BASE_URL = os.getenv("LITELLM_BASE_URL")
client = OpenAI(
    api_key=LITELLM_API_KEY,
    base_url=LITELLM_BASE_URL,
)
system_prompt = "You are a strong password generator tool"
query = """
        I am James Venn. My email is james@gmail.com, 
        my phone number is +91 9876543210, 
        and my credit card number is 4111 1111 1111 1111. 
        Can you generate a strong password for this email?
        Also, append my email at the end of password
        """

def redact_pii(data, **kwargs):
    print(data)
    """
    Uses Microsoft Presidio to detect and redact PII via NLP.
    Targeted at: {'args': (USER_PROMPT,), 'kwargs': {}}
    """
    # Guard Clause: Skip if data is None, not a dict, or missing 'args'
    if not isinstance(data, dict) or 'args' not in data:
        return data

    args = data.get('args')
    if isinstance(args, tuple) and len(args) > 0:
        prompt = args[0]
        
        if isinstance(prompt, str):
            # 1. Analyze text for PII (Names, Emails, Phones, etc.)
            results = analyzer.analyze(text=prompt, entities=None, language='en')
            
            # 2. Anonymize the findings
            # We can define specific operators (e.g., replace with [ENTITY_TYPE])
            anonymized_result = anonymizer.anonymize(
                text=prompt,
                analyzer_results=results,
                operators={
                    "EMAIL_ADDRESS": OperatorConfig("replace", {"new_value": "[EMAIL_REDACTED]"}),
                    "PERSON": OperatorConfig("replace", {"new_value": "[NAME]"}),
                    "DEFAULT": OperatorConfig("replace", {"new_value": "[PII_REDACTED]"}),
                }
            )
            
            # 3. Update the data structure
            new_prompt = anonymized_result.text
            data['args'] = (new_prompt,) + args[1:]

    return data

Langfuse(mask=redact_pii)

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