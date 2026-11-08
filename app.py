import json
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
SAVE_VERSION = 2

INITIAL_WORLD = {
    "temperature": 1000.0,
    "ocean": 0.0,
    "cells": 0,
    "energy": 20.0,
    "cell_cost": 10.0,
    "research": [],
    "solar": 100,
    "volcano": 20,
    "years": 0.0,
}

OCEAN_FORMATION_TEMPERATURE = 80.0
COOLING_RATE_PER_SIMULATED_SECOND = 0.00906

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

SPECIES = {
    "photosynthetic": {
        "name": "광합성 생물",
        "icon": "☀️",
        "unlock_seconds": 30.0,
        "growth_per_second": 0.1,
        "max_population": 1000,
        "condition": "세포 5개 이상 · 온도 0~50°C · 바다 10% 이상",
    },
    "multicellular": {
        "name": "다세포 생물",
        "icon": "🪸",
        "unlock_seconds": 45.0,
        "growth_per_second": 0.05,
        "max_population": 1000,
        "condition": "광합성 생물 해금 · 온도 0~50°C · 바다 10% 이상",
    },
    "plants": {
        "name": "육상 식물",
        "icon": "🌿",
        "unlock_seconds": 60.0,
        "growth_per_second": 0.1,
        "max_population": 1000,
        "condition": "다세포 생물 해금 · 온도 0~50°C · 육지 존재",
    },
    "marine_animals": {
        "name": "해양 동물",
        "icon": "🐟",
        "unlock_seconds": 60.0,
        "growth_per_second": 0.1,
        "max_population": 1000,
        "condition": "다세포 생물 해금 · 온도 0~50°C · 바다 10% 이상",
    },
    "land_animals": {
        "name": "육상 동물",
        "icon": "🦎",
        "unlock_seconds": 90.0,
        "growth_per_second": 0.05,
        "max_population": 1000,
        "condition": "육상 식물 20개 이상 · 해양 동물 해금 · 온도 0~50°C",
    },
}


def new_biological_state():
    return {
        "organisms": {species_id: 0 for species_id in SPECIES},
        "evolution_progress": {species_id: 0.0 for species_id in SPECIES},
        "growth_progress": {species_id: 0.0 for species_id in SPECIES},
    }


def ensure_biological_state(world):
    defaults = new_biological_state()
    for field, values in defaults.items():
        world.setdefault(field, values)


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


def export_world(world, speed):
    ensure_biological_state(world)
    return {
        "save_version": SAVE_VERSION,
        "world": {
            "name": world["name"],
            "temperature": world["temperature"],
            "ocean": world["ocean"],
            "years": world["years"],
            "energy": world["energy"],
            "cells": world["cells"],
            "cell_cost": world["cell_cost"],
            "research": world["research"],
            "solar": world["solar"],
            "volcano": world["volcano"],
            "speed": speed,
            "life_ready_logged": world["life_ready_logged"],
            "history": world["history"],
            "organisms": world["organisms"],
            "evolution_progress": world["evolution_progress"],
            "growth_progress": world["growth_progress"],
        },
    }


