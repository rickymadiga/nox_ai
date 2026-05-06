import streamlit as st

def show_loader(message="Processing..."):
    return st.spinner(message)