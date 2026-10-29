import math
import time
from copy import deepcopy

import streamlit as st
import streamlit.components.v1 as components


# ==================================================
# 기본 설정
# ==================================================

st.set_page_config(
    page_title="GENESIS | 지구의 설계자",
    page_icon="🌍",
    layout="wide",
)

VERSION = "genesis-idle-1"

PRESETS = {
    "원시 지구": {
        "icon": "🔥",
        "description": "뜨거운 행성을 식혀 바다와 생명을 만드세요.",
        "temperature": 1000.0,
        "ocean": 0.0,
        "cells": 0,
    },
    "바다의 지구": {
        "icon": "🌊",
        "description": "바다에서 최초의 세포를 탄생시키세요.",
        "temperature": 35.0,
        "ocean": 70.0,
        "cells": 0,
    },
    "생명의 지구": {
        "icon": "🌱",
        "description": "세포를 가진 상태에서 진화를 시작하세요.",
        "temperature": 22.0,
        "ocean": 65.0,
        "cells": 1,
    },
}

RESEARCH = {
    "metabolism": {
        "name": "🧬 대사 효율",
        "cost": 50.0,
        "description": "세포의 에너지 생산량 ×2",
        "requires": None,
    },
    "photosynthesis": {
        "name": "☀️ 광합성 연구",
        "cost": 200.0,
        "description": "세포의 에너지 생산량 추가 ×3",
        "requires": "metabolism",
    },
    "multicellular": {
        "name": "🪸 다세포 조직 연구",
        "cost": 1000.0,
        "description": "세포의 에너지 생산량 추가 ×5",
        "requires": "photosynthesis",
    },
}

# 이전 버전에서 남은 상태와 충돌하지 않도록 초기화합니다.
if st.session_state.get("genesis_version") != VERSION:
    st.session_state.genesis_version = VERSION
    st.session_state.genesis_world = None

    for key in (
        "genesis_speed",
        "genesis_solar",
        "genesis_volcano",
    ):
        st.session_state.pop(key, None)


