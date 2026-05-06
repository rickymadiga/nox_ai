import streamlit as st
import base64
import json
from datetime import datetime

def show():
    st.title("💬 NOXChat")

    api = st.session_state.api

    # ✅ Ensure session state exists
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    if "current_files" not in st.session_state:
        st.session_state.current_files = {}

    if "last_response" not in st.session_state:
        st.session_state.last_response = None

    user = st.session_state.get("user", {})
    st.success(f"👤 {user.get('username', 'User')}")

    # -------------------------
    # INPUT FORM
    # -------------------------
    with st.form("chat_form"):
        prompt = st.text_area(
            "Enter prompt",
            key="chat_prompt",
            height=120,
            placeholder="Describe what you need help with..."
        )
        submit = st.form_submit_button("Send", use_container_width=True)

    if submit:
        if not prompt.strip():
            st.warning("⚠️ Please enter a prompt")
            return

        with st.spinner("⚙️ NOX thinking..."):
            try:
                res = api.chat(prompt)
            except Exception as e:
                st.error(f"❌ API Error: {str(e)}")
                return

        if not res:
            st.error("❌ No response from server")
            return

        # Error handling
        if isinstance(res, dict) and res.get("success") is False:
            st.error(f"❌ Error: {res.get('error', 'Unknown error')}")
            return

        if isinstance(res, dict) and res.get("detail"):
            st.error(f"❌ Error: {res.get('detail')}")
            return

        # ✅ Save response globally
        st.session_state.last_response = res

        # -------------------------
        # RESPONSE CORE
        # -------------------------
        st.markdown("### 🧠 Response")
        response_text = res.get("response", "No response")
        st.write(response_text)

        status = res.get("status", "unknown")
        response_type = res.get("type", "message")
        action = res.get("action", "chat")

        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"📊 Status: `{status}`")
        with col2:
            st.caption(f"📋 Type: `{response_type}`")
        with col3:
            st.caption(f"🎯 Action: `{action}`")

        # -------------------------
        # 🔧 CODE RESULT
        # -------------------------
        if response_type == "code_result":
            st.markdown("## 🔧 Fixed Code")

            updated_files = res.get("updated_files", {})

            if updated_files:
                st.session_state.current_files = updated_files
                st.info(f"✅ Updated {len(updated_files)} file(s)")

                for filename, code in updated_files.items():
                    with st.expander(f"📄 {filename}", expanded=True):
                        st.code(code, language="python")

                # ✅ Persist files for edit page
                st.session_state.current_files.update(updated_files)

            else:
                st.info("ℹ️ No files were modified")
            
            diffs = res.get("diffs", {})
            if diffs:
                with st.expander(f"🔍 Diffs ({len(diffs)} file(s))"):
                    for file, diff in diffs.items():
                        st.markdown(f"**{file}**")
                        st.code(diff, language="diff")

            if res.get("analysis"):
                st.markdown("## 🧠 Analysis")
                st.write(res["analysis"])

            if res.get("root_cause"):
                st.markdown("## 🎯 Root Cause")
                st.error(res["root_cause"])

            if res.get("summary"):
                st.markdown("## 📝 Summary")
                st.write(res["summary"])

        if updated_files:
            st.markdown("### ✏️ Edit Code")

            selected_file = st.selectbox(
                "Select file",
                list(updated_files.keys())
            )

            code = updated_files[selected_file]

            edited = st.text_area(
                "Edit code",
                value=code,
                height=300,
                key=f"edit_{selected_file}"
            )

            instruction = st.text_input("Instruction (e.g. fix bug, optimize)")

            if st.button("⚡ Apply AI Edit"):
                res = api.edit(
                    file=selected_file,
                    code=edited,
                    instruction=instruction
                )

                if res.get("updated_code"):
                    st.success("✅ Updated")
                    st.code(res["updated_code"], language="python")

        # -------------------------
