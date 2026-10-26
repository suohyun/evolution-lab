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
import random

st.divider()
st.subheader("🌍 생물 초기 배치")

# 같은 설정에서 위치를 재현하기 위한 난수 생성기
rng = random.Random(42)

# 초기 생물 수만큼 좌표 생성
organisms = [
    {
        "x": rng.uniform(0, 100),
        "y": rng.uniform(0, 100),
    }
    for _ in range(initial_population)
]

# 각 생물을 점으로 표시
st.scatter_chart(
    organisms,
    x="x",
    y="y",
    color="#22c55e",
    size=60,
    height=500,
)

st.caption(
    f"초록색 점 하나가 생물 한 마리입니다. "
    f"현재 {len(organisms)}마리를 배치했습니다."
)
