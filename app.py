import streamlit as st

st.set_page_config(
    page_title="가상 진화 실험실",
    page_icon="🧬",
    layout="wide",
)

st.title("🧬 가상 진화 실험실")
st.write("환경과 생물의 조건을 직접 설정하는 시뮬레이터")
st.success("첫 번째 앱 화면입니다!")
st.divider()
st.subheader("⚙️ 실험 설정")

initial_population = st.slider(
    "초기 생물 수",
    min_value=10,
    max_value=500,
    value=80,
    step=10,
)

st.metric("설정한 초기 생물 수", f"{initial_population}마리")