def validate_save_data(data):
    if not isinstance(data, dict) or set(data) != {"save_version", "world"}:
        raise ValueError("JSON 최상위 구조가 올바르지 않습니다.")

    save_version = data["save_version"]
    if type(save_version) is not int or save_version not in (1, SAVE_VERSION):
        raise ValueError("지원하지 않는 저장 파일 버전입니다.")

    legacy_fields = {
        "name",
        "temperature",
        "ocean",
        "years",
        "energy",
        "cells",
        "cell_cost",
        "research",
        "solar",
        "volcano",
        "speed",
        "life_ready_logged",
        "history",
    }
    biological_fields = {
        "organisms",
        "evolution_progress",
        "growth_progress",
    }
    fields = (
        legacy_fields | biological_fields
        if save_version >= 2
        else legacy_fields
    )
    saved_world = data["world"]
    if not isinstance(saved_world, dict) or set(saved_world) != fields:
        raise ValueError("세계 정보의 항목이 올바르지 않습니다.")

    name = saved_world["name"]
    if not isinstance(name, str) or not name.strip() or len(name) > 30:
        raise ValueError("세계 이름은 1~30자여야 합니다.")

    numeric_ranges = {
        "temperature": (-1000.0, 2000.0),
        "ocean": (0.0, 70.0),
        "years": (0.0, 1e18),
        "energy": (0.0, 1e300),
        "cell_cost": (0.0, 1e300),
    }
    labels = {
        "temperature": "온도",
        "ocean": "바다 비율",
        "years": "경과 연수",
        "energy": "생명 에너지",
        "cell_cost": "다음 세포 가격",
    }
    values = {}
    for field, (minimum, maximum) in numeric_ranges.items():
        value = saved_world[field]
        if type(value) not in (int, float):
            raise ValueError(f"{labels[field]} 값은 숫자여야 합니다.")
        if isinstance(value, float) and not math.isfinite(value):
            raise ValueError(f"{labels[field]} 값은 유한한 숫자여야 합니다.")
        if not minimum <= value <= maximum:
            raise ValueError(f"{labels[field]} 값이 허용 범위를 벗어났습니다.")
        values[field] = float(value)

    if values["cell_cost"] <= 0:
        raise ValueError("다음 세포 가격은 0보다 커야 합니다.")

    cells = saved_world["cells"]
    if type(cells) is not int or not 0 <= cells <= 1_000_000_000:
        raise ValueError("세포 수는 0~1,000,000,000 사이의 정수여야 합니다.")

    for field, maximum in (("solar", 200), ("volcano", 100)):
        value = saved_world[field]
        if type(value) is not int or not 0 <= value <= maximum:
            label = "태양 에너지" if field == "solar" else "화산 활동"
            raise ValueError(f"{label} 값이 허용 범위를 벗어났습니다.")

    speed = saved_world["speed"]
    if type(speed) is not int or speed not in (0, 1, 2, 5, 20):
        raise ValueError("배속 값이 올바르지 않습니다.")

    research = saved_world["research"]
    if not isinstance(research, list) or len(research) > len(RESEARCH):
        raise ValueError("연구 목록 형식이 올바르지 않습니다.")
    if any(not isinstance(item, str) or item not in RESEARCH for item in research):
        raise ValueError("알 수 없는 연구가 포함되어 있습니다.")
    if len(set(research)) != len(research):
        raise ValueError("연구 목록에 중복 항목이 있습니다.")
    for research_id in research:
        required = RESEARCH[research_id]["requires"]
        if required and required not in research:
            raise ValueError("선행 연구가 완료되지 않은 연구가 포함되어 있습니다.")

    life_ready_logged = saved_world["life_ready_logged"]
    if type(life_ready_logged) is not bool:
        raise ValueError("생명 환경 기록 상태가 올바르지 않습니다.")

    history = saved_world["history"]
    if (
        not isinstance(history, list)
        or len(history) > 40
        or any(not isinstance(event, str) or len(event) > 500 for event in history)
    ):
        raise ValueError("사건 기록 형식이 올바르지 않습니다.")

    biological_state = new_biological_state()
    if save_version >= 2:
        organisms = saved_world["organisms"]
        evolution_progress = saved_world["evolution_progress"]
        growth_progress = saved_world["growth_progress"]
        for field, values in (
            ("organisms", organisms),
            ("evolution_progress", evolution_progress),
            ("growth_progress", growth_progress),
        ):
            if not isinstance(values, dict) or set(values) != set(SPECIES):
                raise ValueError("생물 상태 저장 형식이 올바르지 않습니다.")

        for species_id, species in SPECIES.items():
            count = organisms[species_id]
            if (
                type(count) is not int
                or count < 0
                or count > species["max_population"]
            ):
                raise ValueError(f"{species['name']} 수가 허용 범위를 벗어났습니다.")

            for progress_name, progress_values, maximum in (
                ("해금 진행률", evolution_progress, species["unlock_seconds"]),
                ("증식 진행률", growth_progress, 1.0),
            ):
                progress = progress_values[species_id]
                if (
                    type(progress) not in (int, float)
                    or (
                        isinstance(progress, float)
                        and not math.isfinite(progress)
                    )
                    or not 0 <= progress < maximum
                ):
                    raise ValueError(
                        f"{species['name']} {progress_name}이 올바르지 않습니다."
                    )

            biological_state["organisms"][species_id] = count
            biological_state["evolution_progress"][species_id] = float(
                evolution_progress[species_id]
            )
            biological_state["growth_progress"][species_id] = float(
                growth_progress[species_id]
            )
            if count == 0 and biological_state["growth_progress"][species_id] != 0:
                raise ValueError("잠긴 생물의 증식 진행률은 0이어야 합니다.")

        populations = biological_state["organisms"]
        if populations["multicellular"] and not populations["photosynthetic"]:
            raise ValueError("다세포 생물은 광합성 생물 해금 후 존재할 수 있습니다.")
        if (
            (populations["plants"] or populations["marine_animals"])
            and not populations["multicellular"]
        ):
            raise ValueError(
                "육상 식물과 해양 동물은 다세포 생물 해금 후 존재할 수 있습니다."
            )
        if populations["land_animals"] and (
            populations["plants"] < 20 or not populations["marine_animals"]
        ):
            raise ValueError("육상 동물 해금 조건이 충족되지 않은 저장 파일입니다.")

    return {
        **values,
        "name": name,
        "cells": cells,
        "research": research,
        "solar": saved_world["solar"],
        "volcano": saved_world["volcano"],
        "speed": speed,
        "life_ready_logged": life_ready_logged,
        "history": history,
        **biological_state,
    }


