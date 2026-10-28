"""Small helpers shared by dashboard pages."""
import matplotlib.pyplot as plt
import streamlit as st


def get_ctx() -> dict:
    return st.session_state["ctx"]


def show(fig) -> None:
    st.pyplot(fig)
    plt.close(fig)
