import streamlit as st

def show():
    st.title("🧠 NOX AI Editor")

    api = st.session_state.api
    files = st.session_state.get("current_files", {})

    if not files:
        st.warning("No files available")
        return

    selected_file = st.selectbox("📄 File", list(files.keys()))
    original_code = files[selected_file]

    # -------------------------
    # CODE EDITOR
    # -------------------------
    code = st.text_area(
        "Code",
        value=original_code,
        height=400,
        key=f"editor_{selected_file}"
    )

    # -------------------------
    # CURSOR SELECTION
    # -------------------------
    st.markdown("### 🎯 Select Region")

    col1, col2 = st.columns(2)
    with col1:
        start = st.number_input("Start Line", min_value=1, value=1)
    with col2:
        end = st.number_input("End Line", min_value=1, value=5)

    code_lines = code.split("\n")
    selected_block = "\n".join(code_lines[start-1:end])

    st.markdown("#### 🔍 Selected Code")
    st.code(selected_block, language="python")

    # -------------------------
    # INSTRUCTION
    # -------------------------
    instruction = st.text_input("💬 What should AI do?")

    # -------------------------
    # APPLY AI EDIT
    # -------------------------
    if st.button("⚡ Apply AI Edit"):
        with st.spinner("AI editing..."):

            res = api.edit({
                "file": selected_file,
                "code": code,
                "selection": selected_block,
                "instruction": instruction
            })

        patch = res.get("patch")
        updated_code = res.get("updated_code")

        if not updated_code:
            st.error("No changes returned")
            return

        # -------------------------
        # PREVIEW DIFF
        # -------------------------
        st.markdown("## 🔍 Preview Changes")

        st.code(updated_code, language="python")

        # -------------------------
        # APPLY / REJECT
        # -------------------------
        col1, col2 = st.columns(2)

        with col1:
            if st.button("✅ Accept Changes"):
                files[selected_file] = updated_code
                st.session_state.current_files = files
                st.success("Applied!")

        with col2:
            if st.button("❌ Reject"):
                st.info("Changes discarded")