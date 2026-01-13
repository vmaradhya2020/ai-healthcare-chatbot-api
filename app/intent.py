from enum import Enum
import os
import openai
from typing import Optional

_client: Optional[openai.AsyncOpenAI] = None


def get_openai_client() -> Optional[openai.AsyncOpenAI]:
    global _client
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        return None
    if _client is None:
        try:
            _client = openai.AsyncOpenAI(api_key=api_key)
        except Exception:
            _client = None
    return _client

class Intents(str, Enum):
    """
    Enum for the different intents the chatbot can recognize.
    """
    ORDER_STATUS = "order_status"
    PRODUCT_SPECS = "product_specifications"
    SCHEDULING = "scheduling_maintenance"
    WARRANTY_AMC = "warranty_amc_queries"
    COMPLAINT = "complaint_registration"
    PAYMENT_INVOICE = "payment_invoice_queries"
    SPARE_PARTS = "spare_parts_accessories"
    CERTIFICATIONS = "certifications_compliance"
    GENERAL_QUERIES = "general_queries"
    UNKNOWN = "unknown"

# Create a dynamic list of intent values for the prompt
INTENT_LIST = [intent.value for intent in Intents if intent != Intents.UNKNOWN]

SYSTEM_PROMPT = f"""
You are an expert intent detection system for a customer support chatbot in a medical equipment company. 
Your task is to classify the user's message into one of the following predefined categories.
Respond with ONLY the category name.

Available categories:
{', '.join(INTENT_LIST)}

User message:
"""

async def classify_intent(message: str) -> Intents:
    """
    Classifies the user's message into one of the predefined intents using OpenAI when available,
    otherwise falls back to a simple keyword heuristic.
    """
    client = get_openai_client()
    if client is not None:
        try:
            response = await client.chat.completions.create(
                model="gpt-4o",
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": message}
                ],
                temperature=0,
                max_tokens=50,
            )
            intent_str = response.choices[0].message.content.strip()
            for intent in Intents:
                if intent.value == intent_str:
                    return intent
        except Exception as e:
            print(f"Error classifying intent: {e}")

    # Heuristic fallback
    text = message.lower()
    if any(k in text for k in ["order", "delivery", "tracking", "ship"]):
        return Intents.ORDER_STATUS
    if any(k in text for k in ["spec", "specification", "model", "feature"]):
        return Intents.PRODUCT_SPECS
    if any(k in text for k in ["install", "schedule", "maintenance", "service"]):
        return Intents.SCHEDULING
    if any(k in text for k in ["warranty", "amc", "coverage"]):
        return Intents.WARRANTY_AMC
    if any(k in text for k in ["complaint", "issue", "problem", "ticket"]):
        return Intents.COMPLAINT
    if any(k in text for k in ["invoice", "payment", "bill", "paid"]):
        return Intents.PAYMENT_INVOICE
    if any(k in text for k in ["spare", "part", "accessor"]):
        return Intents.SPARE_PARTS
    if any(k in text for k in ["certificate", "compliance", "iso", "ce"]):
        return Intents.CERTIFICATIONS
    if any(k in text for k in ["help", "info", "question", "general", "support"]):
        return Intents.GENERAL_QUERIES
    return Intents.UNKNOWN
