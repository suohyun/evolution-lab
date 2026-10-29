from copy import deepcopy
from html import escape

import streamlit as st


# ==========================================
# 1. 기본 설정
# ==========================================

st.set_page_config(
    page_title="GENESIS | 지구의 설계자",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 실제 지구 역사의 정확한 수치가 아닌 게임용 설정입니다.
PRESETS = {
    "원시 지구": {
        "icon": "🔥",
        "description": "뜨거운 행성을 식혀 새로운 세계의 기반을 만드세요.",
        "temperature": 1000.0,
        "ocean": 0,
        "life": 0,
    },
    "바다의 지구": {
        "icon": "🌊",
        "description": "푸른 바다에서 첫 생명이 탄생할 환경을 준비하세요.",
        "temperature": 35.0,
        "ocean": 70,
        "life": 0,
    },
    "생명의 지구": {
        "icon": "🌱",
        "description": "작은 생태계에서 시작해 세계의 가능성을 관찰하세요.",
        "temperature": 22.0,
        "ocean": 65,
        "life": 20,
    },
}

# 이전 코드에서 남은 상태와 충돌하지 않도록 사용합니다.
APP_VERSION = "genesis_v2"

if st.session_state.get("app_version") != APP_VERSION:
    for key in (
        "world",
        "solar_control",
        "volcano_control",
        "temperature_control",
    ):
        st.session_state.pop(key, None)

    st.session_state.app_version = APP_VERSION
    st.session_state.world = None


# ==========================================
# 2. 게임 함수
# ==========================================

def get_planet_color(temperature):
    """게임용 온도 구간에 따라 행성 색을 정합니다."""
    if temperature >= 100:
        return "#f97346"

    if temperature <= 0:
        return "#b7e5ff"

    return "#359cfa"


def get_target_temperature(solar, volcano):
    """게임용 환경 조건으로 목표 온도를 계산합니다."""
    return (
        15.0
        + (solar - 100) * 0.5
        + (volcano - 20) * 0.2
    )


def create_world(preset_name):
    """선택한 초기 설정으로 새로운 세계를 만듭니다."""
    world = deepcopy(PRESETS[preset_name])

    world.update(
        {
            "name": (
                st.session_state.get("world_name", "").strip()
                or "이름 없는 지구"
            ),
            "stage": preset_name,
            "years": 0,
            "civilization": 0,
            "solar_energy": 100,
            "volcanic_activity": 20,
            "last_change": None,
            "history": [
                f"{preset_name} 상태로 세계가 탄생했습니다."
            ],
        }
    )

    st.session_state.world = world

    # 슬라이더 초기값도 함께 설정합니다.
    st.session_state.solar_control = 100
    st.session_state.volcano_control = 20
    st.session_state.temperature_control = float(
        world["temperature"]
    )


def reset_world():
    """세계와 환경 조절 상태를 초기화합니다."""
    st.session_state.world = None

    for key in (
        "solar_control",
        "volcano_control",
        "temperature_control",
    ):
        st.session_state.pop(key, None)


def update_environment():
    """환경 슬라이더의 값을 세계 상태에 반영합니다."""
    world = st.session_state.world

    if world is None:
        return

    world["solar_energy"] = st.session_state.solar_control
    world["volcanic_activity"] = (
        st.session_state.volcano_control
    )


def set_temperature():
    """신의 직접 개입으로 현재 온도를 변경합니다."""
    world = st.session_state.world

    if world is None:
        return

    world["temperature"] = float(
        st.session_state.temperature_control
    )
    world["last_change"] = None


def advance_time():
    """100만 년을 진행하고 환경에 따라 온도를 바꿉니다."""
    world = st.session_state.world

    if world is None:
        return

    target = get_target_temperature(
        world["solar_energy"],
        world["volcanic_activity"],
    )

    old_temperature = world["temperature"]

    # 매 진행마다 목표 온도와의 차이를 10% 좁힙니다.
    new_temperature = (
        old_temperature
        + (target - old_temperature) * 0.1
    )
    new_temperature = round(new_temperature, 1)

    world["temperature"] = new_temperature
    world["years"] += 1_000_000
    world["last_change"] = round(
        new_temperature - old_temperature,
        1,
    )

    # 버튼 콜백에서 온도 슬라이더도 함께 갱신합니다.
    st.session_state.temperature_control = new_temperature

    event = (
        f"{world['years']:,}년 경과 · "
        f"평균 기온 {old_temperature:,.1f} → "
        f"{new_temperature:,.1f} °C"
    )

    world["history"].append(event)

    # 최근 기록 50개만 보관합니다.
    world["history"] = world["history"][-50:]


# ==========================================
# 3. 화면 디자인
# ==========================================

st.markdown(
    """
    <style>
    .stApp {
        background:
            radial-gradient(
                ellipse at top,
                #18314a 0%,
                #0b1322 45%,
                #050912 100%
            );
        color: #e8f0fa;
    }

    .block-container {
        max-width: 1250px;
        padding-top: 2.5rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #edf5ff !important;
    }

    section[data-testid="stSidebar"] {
        background-color: #0d1727;
    }

    .eyebrow {
        color: #57dfc5;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 4px;
    }

    .title {
        color: #edf5ff;
        font-size: clamp(38px, 8vw, 72px);
        font-weight: 800;
        letter-spacing: 7px;
        margin: 8px 0;
    }

    .subtitle {
        color: #a5b7cb;
        line-height: 1.8;
        margin-bottom: 28px;
    }

    .card-icon {
        font-size: 44px;
        margin-bottom: 12px;
    }

    .card-description {
        min-height: 80px;
        color: #a5b7cb;
        line-height: 1.8;
    }

    .planet-stage {
        min-height: 350px;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .planet {
        width: min(260px, 60vw);
        aspect-ratio: 1;
        border-radius: 50%;
        background:
            radial-gradient(
                circle at 28% 25%,
                #ffffff99,
                transparent 32%
            ),
            radial-gradient(
                circle at 35% 35%,
                var(--planet-color),
                var(--planet-color) 30%,
                #07101e 85%
            );
        box-shadow:
            0 0 65px var(--planet-color),
            inset -24px -20px 40px #00000088;
    }

    .planet-label {
        text-align: center;
        color: #a5b7cb;
        letter-spacing: 3px;
        margin-bottom: 25px;
    }

    div[data-testid="stMetric"] {
        background: rgba(18, 34, 54, 0.85);
        border: 1px solid #29405a;
        border-radius: 14px;
        padding: 16px;
    }

    div[data-testid="stMetricLabel"] {
        color: #b8c9dc;
    }

    div[data-testid="stMetricValue"] {
        color: #edf5ff;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# 4. 공통 제목
# ==========================================

st.markdown(
    '<div class="eyebrow">CREATE · OBSERVE · EVOLVE</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="title">GENESIS</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "지구의 설계자 — 당신의 손에서 새로운 세계가 시작됩니다."
    "</div>",
    unsafe_allow_html=True,
)


# ==========================================
# 5. 시작 화면
# ==========================================

if st.session_state.world is None:
    st.subheader("01 / 세계의 시작")

    st.text_input(
        "세계 이름",
        value="나의 첫 번째 지구",
        max_chars=30,
        key="world_name",
    )

    st.write("")
    columns = st.columns(3)

    for column, (preset_name, preset) in zip(
        columns,
        PRESETS.items(),
    ):
        with column:
            with st.container(border=True):
                st.markdown(
                    f'<div class="card-icon">'
                    f'{preset["icon"]}'
                    "</div>",
                    unsafe_allow_html=True,
                )

                st.subheader(preset_name)

                st.markdown(
                    '<div class="card-description">'
                    f'{preset["description"]}'
                    "</div>",
                    unsafe_allow_html=True,
                )

                st.divider()

                st.write(
                    "🌡️ 초기 온도 · "
                    f"{preset['temperature']:,.0f} °C"
                )
                st.write(
                    f"🌊 바다 비율 · {preset['ocean']}%"
                )
                st.write(
                    f"🌱 생명량 · {preset['life']}"
                )

                st.button(
                    "이 세계 창조하기",
                    key=f"create_{preset_name}",
                    type="primary",
                    use_container_width=True,
                    on_click=create_world,
                    args=(preset_name,),
                )

    st.caption(
        "게임용으로 단순화한 초기 조건입니다. "
        "생명량은 실제 개체 수가 아닌 상대적인 지표입니다."
    )


# ==========================================
# 6. 게임 화면
# ==========================================

else:
    world = st.session_state.world

    # ---------- 왼쪽 제어판 ----------
    with st.sidebar:
        st.header("⚡ 신의 제어판")
        st.caption(
            "환경을 바꾸고 시간을 진행해 변화를 관찰하세요."
        )

        st.subheader("환경 설정")

        st.slider(
            "☀️ 태양 에너지",
            min_value=0,
            max_value=200,
            step=5,
            key="solar_control",
            on_change=update_environment,
            help="100을 기준으로 한 게임용 에너지 지표입니다.",
        )

        st.slider(
            "🌋 화산 활동",
            min_value=0,
            max_value=100,
            step=5,
            key="volcano_control",
            on_change=update_environment,
            help="이 게임에서는 높을수록 가열 효과가 커집니다.",
        )

        target_temperature = get_target_temperature(
            world["solar_energy"],
            world["volcanic_activity"],
        )

        st.metric(
            "현재 환경의 목표 온도",
            f"{target_temperature:.1f} °C",
        )

        st.caption(
            "시간을 진행하면 현재 온도가 목표 온도에 "
            "조금씩 가까워집니다."
        )

        st.divider()
        st.subheader("직접 개입")

        st.slider(
            "🌡️ 현재 온도 강제 설정",
            min_value=-100.0,
            max_value=1500.0,
            step=0.1,
            key="temperature_control",
            on_change=set_temperature,
            format="%.1f °C",
        )

        st.caption(
            "직접 설정한 온도도 이후 시간이 흐르면 "
            "환경의 영향을 받습니다."
        )

        st.divider()

        st.button(
            "새 세계 만들기",
            on_click=reset_world,
            use_container_width=True,
        )

        st.caption("누르면 현재 세계가 초기화됩니다.")

    # ---------- 게임 제목 ----------
    st.subheader(f"🌍 {world['name']}")

    st.caption(
        f"시작 유형 · {world['stage']}  |  "
        f"경과 시간 · {world['years']:,}년"
    )

    # ---------- 행성 시각화 ----------
    planet_color = get_planet_color(
        world["temperature"]
    )

    safe_name = escape(world["name"])

    st.markdown(
        f"""
        <div class="planet-stage">
            <div
                class="planet"
                style="--planet-color: {planet_color};"
            ></div>
        </div>
        <div class="planet-label">{safe_name}</div>
        """,
        unsafe_allow_html=True,
    )

    # ---------- 상태 지표 ----------
    delta = None

    if world["last_change"] is not None:
        delta = f"{world['last_change']:+.1f} °C"

    columns = st.columns(4)

    columns[0].metric(
        "평균 기온",
        f"{world['temperature']:,.1f} °C",
        delta=delta,
        delta_color="off",
    )

    columns[1].metric(
        "바다 비율",
        f"{world['ocean']}%",
    )

    columns[2].metric(
        "생명량",
        world["life"],
    )

    columns[3].metric(
        "문명 수준",
        world["civilization"],
    )

       # ---------- 시간 배속 ----------
    st.write("")
    st.subheader("⏳ 시간의 흐름")

    st.select_slider(
        "시간 배속",
        options=[1, 5, 20],
        value=1,
        format_func=lambda speed: f"×{speed}",
        key="time_speed",
    )

    st.caption(
        "×1: 초당 100만 년 · "
        "×5: 초당 500만 년 · "
        "×20: 초당 2,000만 년"
    )

    # ---------- 사건 기록 ----------
    st.divider()
    st.subheader("📜 세계의 역사")

    for event in reversed(world["history"]):
        st.write(f"✦ {event}")

    st.info(
        "현재 구현: 세계 생성, 환경 조절, 온도 변화, 시간 진행. "
        "바다 비율·생명량·문명 수준은 아직 초기값으로 유지됩니다."
    )
