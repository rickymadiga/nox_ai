import streamlit as st
import requests
import time
from typing import Generator, Optional

API_URL = "http://localhost:8000/api/chat/message"


# ============================================================================
# CONFIG
# ============================================================================

REQUEST_TIMEOUT = 30
STREAM_DELAY = 0.01


# ============================================================================
# STREAMING UTIL (FALLBACK)
# ============================================================================

def fake_stream(text: str, delay: float = STREAM_DELAY) -> Generator[str, None, None]:
    """Fallback streaming when backend doesn't support streaming."""
    words = text.split()
    buffer = ""

    for word in words:
        buffer += word + " "
        yield buffer
        time.sleep(delay)


# ============================================================================
# API CALL (NORMAL)
# ============================================================================

def send_message(message: str) -> dict:
    """Standard API call."""
    try:
        response = requests.post(
            API_URL,
            json={"message": message},
            timeout=REQUEST_TIMEOUT
        )
        response.raise_for_status()
        return response.json()

    except requests.exceptions.RequestException as e:
        return {"error": str(e)}


# ============================================================================
# API CALL (STREAMING)
# ============================================================================

def stream_message(message: str) -> Generator[str, None, None]:
    """
    Try real streaming from backend.
    Backend must support chunked responses.
    """
    try:
        with requests.post(
            API_URL,
            json={"message": message},
            stream=True,
            timeout=REQUEST_TIMEOUT
        ) as response:

            for chunk in response.iter_content(chunk_size=1024):
                if chunk:
                    yield chunk.decode("utf-8")

    except Exception as e:
        yield f"\n\n❌ Streaming error: {str(e)}"


# ============================================================================
# RESPONSE PARSER
# ============================================================================

def parse_response(response: dict) -> tuple[str, str]:
    intent = response.get("intent", "unknown")
    result = response.get("response", {}).get("result", "")

    return intent, result


# ============================================================================
# CHAT UI
# ============================================================================

def render_chat():
    st.set_page_config(page_title="Smart Intent Chat", layout="centered")

    st.title("💬 Smart Intent Chat")

    # Debug toggle
    debug = st.sidebar.toggle("🛠 Debug Mode", False)

    # Session state init
    if "messages" not in st.session_state:
        st.session_state.messages = []

    # Render history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Input
    user_input = st.chat_input("Type your message...")

    if not user_input:
        return

    # Save user message
    st.session_state.messages.append({
        "role": "user",
        "content": user_input
    })

    with st.chat_message("user"):
        st.markdown(user_input)

    # Assistant response
    with st.chat_message("assistant"):
        placeholder = st.empty()
        status = st.status("Thinking...", expanded=False)

        # --- CALL BACKEND ---
        response = send_message(user_input)

        if "error" in response:
            status.update(label="Error", state="error")
            placeholder.error(response["error"])
            return

        intent, result = parse_response(response)

        full_text = f"**🧠 Intent:** `{intent}`\n\n{result}"

        # --- STREAM OUTPUT (fallback for now) ---
        streamed = ""
        for chunk in fake_stream(full_text):
            streamed = chunk
            placeholder.markdown(streamed)

        status.update(label="Done", state="complete")

        # Debug info
        if debug:
            with st.expander("🔍 Raw Response"):
                st.json(response)

        # Save assistant message
        st.session_state.messages.append({
            "role": "assistant",
            "content": full_text
        })

# ============================================================================
# LEGACY COMPATIBILITY (IMPORTANT)
# ============================================================================

def stream_output(text: str):
    """
    Backward-compatible function for existing UI imports.
    Streams text into a Streamlit placeholder.
    """
    placeholder = st.empty()
    streamed = ""

    for chunk in fake_stream(text):
        streamed = chunk
        placeholder.markdown(streamed)

    return streamed        


# ============================================================================
# ENTRY
# ============================================================================

def main():
    render_chat()


if __name__ == "__main__":
    main()