import random

import altair as alt
import pandas as pd
import streamlit as st


# ──────────────────────────────
# 페이지 설정
# ──────────────────────────────
st.set_page_config(
    page_title="EvoLab | 가상 진화 실험실",
    page_icon="🧬",
    layout="wide",
)

st.title("🧬 가상 진화 실험실")
st.caption("환경과 생물의 조건을 직접 설정하는 시뮬레이터")
st.info("현재 단계: 생물과 먹이의 초기 배치 — 아직 이동하거나 번식하지 않습니다.")


# ──────────────────────────────
# 사용자 설정
# ──────────────────────────────
with st.sidebar:
    st.header("⚙️ 초기 설정")

    initial_population = st.slider(
        "초기 생물 수",
        min_value=10,
        max_value=500,
        value=80,
        step=10,
    )

    initial_food = st.slider(
        "초기 먹이 수",
        min_value=0,
        max_value=1000,
        value=200,
        step=10,
    )

    seed = st.number_input(
        "배치 시드",
        min_value=0,
        max_value=1_000_000,
        value=42,
        step=1,
        help="같은 시드와 같은 개체 수를 설정하면 같은 위치에 배치됩니다.",
    )

    st.divider()
    st.markdown("🟢 **생물: 초록색**")
    st.markdown("🟠 **먹이: 주황색**")
    st.caption("먹이 수를 0으로 내리면 생물만 확인할 수 있습니다.")


# ──────────────────────────────
# 좌표 생성
# 생물·먹이의 난수 생성기를 분리
# ──────────────────────────────
organism_rng = random.Random(int(seed))
food_rng = random.Random(int(seed) + 1)

organisms = [
    {
        "x": organism_rng.uniform(0, 100),
        "y": organism_rng.uniform(0, 100),
        "종류": "생물",
    }
    for _ in range(initial_population)
]

foods = [
    {
        "x": food_rng.uniform(0, 100),
        "y": food_rng.uniform(0, 100),
        "종류": "먹이",
    }
    for _ in range(initial_food)
]

# 먹이를 먼저, 생물을 나중에 추가
map_data = pd.DataFrame(
    foods + organisms,
    columns=["x", "y", "종류"],
)


# ──────────────────────────────
# 개체 수 표시
# ──────────────────────────────
left, right = st.columns(2)

with left:
    st.metric("🟢 생물 수", f"{len(organisms)}마리")

with right:
    st.metric("🟠 먹이 수", f"{len(foods)}개")


# ──────────────────────────────
# 지도
# 종류와 색상의 대응을 명시적으로 고정
# ──────────────────────────────
st.subheader("🌍 초기 세계")

chart = (
    alt.Chart(map_data)
    .mark_circle(opacity=0.85)
    .encode(
        x=alt.X(
            "x:Q",
            title="가로 위치",
            scale=alt.Scale(domain=[0, 100], nice=False),
        ),
        y=alt.Y(
            "y:Q",
            title="세로 위치",
            scale=alt.Scale(domain=[0, 100], nice=False),
        ),
        color=alt.Color(
            "종류:N",
            title="종류",
            scale=alt.Scale(
                domain=["생물", "먹이"],
                range=["#22c55e", "#f59e0b"],
            ),
            legend=alt.Legend(orient="top"),
        ),
        size=alt.Size(
            "종류:N",
            scale=alt.Scale(
                domain=["생물", "먹이"],
                range=[90, 35],
            ),
            legend=None,
        ),
        tooltip=[
            alt.Tooltip("종류:N", title="종류"),
            alt.Tooltip("x:Q", title="가로 위치", format=".1f"),
            alt.Tooltip("y:Q", title="세로 위치", format=".1f"),
        ],
    )
    .properties(height=550)
)

st.altair_chart(
    chart,
    width="stretch",
    theme=None,
)

st.caption(
    "큰 초록색 점은 생물, 작은 주황색 점은 먹이입니다. "
    "위치가 가까운 점은 겹쳐 보일 수 있습니다."
)


# ──────────────────────────────
# 확인용 데이터
# ──────────────────────────────
with st.expander("🔍 배치 데이터 확인"):
    st.write(
        {
            "생물 수": len(organisms),
            "먹이 수": len(foods),
            "배치 시드": int(seed),
        }
    )
    st.dataframe(map_data, hide_index=True)