def reject_json_constant(value):
    raise ValueError(f"허용되지 않는 숫자 값입니다: {value}")


def reject_duplicate_keys(pairs):
    result = {}
    for key, value in pairs:
        if key in result:
            raise ValueError("JSON에 중복된 항목이 있습니다.")
        result[key] = value
    return result


def load_uploaded_world():
    uploaded_file = st.session_state.get("genesis_save_upload")
    if uploaded_file is None:
        st.session_state.genesis_save_message = (
            "불러올 JSON 파일을 먼저 선택해 주세요."
        )
        st.session_state.genesis_save_error = True
        return

    try:
        data = json.loads(
            uploaded_file.getvalue().decode("utf-8"),
            parse_constant=reject_json_constant,
            object_pairs_hook=reject_duplicate_keys,
        )
        saved = validate_save_data(data)
    except (UnicodeDecodeError, json.JSONDecodeError, ValueError, RecursionError) as error:
        st.session_state.genesis_save_message = (
            f"저장 파일을 불러오지 못했습니다: {error}"
        )
        st.session_state.genesis_save_error = True
        return

    world = {
        "name": saved["name"],
        "temperature": saved["temperature"],
        "ocean": saved["ocean"],
        "years": saved["years"],
        "energy": saved["energy"],
        "cells": saved["cells"],
        "cell_cost": saved["cell_cost"],
        "research": saved["research"],
        "solar": saved["solar"],
        "volcano": saved["volcano"],
        "last_tick": time.monotonic(),
        "last_tick_speed": saved["speed"],
        "life_ready_logged": saved["life_ready_logged"],
        "history": saved["history"],
        "organisms": saved["organisms"],
        "evolution_progress": saved["evolution_progress"],
        "growth_progress": saved["growth_progress"],
    }
    st.session_state.genesis_world = world
    st.session_state.genesis_speed = saved["speed"]
    st.session_state.genesis_solar = saved["solar"]
    st.session_state.genesis_volcano = saved["volcano"]
    st.session_state.confirm_reset = False
    st.session_state.genesis_save_message = "저장 파일을 불러왔습니다."
    st.session_state.genesis_save_error = False


def target_temperature(world):
    # 실제 기후 공식이 아닌 게임용 모델입니다.
    return (
        15.0
        + (world["solar"] - 100) * 0.5
        + (world["volcano"] - 20) * 0.2
    )


def temperature_after(current, target, simulated_seconds):
    if simulated_seconds <= 0:
        return current

    return target + (current - target) * math.exp(
        -COOLING_RATE_PER_SIMULATED_SECOND * simulated_seconds
    )


