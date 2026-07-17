"""LLM call dispatcher. Logs every call to token_usage_logs."""
from groq import Groq
from flask import current_app
from app.extensions import db
from app.models.token_usage_log import TokenUsageLog

# Centralized model configuration to avoid hardcoding strings downstream
GROQ_MODEL = "openai/gpt-oss-120b"

def generate_reply(business_id: int, conversation_id: int, context_chunks: list, user_message: str) -> str:
    client = Groq(api_key=current_app.config["GROQ_API_KEY"])

    context_text = "\n\n".join(context_chunks) if context_chunks else "No relevant documents found."
    system_prompt = (
        "You are a helpful business assistant. Answer ONLY using the context below. "
        "If the answer isn't in the context, say you don't have that information.\n\n"
        f"Context:\n{context_text}"
    )

    # Call the Groq API using the updated model
    completion = client.chat.completions.create(
        model=GROQ_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ],
    )

    reply = completion.choices[0].message.content
    tokens_used = completion.usage.total_tokens if completion.usage else 0

    # Log token usage with the updated model string
    db.session.add(TokenUsageLog(
        business_id=business_id,
        conversation_id=conversation_id,
        model_used=GROQ_MODEL,
        tokens_used=tokens_used,
    ))
    db.session.commit()

    return reply