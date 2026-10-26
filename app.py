from copy import deepcopy
from html import escape

import streamlit as st


st.set_page_config(
    page_title="GENESIS | 지구의 설계자",
    page_icon="🌍",
    layout="wide",
)


# 실제 지구 역사의 정확한 수치가 아닌 게임용 설정입니다.
PRESETS = {
    "원시 지구": {
        "icon": "🔥",
        "description": "뜨거운 행성을 식혀 바다와 생명의 기반을 만드세요.",
        "temperature": 1000,
        "ocean": 0,
        "life": 0,
        "color": "#f97346",
    },
    "바다의 지구": {
        "icon": "🌊",
        "description": "푸른 바다에서 첫 생명이 탄생할 조건을 만드세요.",
        "temperature": 35,
        "ocean": 70,
        "life": 0,
        "color": "#359cfa",
    },
    "생명의 지구": {
        "icon": "🌱",
        "description": "작은 생태계를 키워 새로운 시대를 준비하세요.",
        "temperature": 22,
        "ocean": 65,
        "life": 20,
        "color": "#36cfaa",
    },
}


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
        max-width: 1200px;
        padding-top: 3rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #edf5ff !important;
    }

    .eyebrow {
        color: #57dfc5;
        font-size: 12px;
        font-weight: 700;
        letter-spacing: 4px;
    }

    .title {
        color: #edf5ff;
        font-size: clamp(40px, 8vw, 76px);
        font-weight: 800;
        letter-spacing: 8px;
        margin: 8px 0;
    }

    .subtitle {
        color: #a5b7cb;
        line-height: 1.8;
        margin-bottom: 32px;
    }

    .card-icon {
        font-size: 44px;
        margin-bottom: 12px;
    }

    .card-description {
        min-height: 75px;
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
    </style>
    """,
    unsafe_allow_html=True,
)


if "world" not in st.session_state:
    st.session_state.world = None


def create_world(preset_name, name):
    """선택한 초기 설정으로 새 세계를 만듭니다."""
    world = deepcopy(PRESETS[preset_name])

    world.update(
        {
            "name": name.strip() or "이름 없는 지구",
            "stage": preset_name,
            "years": 0,
            "civilization": 0,
            "history": [
                f"{preset_name} 상태로 세계가 탄생했습니다."
            ],
        }
    )

    st.session_state.world = world


def reset_world():
    st.session_state.world = None


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


if st.session_state.world is None:
    st.subheader("01 / 세계의 시작")

    name = st.text_input(
        "세계 이름",
        value="나의 첫 번째 지구",
        max_chars=30,
    )

    st.write("")
    columns = st.columns(3)

    for column, (preset_name, preset) in zip(
        columns, PRESETS.items()
    ):
        with column:
            with st.container(border=True):
                st.markdown(
                    f'<div class="card-icon">{preset["icon"]}</div>',
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
                    f"🌡️ 초기 온도 · {preset['temperature']} °C"
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
                    args=(preset_name, name),
                )

    st.caption(
        "게임용으로 단순화한 초기 조건입니다. "
        "생명량은 개체 수가 아닌 상대적인 지표입니다."
    )

else:
    world = st.session_state.world

    left, right = st.columns([4, 1])

    with left:
        st.subheader(f"🌍 {world['name']}")
        st.caption(
            f"{world['stage']} · 경과 시간 {world['years']:,}년"
        )

    with right:
        st.button(
            "새 세계 만들기",
            on_click=reset_world,
            use_container_width=True,
        )

    st.markdown(
        f"""
        <div class="planet-stage">
            <div
                class="planet"
                style="--planet-color: {world['color']};"
            ></div>
        </div>
        <div class="planet-label">
            {escape(world["name"])}
        </div>
        """,
        unsafe_allow_html=True,
    )

    columns = st.columns(4)

    columns[0].metric(
        "평균 기온",
        f"{world['temperature']:,} °C",
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

    st.divider()
    st.subheader("세계의 역사")

    for event in reversed(world["history"]):
        st.write(f"✦ {event}")

    st.info(
        "첫 단계: 세계 생성 완료. "
        "환경 조절과 시간 진행은 다음 단계에서 연결합니다."
    )
