import json
import os
import tempfile
import time
import uuid
from html import escape

import streamlit as st
from openai import OpenAI
from streamlit_stl import stl_from_file

from components.parameter_ui import show_parameter_sliders
from utils.dataloader import log_message


# Initialize the OpenAI client with a fixed API key.
client = OpenAI(
    api_key="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"
)


def call_openai_chat(messages, data, model="gpt-4o"):
    """
    Calls the OpenAI Chat Completions API with the conversation messages.

    - Prepends a system prompt (from data['system_prompt']) to the provided messages.
    - Uses temperature=0 for deterministic output.
    - Returns the assistant's text content, or an error string if the call fails.
    """
    try:
        messages = [{"role": "system", "content": data["system_prompt"]}] + messages
        resp = client.chat.completions.create(
            model=model,
            messages=messages,
            temperature=0,
        )
        return resp.choices[0].message.content
    except Exception as e:
        return f"OpenAI API Error: {e}"


def handle_user_input(data):
    """
    Renders a custom HTML/CSS chat UI in Streamlit, handles user input, and manages
    a two-step LLM interaction flow with a typing indicator placeholder.

    Session state keys used:
    - messages: list of chat message dicts (role/type/content/etc.)
    - initialized: ensures the greeting is added once
    - pending_llm: holds pending user input until the next run triggers the LLM call
    - processing_input: indicates a request is in progress (typing placeholder shown)
    """
    # --- Session init ---
    if "messages" not in st.session_state:
        st.session_state["messages"] = []
    if "initialized" not in st.session_state:
        st.session_state["initialized"] = False
    if "pending_llm" not in st.session_state:
        st.session_state["pending_llm"] = None
    if "processing_input" not in st.session_state:
        st.session_state["processing_input"] = False

    # Add an opening assistant message exactly once.
    if not st.session_state["initialized"]:
        if not st.session_state["messages"]:
            st.session_state["messages"].append(
                {
                    "id": str(uuid.uuid4()),
                    "role": "assistant",
                    "type": "text",
                    "content": "Hello! I am Lattice Genie. Ask me to recommend a lattice structure.",
                }
            )
        st.session_state["initialized"] = True

    # ---------- CSS (no avatars; user messages flush-right) ----------
    # Includes animated typing dots, injected as raw HTML in a placeholder message.
    st.markdown(
        """
        <style>
        .chat-wrapper { width:100%; max-width:900px; margin:8px auto; display:flex; flex-direction:column; }
        .chat-box {
            border:1px solid #444;
            border-radius:12px;
            background:#2e2e2e;
            padding:12px;
            height:420px;
            overflow-y:auto;
            display:flex;
            flex-direction:column;
            gap:8px;
            box-sizing:border-box;
        }
        .message {
            max-width:75%;
            padding:10px 14px;
            border-radius:12px;
            font-size:17px;
            line-height:1.4;
            word-wrap:break-word;
            color:#ffffff;
            display:inline-block;
        }
        .user { margin-left:auto; background-color:#7324B9; text-align:right; }
        .assistant { margin-right:auto; background-color:#3f51b5; text-align:left; }
        .stl-wrapper {display:block; margin-top:6px; margin-bottom:6px; }
        .stChatInputWrapper { margin-top: -6px; } /* visually attach native chat_input */

        /* animated typing dots (these are in-message HTML) */
        .typing-dots { display:flex; gap:6px; align-items:center; justify-content:flex-end; margin-top:6px; }
        .typing-dots .dot { width:10px; height:10px; border-radius:50%; background:#cfe9ff; opacity:0.25; animation:typing-blink 1s infinite ease-in-out; transform-origin:center; }
        .typing-dots .dot:nth-child(1){ animation-delay:0s; }
        .typing-dots .dot:nth-child(2){ animation-delay:0.15s; }
        .typing-dots .dot:nth-child(3){ animation-delay:0.3s; }
        @keyframes typing-blink {
          0% { transform: translateY(0); opacity:0.25; }
          30% { transform: translateY(-6px); opacity:1; }
          60% { transform: translateY(0); opacity:0.6; }
          100% { transform: translateY(0); opacity:0.25; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )

    # --- Render chat wrapper and messages (all inside chat-box) ---
    st.markdown('<div class="chat-wrapper">', unsafe_allow_html=True)

    messages_html = '<div class="chat-box" id="chat-box">'
    # Build simple HTML for text messages only; STL handled via stl_from_file below in order.
    for msg in st.session_state["messages"]:
        role = msg.get("role", "assistant")
        css_class = "user" if role == "user" else "assistant"
        ph = st.empty()
        with ph.container():
            # If this is a typing placeholder message (msg['typing'] == True),
            # render its raw HTML content (not escaped).
            if msg.get("type", "text") == "text":
                if msg.get("typing", False):
                    # content contains HTML for dots; insert raw
                    content_html = msg.get("content", "")
                    messages_html += (
                        f'<div class="message {css_class}">{content_html}</div>'
                    )
                else:
                    content = escape(msg.get("content", ""))
                    messages_html += f'<div class="message {css_class}">{content}</div>'
    messages_html += "</div>"

    # Auto-scroll to bottom after render.
    messages_html += """
    <script>
    const box = document.getElementById('chat-box');
    if (box) { box.scrollTop = box.scrollHeight; }
    </script>
    """
    st.markdown(messages_html, unsafe_allow_html=True)

    # --- Native Streamlit chat_input (do NOT change this key elsewhere) ---
    user_input = st.chat_input(
        "Ask Lattice Genie to recommend a structure",
        key="user_chat_input",
    )
    # Download button directly under the STL viewer (same flow)

    # Step 1:
    # If the user submitted text, append it immediately and mark pending LLM
    # for follow-up processing on the next run.
    if user_input and st.session_state["pending_llm"] is None:
        # Prevent accidental duplicate if last message already equals this user_input.
        is_dup = False
        if st.session_state["messages"]:
            last = st.session_state["messages"][-1]
            if last.get("role") == "user" and last.get("content") == user_input:
                is_dup = True

        if not is_dup:
            # Immediately show the user's message.
            st.session_state["messages"].append(
                {
                    "id": str(uuid.uuid4()),
                    "role": "user",
                    "type": "text",
                    "content": user_input,
                }
            )
            log_message("user", user_input)

        # Register pending LLM processing (we'll do it on the next run).
        st.session_state["pending_llm"] = {"input": user_input}

        # Rerun so the UI updates immediately with the user's message visible.
        st.rerun()

    # Step 2:
    # If there is pending work and we're not already processing it, do the LLM
    # call setup now by appending a typing placeholder message and rerunning
    # so the dots appear inside the chat box.
    if (
        st.session_state["pending_llm"] is not None
        and not st.session_state["processing_input"]
    ):
        st.session_state["processing_input"] = True
        pending = st.session_state["pending_llm"]
        user_text = pending.get("input", "")

        # Append an assistant placeholder message that contains the animated
        # dots HTML and mark typing=True.
        typing_html = (
            '<div class="typing-dots" style="justify-content:flex-end;">'
            '<div class="dot"></div><div class="dot"></div><div class="dot"></div>'
            "</div>"
        )
        st.session_state["messages"].append(
            {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "type": "text",
                "content": typing_html,
                "typing": True,
            }
        )

        # Rerun so the typing dots appear immediately inside the chat box.
        st.rerun()

    # Next run:
    # Detect the typing placeholder and perform the LLM call, then replace the
    # placeholder with the assistant reply.
    if st.session_state["processing_input"] and st.session_state["messages"]:
        last_msg = st.session_state["messages"][-1]
        if last_msg.get("role") == "assistant" and last_msg.get("typing", False):
            pending = st.session_state.get("pending_llm") or {}
            user_text = pending.get("input", "")

            # Call the LLM (blocking).
            assistant_reply = call_openai_chat(st.session_state["messages"], data)

            msg_to_display, gen_struc = process_assistant_response(
                assistant_reply,
                data,
            )

            # Replace the typing placeholder with the real assistant reply (plain text).
            st.session_state["messages"][-1] = {
                "id": str(uuid.uuid4()),
                "role": "assistant",
                "type": "text",
                "content": msg_to_display,
            }
            log_message("assistant", msg_to_display)

            # Clear pending and processing flags.
            st.session_state["pending_llm"] = None
            st.session_state["processing_input"] = False

            # Rerun to render the assistant reply (the typing HTML is gone now).
            st.rerun()


def process_assistant_response(assistant_msg, data):
    """
    Attempts to parse a JSON object embedded inside the assistant message.

    - Finds the first '{' and last '}' and tries to json.loads that substring.
    - If 'dict_key' is present, uses it to look up a parameter schema in
      data["params_dict"] and builds a confirmed parameter dict using defaults.
    - Stores confirmed params in st.session_state['confirmed_params'].

    Returns:
    - ("⬅️ Adjust parameters in the sidebar", 1) if confirmation succeeded
    - (assistant_msg, 0) otherwise
    """
    start = assistant_msg.find("{")
    end = assistant_msg.rfind("}")
    confirmed = False
    params_dict = data["params_dict"]

    if start != -1 and end != -1 and end > start:
        try:
            parsed = json.loads(assistant_msg[start : end + 1])
            dict_key = parsed.get("dict_key")
            if dict_key is not None:
                schema = params_dict.get(int(dict_key), {})
                base = {"dict_key": dict_key}
                for k, cfg in schema.items():
                    base[k] = cfg["default"]
                st.session_state["confirmed_params"] = base
                confirmed = True
        except json.JSONDecodeError:
            pass

    if confirmed:
        return "⬅️ Adjust parameters in the sidebar", 1

    return assistant_msg, 0
