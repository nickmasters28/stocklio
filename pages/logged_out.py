import streamlit as st
import streamlit.components.v1 as components

components.html(
    "<script>window.location.replace('https://www.stocklio.ai');</script>",
    height=0,
)
st.stop()