# ✍️ INLINE EDITOR (CURSOR-STYLE)
# -------------------------
if "current_files" in st.session_state and st.session_state.current_files:

    st.markdown("## ✍️ Edit Files (AI + Manual)")

    files = st.session_state.current_files

    # File selector
    selected_file = st.selectbox(
        "Select file to edit",
        list(files.keys()),
        key="selected_file"
    )

    # Load current content
    file_content = files.get(selected_file, "")

    # Editable code area
    edited_code = st.text_area(
        f"Editing: {selected_file}",
        value=file_content,
        height=400,
        key=f"editor_{selected_file}"
    )

    # Save changes locally
    if st.button("💾 Apply Changes"):
        st.session_state.current_files[selected_file] = edited_code
        st.success(f"Updated {selected_file}")

    # -------------------------
    # 🤖 AI INLINE EDIT
    # -------------------------
    st.markdown("### 🤖 Ask AI about this file")

    ai_prompt = st.text_input(
        "What do you want to change?",
        placeholder="e.g. optimize this function, fix bug, add logging..."
    )

    if st.button("⚡ Run AI Edit"):
        if not ai_prompt.strip():
            st.warning("Enter a prompt for AI")
        else:
            with st.spinner("AI editing..."):
                try:
                    api = st.session_state.api
                    res = api.chat({
                        "prompt": ai_prompt,
                        "context": {
                            "mode_override": "fixer",
                            "files": st.session_state.current_files,
                            "active_file": selected_file
                        }
                    })

                    if res.get("updated_files"):
                        st.session_state.current_files.update(res["updated_files"])
                        st.success("AI applied changes")

                except Exception as e:
                    st.error(str(e))        

        # -------------------------
        # 📦 BUILD ZIP
        # -------------------------
        zip_data = res.get("zip")

        if zip_data:
            st.markdown("## 📦 Build Output")

            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("📁 Filename", zip_data.get("filename", "nox_app.zip"))
            with col2:
                size_bytes = zip_data.get("size", 0)
                size_mb = size_bytes / (1024 * 1024)
                st.metric("💾 Size", f"{size_mb:.2f} MB" if size_mb > 1 else f"{size_bytes:,} B")
            with col3:
                st.metric("📥 Status", "Ready")

            try:
                zip_b64 = zip_data.get("data", "")
                if zip_b64:
                    zip_bytes = base64.b64decode(zip_b64)

                    st.download_button(
                        label="⬇️ Download ZIP",
                        data=zip_bytes,
                        file_name=zip_data.get("filename", "nox_app.zip"),
                        mime="application/zip",
                        use_container_width=True
                    )
                else:
                    st.error("❌ ZIP data is empty")

            except Exception as e:
                st.error(f"❌ Error preparing download: {str(e)}")

        # -------------------------
        # 📜 LOGS
        # -------------------------
        logs = res.get("logs", [])

        if logs:
            with st.expander(f"📜 Execution Logs ({len(logs)} total)"):
                for log in logs[-50:]:
                    log_text = log.get("message") if isinstance(log, dict) else str(log)

                    if "error" in log_text.lower() or "❌" in log_text:
                        st.error(log_text)
                    elif "warning" in log_text.lower() or "⚠️" in log_text:
                        st.warning(log_text)
                    elif "success" in log_text.lower() or "✅" in log_text:
                        st.success(log_text)
                    else:
                        st.text(log_text)

        # -------------------------
        # 📊 ADDITIONAL DATA
        # -------------------------
        if res.get("chain"):
            with st.expander("🔗 Execution Chain"):
                st.json(res["chain"])

        if res.get("structured"):
            with st.expander("📊 Structured Data"):
                st.json(res["structured"])

        if res.get("intent"):
            st.info(f"💭 Intent: `{res['intent']}`")

        if res.get("confidence"):
            st.info(f"🎯 Confidence: `{res['confidence']:.1%}`")

        if res.get("price"):
            st.warning(f"💰 Estimated cost: {res['price']} credits")

        if res.get("plan"):
            with st.expander("📋 Execution Plan"):
                st.json(res["plan"])

        # -------------------------
        # 💾 SAVE HISTORY
        # -------------------------
        st.session_state.chat_history.append({
            "timestamp": datetime.now().isoformat(),
            "prompt": ai_prompt,
            "response": res
        })

    # -------------------------
    # 🧭 QUICK NAV TO EDIT PAGE
    # -------------------------
    if st.session_state.current_files:
        st.markdown("---")
        st.markdown("### 🛠️ Continue Editing")

        if st.button("Open Editor"):
            st.session_state.page = "edit"
            st.rerun()