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
st.subheader("🌍 생물과 먹이 초기 배치")

initial_food = st.slider(
    "초기 먹이 수",
    min_value=0,
    max_value=1000,
    value=200,
    step=10,
)

# 생물과 먹이의 난수 생성기를 분리
organism_rng = random.Random(42)
food_rng = random.Random(100)

# 생물 배치
organisms = [
    {
        "x": organism_rng.uniform(0, 100),
        "y": organism_rng.uniform(0, 100),
        "color": "#22c55e",
    }
    for _ in range(initial_population)
]

# 먹이 배치
foods = [
    {
        "x": food_rng.uniform(0, 100),
        "y": food_rng.uniform(0, 100),
        "color": "#f59e0b",
    }
    for _ in range(initial_food)
]

# 먹이를 먼저 그리고 그 위에 생물 표시
map_data = foods + organisms

st.scatter_chart(
    map_data,
    x="x",
    y="y",
    color="color",
    size=60,
    height=500,
)

st.caption("🟢 초록색: 생물 / 🟠 주황색: 먹이")

left, right = st.columns(2)

with left:
    st.metric("생물 수", f"{len(organisms)}마리")

with right:
    st.metric("먹이 수", f"{len(foods)}개")
st.write("생물 슬라이더 값:", initial_population)
st.write("실제 생물 데이터 수:", len(organisms))
st.write("먹이 슬라이더 값:", initial_food)
st.write("실제 먹이 데이터 수:", len(foods))

st.write("생물 데이터 예시:", organisms[:2])
st.write("먹이 데이터 예시:", foods[:2])