def cooling_progress(world):
    total_cooling = INITIAL_WORLD["temperature"] - OCEAN_FORMATION_TEMPERATURE
    progress = (
        INITIAL_WORLD["temperature"] - world["temperature"]
    ) / total_cooling
    return min(max(progress, 0.0), 1.0)


def cooling_seconds_remaining(world, speed):
    if world["temperature"] <= OCEAN_FORMATION_TEMPERATURE:
        return 0.0

    target = target_temperature(world)
    if target >= OCEAN_FORMATION_TEMPERATURE or speed <= 0:
        return None

    temperature_ratio = (
        (world["temperature"] - target)
        / (OCEAN_FORMATION_TEMPERATURE - target)
    )
    return (
        math.log(temperature_ratio)
        / COOLING_RATE_PER_SIMULATED_SECOND
        / speed
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


def biological_conditions(world):
    comfortable_temperature = 0 <= world["temperature"] <= 50
    ocean_available = world["ocean"] >= 10
    land_available = world["ocean"] < 100
    organisms = world["organisms"]

    return {
        "photosynthetic": (
            world["cells"] >= 5
            and comfortable_temperature
            and ocean_available
        ),
        "multicellular": (
            organisms["photosynthetic"] > 0
            and comfortable_temperature
            and ocean_available
        ),
        "plants": (
            organisms["multicellular"] > 0
            and comfortable_temperature
            and land_available
        ),
        "marine_animals": (
            organisms["multicellular"] > 0
            and comfortable_temperature
            and ocean_available
        ),
        "land_animals": (
            organisms["plants"] >= 20
            and organisms["marine_animals"] > 0
            and comfortable_temperature
        ),
    }


def advance_biology(world, simulated_seconds, conditions=None):
    starting_populations = world["organisms"].copy()
    if conditions is None:
        conditions = biological_conditions(world)

    for species_id, species in SPECIES.items():
        if starting_populations[species_id] > 0 or not conditions[species_id]:
            continue

        progress = world["evolution_progress"][species_id] + simulated_seconds
        if progress >= species["unlock_seconds"]:
            world["organisms"][species_id] = 1
            world["evolution_progress"][species_id] = 0.0
            add_log(
                world,
                f"{species['icon']} {species['name']}이(가) 처음 등장했습니다.",
            )
        else:
            world["evolution_progress"][species_id] = progress

    for species_id, species in SPECIES.items():
        population = starting_populations[species_id]
        if population == 0 or not conditions[species_id]:
            continue

        if population >= species["max_population"]:
            world["growth_progress"][species_id] = 0.0
            continue

        growth = (
            world["growth_progress"][species_id]
            + species["growth_per_second"] * simulated_seconds
        )
        increase = int(growth)
        world["organisms"][species_id] = min(
            species["max_population"],
            population + increase,
        )
        world["growth_progress"][species_id] = (
            growth - increase
            if world["organisms"][species_id] < species["max_population"]
            else 0.0
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

    ensure_biological_state(world)
    now = time.monotonic()

    # 긴 연결 중단을 오프라인 보상으로 계산하지 않습니다.
    elapsed = min(max(now - world["last_tick"], 0.0), 5.0)
    world["last_tick"] = now

    speed = float(st.session_state.get("genesis_speed", 1))
    previous_speed = float(world.get("last_tick_speed", speed))
    world["last_tick_speed"] = speed
    simulated_seconds = elapsed * previous_speed

    if simulated_seconds <= 0:
        return

    biology_conditions = biological_conditions(world)

    # 환경 변화 전후의 생산량을 평균내어 자원을 계산합니다.
    old_rate = production_rate(world)

    target = target_temperature(world)

    world["temperature"] = temperature_after(
        world["temperature"],
        target,
        simulated_seconds,
    )

    world["years"] += simulated_seconds * 1_000_000

    # 게임용 규칙: 충분히 식으면 바다가 서서히 형성됩니다.
    if (
        world["temperature"] <= OCEAN_FORMATION_TEMPERATURE
        and world["ocean"] < 70
    ):
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

    advance_biology(world, simulated_seconds, biology_conditions)

    if can_create_cell(world) and not world["life_ready_logged"]:
        world["life_ready_logged"] = True
        add_log(
            world,
            "✨ 세포를 만들 수 있는 환경이 갖춰졌습니다.",
        )


def create_world(name):
    world = deepcopy(INITIAL_WORLD)
    world.update(
        {
            "name": name.strip() or "이름 없는 지구",
            "last_tick": time.monotonic(),
            "last_tick_speed": 1.0,
            "life_ready_logged": False,
            "history": [
                "🌍 원시 지구 상태로 세계가 탄생했습니다."
            ],
            **new_biological_state(),
        }
    )

    st.session_state.genesis_world = world
    st.session_state.genesis_speed = 1
    st.session_state.genesis_solar = 100
    st.session_state.genesis_volcano = 20
    st.session_state.confirm_reset = False


def restart_world():
    world = st.session_state.genesis_world
    if world is not None:
        create_world(world["name"])


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

    ensure_biological_state(world)
    render_state = {
        "name": world["name"],
        "temperature": world["temperature"],
        "ocean": world["ocean"],
        "species": [
            {
                "id": species_id,
                "name": species["name"],
                "icon": species["icon"],
                "count": world["organisms"][species_id],
            }
            for species_id, species in SPECIES.items()
        ],
    }
    state_json = json.dumps(
        render_state,
        ensure_ascii=False,
        allow_nan=False,
    ).replace("<", "\\u003c").replace("&", "\\u0026")

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
                color: #dce8f5;
                font-family: sans-serif;
            }

            #scene {
                width: 100%;
                height: 360px;
            }

            #label, #species {
                position: absolute;
                width: 100%;
                text-align: center;
                text-shadow: 0 1px 5px #080f1d;
            }

            #label {
                top: 10px;
                color: #9eb8ce;
                font-size: 11px;
                letter-spacing: 2px;
            }

            #species {
                bottom: 9px;
                display: flex;
                flex-wrap: wrap;
                justify-content: center;
                gap: 5px 12px;
                padding: 0 8px;
                box-sizing: border-box;
                color: #cbd9e8;
                font-size: 11px;
            }

            .species-item.locked {
                color: #73869b;
            }
        </style>
    </head>
    <body>
        <div id="scene"></div>
        <div id="label"></div>
        <div id="species"></div>
        <script id="world-state" type="application/json">__STATE_JSON__</script>

        <script type="module">
        try {
            const THREE = await import(
                "https://cdn.jsdelivr.net/npm/three@0.170.0/build/three.module.js"
            );
            const state = JSON.parse(
                document.getElementById("world-state").textContent
            );
            const clamp = (value, min, max) =>
                Math.min(Math.max(value, min), max);
            const smoothstep = (edge0, edge1, value) => {
                const t = clamp((value - edge0) / (edge1 - edge0), 0, 1);
                return t * t * (3 - 2 * t);
            };
            const mixColor = (from, to, amount) => from.map(
                (channel, index) =>
                    Math.round(channel + (to[index] - channel) * amount)
            );
            const seed = Array.from(state.name).reduce(
                (value, char) => Math.imul(value ^ char.charCodeAt(0), 16777619),
                2166136261
            ) >>> 0;
            const hash3 = (x, y, z, offset) => {
                let value = (
                    Math.imul(x, 374761393)
                    + Math.imul(y, 668265263)
                    + Math.imul(z, 2147483647)
                    + offset
                ) | 0;
                value = Math.imul(value ^ (value >>> 13), 1274126177);
                return ((value ^ (value >>> 16)) >>> 0) / 4294967295;
            };
            const noise3 = (x, y, z, offset) => {
                const x0 = Math.floor(x);
                const y0 = Math.floor(y);
                const z0 = Math.floor(z);
                const fx = x - x0;
                const fy = y - y0;
                const fz = z - z0;
                const sx = fx * fx * (3 - 2 * fx);
                const sy = fy * fy * (3 - 2 * fy);
                const sz = fz * fz * (3 - 2 * fz);
                const low = (dx, dy) => (
                    hash3(x0, y0 + dy, z0 + dx, offset) * (1 - sx)
                    + hash3(x0 + 1, y0 + dy, z0 + dx, offset) * sx
                );
                const plane0 = low(0, 0) * (1 - sy) + low(0, 1) * sy;
                const plane1 = (
                    hash3(x0, y0, z0 + 1, offset) * (1 - sx) * (1 - sy)
                    + hash3(x0 + 1, y0, z0 + 1, offset) * sx * (1 - sy)
                    + hash3(x0, y0 + 1, z0 + 1, offset) * (1 - sx) * sy
                    + hash3(x0 + 1, y0 + 1, z0 + 1, offset) * sx * sy
                );
                return plane0 * (1 - sz) + plane1 * sz;
            };

            const container = document.getElementById("scene");
            const label = document.getElementById("label");
            label.textContent =
                "GENESIS · "
                + state.temperature.toFixed(1) + "°C · 바다 "
                + state.ocean.toFixed(1) + "%";

            const speciesContainer = document.getElementById("species");
            for (const species of state.species) {
                const item = document.createElement("span");
                item.className = "species-item"
                    + (species.count > 0 ? "" : " locked");
                item.textContent = species.count > 0
                    ? species.icon + " ×" + species.count.toLocaleString()
                    : "🔒 " + species.name;
                speciesContainer.appendChild(item);
            }

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

            const width = 512;
            const height = 256;
            const canvas = document.createElement("canvas");
            canvas.width = width;
            canvas.height = height;
            const context = canvas.getContext("2d");
            const image = context.createImageData(width, height);
            const terrain = new Float32Array(width * height);
            const vegetation = new Float32Array(width * height);
            const lava = new Float32Array(width * height);

            for (let y = 0; y < height; y++) {
                const latitude = (0.5 - y / (height - 1)) * Math.PI;
                const cosLatitude = Math.cos(latitude);
                for (let x = 0; x < width; x++) {
                    const longitude = x / (width - 1) * Math.PI * 2;
                    const px = cosLatitude * Math.cos(longitude);
                    const py = Math.sin(latitude);
                    const pz = cosLatitude * Math.sin(longitude);
                    const index = y * width + x;
                    terrain[index] = (
                        noise3(px * 2.4, py * 2.4, pz * 2.4, seed) * 0.56
                        + noise3(px * 5.2, py * 5.2, pz * 5.2, seed + 31) * 0.29
                        + noise3(px * 11, py * 11, pz * 11, seed + 79) * 0.15
                    );
                    vegetation[index] = noise3(
                        px * 8 + 19,
                        py * 8 - 7,
                        pz * 8 + 13,
                        seed + 131
                    );
                    lava[index] = noise3(
                        px * 15 - 5,
                        py * 15 + 11,
                        pz * 15 + 3,
                        seed + 197
                    );
                }
            }

            const sortedTerrain = Array.from(terrain).sort((a, b) => a - b);
            const seaCoverage = clamp(state.ocean / 100, 0, 0.7);
            const seaThreshold = seaCoverage > 0
                ? sortedTerrain[Math.floor(seaCoverage * (sortedTerrain.length - 1))]
                : -1;
            const plantCount = state.species.find(
                (species) => species.id === "plants"
            ).count;
            const plantCoverage = plantCount > 0
                ? clamp(plantCount / 1000, 0, 0.75)
                : 0;
            const hotness = smoothstep(80, 900, state.temperature);
            const coldRock = [46, 52, 62];
            const hotRock = [139, 49, 31];
            const rock = mixColor(coldRock, hotRock, hotness);

            for (let index = 0; index < terrain.length; index++) {
                let color;
                if (terrain[index] <= seaThreshold) {
                    const depth = clamp(
                        (seaThreshold - terrain[index]) * 2.5,
                        0,
                        1
                    );
                    color = mixColor([48, 147, 191], [10, 52, 119], depth);
                } else if (
                    plantCoverage > 0
                    && vegetation[index] >= 1 - plantCoverage
                ) {
                    color = mixColor(
                        [46, 94, 55],
                        [88, 158, 73],
                        vegetation[index]
                    );
                } else {
                    const variation = 0.78 + terrain[index] * 0.42;
                    color = rock.map((channel) =>
                        Math.round(channel * variation)
                    );
                    const lavaStrength = (
                        smoothstep(0.66, 0.84, lava[index])
                        * hotness
                    );
                    color = mixColor(color, [255, 91, 24], lavaStrength);
                }

                const offset = index * 4;
                image.data[offset] = color[0];
                image.data[offset + 1] = color[1];
                image.data[offset + 2] = color[2];
                image.data[offset + 3] = 255;
            }
            context.putImageData(image, 0, 0);

            const surfaceTexture = new THREE.CanvasTexture(canvas);
            surfaceTexture.colorSpace = THREE.SRGBColorSpace;
            const planet = new THREE.Mesh(
                new THREE.SphereGeometry(1.15, 48, 32),
                new THREE.MeshStandardMaterial({
                    map: surfaceTexture,
                    roughness: 0.82
                })
            );

            planet.rotation.z = 0.15;
            planet.rotation.y = (
                Date.now() / 1000 * 0.18 + (seed % 6283) / 1000
            ) % (Math.PI * 2);
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
                const star = hash3(i, 17, 29, seed + 251);
                const starY = hash3(i, 31, 7, seed + 307);
                const starZ = hash3(i, 43, 13, seed + 367);
                positions.push(
                    (star - 0.5) * 18,
                    (starY - 0.5) * 10,
                    -4 - starZ * 8
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

                renderer.setSize(width, 360);
                camera.aspect = width / 360;
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
                "3D 행성을 불러오지 못했습니다. 인터넷 연결을 확인해 주세요.";
            console.error("GENESIS WebGL rendering failed:", error);
        }
        </script>
    </body>
    </html>
    """

    components.html(
        html.replace("__STATE_JSON__", state_json),
        height=360,
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

    if world["cells"] == 0:
        temperature_ready = 0 <= world["temperature"] <= 60
        ocean_ready = world["ocean"] >= 10
        ready_conditions = int(temperature_ready) + int(ocean_ready)
        st.info(
            "다음 목표: 지구를 식히고 바다를 형성해 최초의 세포를 만드세요. "
            f"현재 온도 {world['temperature']:.1f}°C "
            f"({'충족' if temperature_ready else '필요: 0~60°C'}) · "
            f"바다 {world['ocean']:.1f}% "
            f"({'충족' if ocean_ready else '필요: 10% 이상'}) · "
            f"시작 에너지 {world['energy']:.1f} "
            f"(세포 비용 {world['cell_cost']:.1f})"
        )
        st.progress(
            ready_conditions / 2,
            text=f"최초 세포 환경 조건 {ready_conditions}/2 충족",
        )

    if world["ocean"] < 10:
        target = target_temperature(world)
        progress = cooling_progress(world)
        st.markdown("**현재 목표: 지표 냉각 중**")
        st.progress(
            progress,
            text=(
                "바다 형성 시작까지 냉각 진행 "
                f"{progress * 100:.1f}% "
                f"(목표 온도 {OCEAN_FORMATION_TEMPERATURE:.0f}°C)"
            ),
        )

        if world["temperature"] <= OCEAN_FORMATION_TEMPERATURE:
            st.caption("바다 형성 시작 온도에 도달했습니다.")
        elif target >= OCEAN_FORMATION_TEMPERATURE:
            st.caption(
                "현재 환경에서는 바다 형성 시작 온도에 도달할 수 없습니다. "
                "태양 에너지나 화산 활동을 조절해 주세요."
            )
        elif speed <= 0:
            st.caption("일시정지 중입니다. 재생하면 남은 시간을 계산합니다.")
        else:
            remaining = cooling_seconds_remaining(world, speed)
            remaining_seconds = math.ceil(remaining)
            hours, remainder = divmod(remaining_seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            if hours:
                estimate = f"{hours}시간 {minutes}분"
            elif minutes:
                estimate = f"{minutes}분 {seconds}초"
            else:
                estimate = f"{seconds}초"
            st.caption(f"현재 예상 남은 시간: 약 {estimate}")

        st.caption(
            "예상 시간은 현재 환경과 배속이 유지될 때의 추정값입니다."
        )

    st.subheader("🧬 생물 단계")
    st.caption(
        "생물 단계는 실제 진화 계통도를 정밀하게 재현한 것이 아닌 게임용 규칙입니다. "
        "육지가 존재하는 조건은 바다 비율 100% 미만으로 계산합니다. "
        "해금과 증식 시간은 배속이 반영된 시뮬레이션 초입니다."
    )
    biology_columns = st.columns(5)
    for column, (species_id, species) in zip(
        biology_columns,
        SPECIES.items(),
    ):
        population = world["organisms"][species_id]
        with column:
            with st.container(border=True):
                st.markdown(f"**{species['icon']} {species['name']}**")
                st.metric(
                    "현재 수",
                    f"{population:,}" if population else "잠김",
                )
                if population:
                    st.caption(
                        f"🔓 해금 · 최대 {species['max_population']:,} · "
                        f"증식 {species['growth_per_second']:.2f}/시뮬레이션 초"
                    )
                else:
                    st.caption("🔒 잠김")
                    progress = world["evolution_progress"][species_id]
                    ratio = progress / species["unlock_seconds"]
                    st.caption(species["condition"])
                    st.progress(
                        ratio,
                        text=(
                            f"해금 진행 {progress:.1f} / "
                            f"{species['unlock_seconds']:.0f}초"
                        ),
                    )

    st.write("")
    environment, evolution = st.columns([1, 1.35])

    # ---------- 환경 제어 ----------
    with environment:
        with st.container(border=True):
            st.subheader("⚡ 신의 제어판")

            st.select_slider(
                "시간 배속",
                options=[0, 1, 2, 5, 20],
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

    save_json = json.dumps(
        export_world(world, st.session_state.genesis_speed),
        ensure_ascii=False,
        indent=2,
        allow_nan=False,
    )
    st.download_button(
        "세계 저장 파일 다운로드",
        data=save_json,
        file_name="genesis-save.json",
        mime="application/json",
        use_container_width=True,
    )


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
    name = st.text_input(
        "세계 이름",
        value="나의 첫 번째 지구",
        max_chars=30,
    )

    if st.button(
        "🔥 지구 탄생시키기",
        key="create_primordial_world",
        type="primary",
        use_container_width=True,
    ):
        create_world(name)
        st.rerun()

    st.caption(
        "모든 새 세계는 뜨거운 원시 지구에서 시작합니다. "
        "지구를 식히고 바다를 만들어 최초의 세포를 탄생시키세요."
    )

else:
    # 3D 화면은 15초 간격, 게임 수치는 1초 간격으로 갱신합니다.
    render_planet()
    game_panel()

    st.divider()

    st.checkbox(
        "현재 세계를 초기화하고 원시 지구로 다시 시작합니다.",
        key="confirm_reset",
    )

    st.button(
        "다시 시작",
        key="restart_world_button",
        disabled=not st.session_state.get(
            "confirm_reset",
            False,
        ),
        on_click=restart_world,
    )

    st.caption(
        "현재 버전은 자동 저장과 오프라인 보상을 지원하지 않습니다. "
        "브라우저 새로고침이나 연결 종료 시 진행 내용이 사라질 수 있습니다."
    )

with st.expander("저장 파일 불러오기"):
    st.file_uploader(
        "GENESIS JSON 저장 파일",
        type=["json"],
        key="genesis_save_upload",
    )
    st.button(
        "불러오기",
        key="genesis_load_save_button",
        on_click=load_uploaded_world,
        type="primary",
    )

    save_message = st.session_state.get("genesis_save_message")
    if save_message:
        if st.session_state.get("genesis_save_error", False):
            st.error(save_message)
        else:
            st.success(save_message)

st.caption(
    "교육용 게임 프로토타입 · 환경 수치와 진화 순서는 "
    "실제 과학을 정밀하게 재현한 것이 아닌 게임용 규칙입니다."
)