# ==================================================
# 디자인
# ==================================================

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
        max-width: 1280px;
        padding-top: 2rem;
        padding-bottom: 3rem;
    }

    h1, h2, h3 {
        color: #edf5ff !important;
    }

    .eyebrow {
        color: #57dfc5;
        letter-spacing: 4px;
        font-size: 12px;
        font-weight: 700;
    }

    .genesis-title {
        color: #edf5ff;
        font-size: clamp(36px, 7vw, 66px);
        font-weight: 800;
        letter-spacing: 7px;
        margin: 6px 0;
    }

    .subtitle {
        color: #a5b7cb;
        line-height: 1.8;
        margin-bottom: 22px;
    }

    div[data-testid="stMetric"] {
        background: rgba(18, 34, 54, 0.85);
        border: 1px solid #29405a;
        border-radius: 14px;
        padding: 15px;
    }

    div[data-testid="stMetricLabel"] {
        color: #b8c9dc;
    }

    div[data-testid="stMetricValue"] {
        color: #edf5ff;
    }

    .stButton > button {
        border-radius: 10px;
    }
    </style>
    """,
    unsafe_allow_html=True,
)


# ==================================================
# 게임 계산
# ==================================================

def add_log(world, message):
    world["history"].append(message)
    world["history"] = world["history"][-40:]


def target_temperature(world):
    # 실제 기후 공식이 아닌 게임용 모델입니다.
    return (
        15.0
        + (world["solar"] - 100) * 0.5
        + (world["volcano"] - 20) * 0.2
    )


def habitat_factor(world):
    """환경에 따른 생산 배율: 세포가 사라지지는 않습니다."""
    temperature = world["temperature"]

    if world["ocean"] < 10:
        return 0.0

    if 0 <= temperature <= 50:
        return 1.0

    if -20 <= temperature <= 80:
        return 0.25

    return 0.05


def production_rate(world):
    multiplier = 1.0

    if "metabolism" in world["research"]:
        multiplier *= 2

    if "photosynthesis" in world["research"]:
        multiplier *= 3

    if "multicellular" in world["research"]:
        multiplier *= 5

    return (
        world["cells"]
        * multiplier
        * habitat_factor(world)
    )


def can_create_cell(world):
    return (
        world["ocean"] >= 10
        and 0 <= world["temperature"] <= 60
    )


def stage_name(world):
    if "multicellular" in world["research"]:
        return "다세포 연구 시대"

    if "photosynthesis" in world["research"]:
        return "광합성 시대"

    if world["cells"] > 0:
        return "초기 생명 시대"

    if world["ocean"] >= 10:
        return "해양 형성 시대"

    return "원시 지구 시대"


def tick():
    """실제 경과 시간에 비례해 세계를 진행합니다."""
    world = st.session_state.genesis_world

    if world is None:
        return

    now = time.monotonic()

    # 긴 연결 중단을 오프라인 보상으로 계산하지 않습니다.
    elapsed = min(max(now - world["last_tick"], 0.0), 5.0)
    world["last_tick"] = now

    speed = float(st.session_state.get("genesis_speed", 1))
    simulated_seconds = elapsed * speed

    if simulated_seconds <= 0:
        return

    # 환경 변화 전후의 생산량을 평균내어 자원을 계산합니다.
    old_rate = production_rate(world)

    target = target_temperature(world)

    # ×1에서 1초마다 온도 차이가 약 10% 줄어듭니다.
    # 배속이 높아도 과도하게 목표 온도를 넘어가지 않습니다.
    cooling_factor = 1 - math.pow(
        0.9,
        simulated_seconds,
    )

    world["temperature"] += (
        target - world["temperature"]
    ) * cooling_factor

    world["years"] += simulated_seconds * 1_000_000

    # 게임용 규칙: 충분히 식으면 바다가 서서히 형성됩니다.
    if world["temperature"] <= 80 and world["ocean"] < 70:
        previous_ocean = world["ocean"]

        world["ocean"] = min(
            70.0,
            world["ocean"] + simulated_seconds * 2,
        )

        if previous_ocean < 10 <= world["ocean"]:
            add_log(
                world,
                "🌊 바다가 형성되기 시작했습니다.",
            )

    new_rate = production_rate(world)

    world["energy"] += (
        (old_rate + new_rate)
        / 2
        * simulated_seconds
    )

    if can_create_cell(world) and not world["life_ready_logged"]:
        world["life_ready_logged"] = True
        add_log(
            world,
            "✨ 세포를 만들 수 있는 환경이 갖춰졌습니다.",
        )


def create_world(preset_name, name):
    world = deepcopy(PRESETS[preset_name])

    world.update(
        {
            "name": name.strip() or "이름 없는 지구",
            "energy": 20.0,
            "cell_cost": 10.0,
            "research": [],
            "solar": 100,
            "volcano": 20,
            "years": 0.0,
            "last_tick": time.monotonic(),
            "life_ready_logged": False,
            "history": [
                f"🌍 {preset_name} 상태로 세계가 탄생했습니다."
            ],
        }
    )

    st.session_state.genesis_world = world
    st.session_state.genesis_speed = 1
    st.session_state.genesis_solar = 100
    st.session_state.genesis_volcano = 20


def change_environment():
    # 변경 전 환경으로 직전까지의 시간을 먼저 계산합니다.
    tick()

    world = st.session_state.genesis_world
    world["solar"] = st.session_state.genesis_solar
    world["volcano"] = st.session_state.genesis_volcano


def buy_cell():
    tick()
    world = st.session_state.genesis_world

    if not can_create_cell(world):
        return

    if world["energy"] < world["cell_cost"]:
        return

    world["energy"] -= world["cell_cost"]
    world["cells"] += 1
    world["cell_cost"] = round(
        world["cell_cost"] * 1.15,
        2,
    )

    if world["cells"] == 1:
        add_log(world, "🦠 최초의 세포가 탄생했습니다.")


def buy_research(research_id):
    tick()
    world = st.session_state.genesis_world
    item = RESEARCH[research_id]

    if research_id in world["research"]:
        return

    required = item["requires"]

    if required and required not in world["research"]:
        return

    if world["cells"] < 1 or world["energy"] < item["cost"]:
        return

    world["energy"] -= item["cost"]
    world["research"].append(research_id)

    add_log(
        world,
        f"🔬 {item['name']} 완료",
    )


# ==================================================
# 3D 행성
# ==================================================

# 게임 계산과 분리하여 3D 화면을 매초 다시 만들지 않습니다.
@st.fragment(run_every="15s")
def render_planet():
    world = st.session_state.genesis_world

    if world is None:
        return

    temperature = world["temperature"]

    if temperature >= 100:
        color = "#f97346"
    elif temperature <= 0:
        color = "#b7e5ff"
    else:
        color = "#359cfa"

    html = """
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="utf-8">
        <style>
            html, body {
                margin: 0;
                overflow: hidden;
                background: #080f1d;
            }

            #scene {
                width: 100%;
                height: 330px;
            }

            #label {
                position: absolute;
                bottom: 12px;
                width: 100%;
                color: #9eb8ce;
                text-align: center;
                font: 11px sans-serif;
                letter-spacing: 3px;
            }
        </style>
    </head>
    <body>
        <div id="scene"></div>
        <div id="label">GENESIS · PLANET OBSERVATORY</div>

        <script type="module">
        try {
            const THREE = await import(
                "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js"
            );

            const container = document.getElementById("scene");
            const scene = new THREE.Scene();

            const camera = new THREE.PerspectiveCamera(
                45, 1, 0.1, 100
            );
            camera.position.z = 4.4;

            const renderer = new THREE.WebGLRenderer({
                antialias: true,
                alpha: true
            });

            renderer.setPixelRatio(
                Math.min(window.devicePixelRatio, 2)
            );

            container.appendChild(renderer.domElement);

            const planet = new THREE.Mesh(
                new THREE.SphereGeometry(1.15, 48, 32),
                new THREE.MeshStandardMaterial({
                    color: "__COLOR__",
                    roughness: 0.75
                })
            );

            planet.rotation.z = 0.15;
            scene.add(planet);

            scene.add(
                new THREE.AmbientLight(0xc5deff, 0.9)
            );

            const sun = new THREE.DirectionalLight(
                0xffffff, 3
            );
            sun.position.set(-3, 2, 4);
            scene.add(sun);

            const rim = new THREE.DirectionalLight(
                0x38bdf8, 1
            );
            rim.position.set(3, 0, -2);
            scene.add(rim);

            const positions = [];

            for (let i = 0; i < 350; i++) {
                positions.push(
                    (Math.random() - 0.5) * 18,
                    (Math.random() - 0.5) * 10,
                    -4 - Math.random() * 8
                );
            }

            const geometry = new THREE.BufferGeometry();

            geometry.setAttribute(
                "position",
                new THREE.Float32BufferAttribute(
                    positions, 3
                )
            );

            scene.add(
                new THREE.Points(
                    geometry,
                    new THREE.PointsMaterial({
                        color: 0xdbeafe,
                        size: 0.025
                    })
                )
            );

            function resize() {
                const width = Math.max(
                    container.clientWidth, 1
                );

                renderer.setSize(width, 330);
                camera.aspect = width / 330;
                camera.updateProjectionMatrix();
            }

            new ResizeObserver(resize).observe(container);
            resize();

            let previous = null;

            function animate(time) {
                const dt = previous === null
                    ? 0
                    : Math.min((time - previous) / 1000, 0.1);

                previous = time;
                planet.rotation.y += dt * 0.18;

                renderer.render(scene, camera);
                requestAnimationFrame(animate);
            }

            requestAnimationFrame(animate);
        } catch (error) {
            document.getElementById("label").textContent =
                "3D 로딩 실패: " + error.message;
        }
        </script>
    </body>
    </html>
    """

    components.html(
        html.replace("__COLOR__", color),
        height=330,
        scrolling=False,
    )


# ==================================================
# 자동 갱신 게임 패널
# ==================================================

@st.fragment(run_every="1s")
def game_panel():
    tick()
    world = st.session_state.genesis_world

    if world is None:
        return

    st.subheader(f"🌍 {world['name']}")

    st.caption(
        f"{stage_name(world)} · "
        f"경과 시간 {int(world['years']):,}년"
    )

    columns = st.columns(4)

    columns[0].metric(
        "🌱 생명 에너지",
        f"{world['energy']:,.1f}",
    )

    columns[1].metric(
        "🦠 세포",
        f"{world['cells']:,}",
    )

    speed = st.session_state.genesis_speed
    actual_rate = production_rate(world) * speed

    columns[2].metric(
        "⚡ 현재 생산 / 현실 초",
        f"{actual_rate:,.1f}",
    )

    columns[3].metric(
        "🌡️ 평균 기온",
        f"{world['temperature']:,.1f} °C",
    )

    st.write("")
    environment, evolution = st.columns([1, 1.35])

    # ---------- 환경 제어 ----------
    with environment:
        with st.container(border=True):
            st.subheader("⚡ 신의 제어판")

            st.select_slider(
                "시간 배속",
                options=[0, 1, 5, 20],
                format_func=lambda value: (
                    "⏸ 일시정지"
                    if value == 0
                    else f"×{value}"
                ),
                key="genesis_speed",
            )

            st.caption(
                "×1에서 현실 1초 ≈ 게임 속 100만 년. "
                "배속은 환경 변화와 자원 생산에 함께 적용됩니다."
            )

            st.slider(
                "☀️ 태양 에너지",
                min_value=0,
                max_value=200,
                step=5,
                key="genesis_solar",
                on_change=change_environment,
            )

            st.slider(
                "🌋 화산 활동",
                min_value=0,
                max_value=100,
                step=5,
                key="genesis_volcano",
                on_change=change_environment,
            )

            st.write(
                "환경의 목표 온도: "
                f"**{target_temperature(world):.1f} °C**"
            )

            st.write(
                f"🌊 바다 비율: **{world['ocean']:.1f}%**"
            )

            st.write(
                "🌿 환경 생산 배율: "
                f"**×{habitat_factor(world):.2f}**"
            )

            st.caption(
                "생산 최적 온도는 0~50°C입니다. "
                "환경이 나빠져도 현재 버전에서는 세포가 죽지 않습니다."
            )

    # ---------- 진화와 연구 ----------
    with evolution:
        with st.container(border=True):
            st.subheader("🧬 생명과 진화")

            st.write(
                f"세포 구매 가격: "
                f"**{world['cell_cost']:,.2f} 에너지**"
            )

            st.button(
                "🦠 세포 생성",
                key="buy_cell_button",
                type="primary",
                use_container_width=True,
                disabled=(
                    not can_create_cell(world)
                    or world["energy"] < world["cell_cost"]
                ),
                on_click=buy_cell,
            )

            if not can_create_cell(world):
                st.caption(
                    "생성 조건: 바다 10% 이상, 온도 0~60°C. "
                    "환경을 조절하고 기다려 주세요."
                )
            else:
                st.caption(
                    "세포는 기본적으로 초당 에너지 1을 생산합니다. "
                    "추가 구매 가격은 15%씩 증가합니다."
                )

            st.divider()

            for research_id, item in RESEARCH.items():
                completed = research_id in world["research"]
                required = item["requires"]

                unlocked = (
                    required is None
                    or required in world["research"]
                )

                st.markdown(f"**{item['name']}**")
                st.caption(item["description"])

                label = (
                    "✅ 연구 완료"
                    if completed
                    else f"연구 · 에너지 {item['cost']:,.0f}"
                )

                st.button(
                    label,
                    key=f"research_{research_id}",
                    use_container_width=True,
                    disabled=(
                        completed
                        or not unlocked
                        or world["cells"] < 1
                        or world["energy"] < item["cost"]
                    ),
                    on_click=buy_research,
                    args=(research_id,),
                )

    st.subheader("📜 세계의 역사")

    with st.container(border=True):
        for event in reversed(world["history"][-8:]):
            st.write(event)


# ==================================================
# 시작 화면 / 플레이 화면
# ==================================================

st.markdown(
    '<div class="eyebrow">CREATE · OBSERVE · EVOLVE</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="genesis-title">GENESIS</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "지구의 설계자 — 작은 세포에서 시작되는 당신의 세계"
    "</div>",
    unsafe_allow_html=True,
)

if st.session_state.genesis_world is None:
    st.subheader("세계의 시작을 선택하세요")

    name = st.text_input(
        "세계 이름",
        value="나의 첫 번째 지구",
        max_chars=30,
    )

    columns = st.columns(3)

    for column, (preset_name, preset) in zip(
        columns,
        PRESETS.items(),
    ):
        with column:
            with st.container(border=True):
                st.markdown(f"## {preset['icon']}")
                st.subheader(preset_name)
                st.write(preset["description"])

                st.divider()

                st.write(
                    f"🌡️ 온도: {preset['temperature']:,.0f} °C"
                )
                st.write(
                    f"🌊 바다: {preset['ocean']:.0f}%"
                )
                st.write(
                    f"🦠 세포: {preset['cells']}"
                )
                st.write("🌱 시작 에너지: 20")

                if st.button(
                    "이 세계 창조하기",
                    key=f"start_{preset_name}",
                    type="primary",
                    use_container_width=True,
                ):
                    create_world(preset_name, name)
                    st.rerun()

    st.caption(
        "빠르게 기능을 확인하려면 '생명의 지구'를 선택하세요."
    )

else:
    # 3D 화면은 15초 간격, 게임 수치는 1초 간격으로 갱신합니다.
    render_planet()
    game_panel()

    st.divider()

    st.checkbox(
        "현재 세계를 지우고 다시 시작할게요.",
        key="confirm_reset",
    )

    if st.button(
        "새 세계 만들기",
        disabled=not st.session_state.get(
            "confirm_reset",
            False,
        ),
    ):
        st.session_state.genesis_world = None
        st.session_state.pop("confirm_reset", None)
        st.rerun()

    st.caption(
        "현재 버전은 자동 저장과 오프라인 보상을 지원하지 않습니다. "
        "브라우저 새로고침이나 연결 종료 시 진행 내용이 사라질 수 있습니다."
    )

st.caption(
    "교육용 게임 프로토타입 · 환경 수치와 진화 순서는 "
    "실제 과학을 정밀하게 재현한 것이 아닌 게임용 규칙입니다."
)
