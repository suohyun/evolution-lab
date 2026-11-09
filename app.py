import json
import math
import secrets
import time
from copy import deepcopy
from pathlib import Path

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
SAVE_VERSION = 5
TERRAIN_GENERATION_VERSION = 1
SIMULATION_SPEED = 1
PRELIFE_DISCOVERY_INTERVAL_SECONDS = 60.0
PRELIFE_DISCOVERY_REWARD = 2.0
PRELIFE_DISCOVERY_CAPACITY = 3
FIXED_ENVIRONMENT = {
    "solar": 100,
    "volcano": 20,
}

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
COOLING_DURATION_SECONDS = 300.0
COOLING_TARGET_TEMPERATURE = 15.0
COOLING_RATE = math.log(
    (INITIAL_WORLD["temperature"] - COOLING_TARGET_TEMPERATURE)
    / (OCEAN_FORMATION_TEMPERATURE - COOLING_TARGET_TEMPERATURE)
) / COOLING_DURATION_SECONDS

planet_component = components.declare_component(
    "genesis_planet",
    path=str(Path(__file__).parent / "planet_component"),
)

OBJECTIVES = (
    {
        "id": "ocean_formed",
        "title": "바다 형성",
        "description": "지표가 식어 80°C에 도달하면 바다가 형성되기 시작합니다.",
        "reward": 10.0,
    },
    {
        "id": "first_cell",
        "title": "최초 세포",
        "description": "적합한 환경에서 세포를 하나 만드세요.",
        "reward": 15.0,
    },
    {
        "id": "five_cells",
        "title": "세포 군집",
        "description": "세포를 5개 모아 진화 선택을 준비하세요.",
        "reward": 0.0,
    },
    {
        "id": "first_evolution",
        "title": "첫 진화 선택",
        "description": "다음 진화 방향을 하나 선택하세요.",
        "reward": 20.0,
    },
    {
        "id": "first_life",
        "title": "첫 생명 발견",
        "description": "첫 광합성 생물이 등장하도록 기다리세요.",
        "reward": 30.0,
    },
)

EVOLUTION_TRAITS = {
    "photosynthetic": {
        "name": "광합성형",
        "icon": "☀️",
        "effect": "세포당 창조 에너지 자동 생산 +0.50/초",
        "energy_per_cell": 0.5,
        "growth_multiplier": 1.0,
        "adaptive_floor": 0.0,
    },
    "proliferative": {
        "name": "증식형",
        "icon": "🧫",
        "effect": "모든 생물의 자동 증식 속도 ×1.50",
        "energy_per_cell": 0.0,
        "growth_multiplier": 1.5,
        "adaptive_floor": 0.0,
    },
    "adaptive": {
        "name": "적응형",
        "icon": "🛡️",
        "effect": "불리한 환경에서도 세포 생산 배율 최소 ×0.25",
        "energy_per_cell": 0.0,
        "growth_multiplier": 1.0,
        "adaptive_floor": 0.25,
    },
}

DISCOVERY_EVENTS = {
    "ocean_formation": {
        "title": "심해의 첫 발견",
        "trigger": "바다 비율 10% 달성",
        "choices": {
            "mineral_vein": {
                "label": "광물층 채집",
                "effect": "창조 에너지 +25",
                "energy": 25.0,
                "energy_per_cell": 0.0,
                "growth_multiplier": 1.0,
            },
            "hydrothermal_chemistry": {
                "label": "열수 화학 반응",
                "effect": "세포당 창조 에너지 자동 생산 +0.20/초",
                "energy": 0.0,
                "energy_per_cell": 0.2,
                "growth_multiplier": 1.0,
            },
        },
    },
    "first_life": {
        "title": "광합성 생물의 흔적",
        "trigger": "광합성 생물 최초 등장",
        "choices": {
            "gene_archive": {
                "label": "유전자 보관",
                "effect": "생물 자동 증식 속도 ×1.25",
                "energy": 0.0,
                "energy_per_cell": 0.0,
                "growth_multiplier": 1.25,
            },
            "metabolic_enzyme": {
                "label": "대사 효소 추출",
                "effect": "세포당 창조 에너지 자동 생산 +0.25/초",
                "energy": 0.0,
                "energy_per_cell": 0.25,
                "growth_multiplier": 1.0,
            },
        },
    },
}

RESEARCH = {
    "metabolism": {
        "name": "🧬 대사 효율",
        "cost": 50.0,
        "description": "세포의 창조 에너지 생산량 ×2",
        "requires": None,
    },
    "photosynthesis": {
        "name": "☀️ 광합성 연구",
        "cost": 200.0,
        "description": "세포의 창조 에너지 생산량 추가 ×3",
        "requires": "metabolism",
    },
    "multicellular": {
        "name": "🪸 다세포 조직 연구",
        "cost": 1000.0,
        "description": "세포의 창조 에너지 생산량 추가 ×5",
        "requires": "photosynthesis",
    },
    "evolution_photosynthetic": {
        "name": "☀️ 광합성형 유전자 해독",
        "cost": 350.0,
        "description": EVOLUTION_TRAITS["photosynthetic"]["effect"],
        "requires": "multicellular",
    },
    "evolution_proliferative": {
        "name": "🧫 증식형 유전자 해독",
        "cost": 350.0,
        "description": EVOLUTION_TRAITS["proliferative"]["effect"],
        "requires": "multicellular",
    },
    "evolution_adaptive": {
        "name": "🛡️ 적응형 유전자 해독",
        "cost": 350.0,
        "description": EVOLUTION_TRAITS["adaptive"]["effect"],
        "requires": "multicellular",
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


def new_campaign_state():
    return {
        "completed_objectives": [],
        "discovery_choices": {
            event_id: None for event_id in DISCOVERY_EVENTS
        },
        "first_evolution": None,
        "researched_evolutions": [],
        "celebrated": [],
        "celebration_pending": [],
    }


def new_prelife_discovery_state():
    return {
        "progress_seconds": 0.0,
        "next_id": 1,
        "available_ids": [],
        "claimed_total": 0,
    }


def ensure_campaign_state(world):
    world.setdefault("campaign", new_campaign_state())


def ensure_prelife_discovery_state(world):
    world.setdefault("prelife_discoveries", new_prelife_discovery_state())


def active_evolutions(world):
    ensure_campaign_state(world)
    campaign = world["campaign"]
    active = set(campaign["researched_evolutions"])
    if campaign["first_evolution"] is not None:
        active.add(campaign["first_evolution"])
    return active


# 이전 버전에서 남은 상태와 충돌하지 않도록 초기화합니다.
if st.session_state.get("genesis_version") != VERSION:
    st.session_state.genesis_version = VERSION
    st.session_state.genesis_world = None

world_state = st.session_state.get("genesis_world")
if isinstance(world_state, dict):
    world_state.update(FIXED_ENVIRONMENT)
    if "terrain_seed" not in world_state:
        world_state["terrain_seed"] = secrets.randbits(32)
    if "terrain_version" not in world_state:
        world_state["terrain_version"] = TERRAIN_GENERATION_VERSION
    ensure_prelife_discovery_state(world_state)

for key in ("genesis_speed", "genesis_solar", "genesis_volcano"):
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

    .stButton > button,
    .stDownloadButton > button {
        min-height: 2.75rem;
        height: auto;
        padding: 0.55rem 0.8rem;
        border-radius: 10px;
        border: 1px solid #64748B !important;
        background-color: #15263B !important;
        color: #F1F5F9 !important;
        white-space: normal;
        overflow-wrap: anywhere;
        line-height: 1.35;
    }

    .stButton > button div[data-testid="stMarkdownContainer"],
    .stButton > button div[data-testid="stMarkdownContainer"] p,
    .stDownloadButton > button div[data-testid="stMarkdownContainer"],
    .stDownloadButton > button div[data-testid="stMarkdownContainer"] p {
        color: inherit !important;
        white-space: normal;
        overflow-wrap: anywhere;
    }

    .stButton > button[kind="primary"] {
        border-color: #5EEAD4 !important;
        background-color: #115E59 !important;
        color: #FFFFFF !important;
    }

    .stButton > button:hover,
    .stButton > button:focus-visible,
    .stDownloadButton > button:hover,
    .stDownloadButton > button:focus-visible {
        border-color: #5EEAD4 !important;
        background-color: #243D58 !important;
        color: #FFFFFF !important;
    }

    .stButton > button[kind="primary"]:hover,
    .stButton > button[kind="primary"]:focus-visible {
        background-color: #0F766E !important;
    }

    .stButton > button:disabled,
    .stDownloadButton > button:disabled {
        border-color: #475569 !important;
        background-color: #1E293B !important;
        color: #94A3B8 !important;
        opacity: 1;
    }

    .genesis-selected-choice {
        min-height: 2.75rem;
        padding: 0.7rem 0.85rem;
        border: 1px solid #5EEAD4;
        border-radius: 10px;
        background: #115E59;
        color: #FFFFFF;
        line-height: 1.4;
        overflow-wrap: anywhere;
    }

    .genesis-selected-choice__label {
        color: #FFFFFF;
        font-weight: 700;
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


def advance_prelife_discoveries(world, simulated_seconds):
    ensure_prelife_discovery_state(world)
    if (
        world["cells"] > 0
        or world["temperature"] <= OCEAN_FORMATION_TEMPERATURE
        or len(world["prelife_discoveries"]["available_ids"])
        >= PRELIFE_DISCOVERY_CAPACITY
    ):
        return

    discoveries = world["prelife_discoveries"]
    discoveries["progress_seconds"] += simulated_seconds
    while (
        discoveries["progress_seconds"] >= PRELIFE_DISCOVERY_INTERVAL_SECONDS
        and len(discoveries["available_ids"]) < PRELIFE_DISCOVERY_CAPACITY
    ):
        discoveries["progress_seconds"] -= PRELIFE_DISCOVERY_INTERVAL_SECONDS
        discoveries["available_ids"].append(discoveries["next_id"])
        discoveries["next_id"] += 1
        add_log(world, "🔎 원시 지구에서 새로운 발견 지점이 준비되었습니다.")

    if len(discoveries["available_ids"]) >= PRELIFE_DISCOVERY_CAPACITY:
        discoveries["progress_seconds"] = 0.0


def collect_prelife_discovery(discovery_id):
    tick()
    world = st.session_state.genesis_world
    if world is None:
        return

    ensure_prelife_discovery_state(world)
    discoveries = world["prelife_discoveries"]
    if type(discovery_id) is not int or discovery_id not in discoveries["available_ids"]:
        return

    discoveries["available_ids"].remove(discovery_id)
    discoveries["claimed_total"] += 1
    world["energy"] += PRELIFE_DISCOVERY_REWARD
    add_log(
        world,
        f"✨ 발견 지점 조사 · 창조 에너지 +{PRELIFE_DISCOVERY_REWARD:g}",
    )


def objective_is_complete(world, objective_id):
    if objective_id == "ocean_formed":
        return world["ocean"] >= 10
    if objective_id == "first_cell":
        return world["cells"] >= 1
    if objective_id == "five_cells":
        return world["cells"] >= 5
    if objective_id == "first_evolution":
        return world["campaign"]["first_evolution"] is not None
    if objective_id == "first_life":
        return world["organisms"]["photosynthetic"] > 0
    return False


def objective_progress(world, objective_id):
    if objective_id == "ocean_formed":
        if world["ocean"] >= 10:
            return 1.0
        if world["temperature"] > OCEAN_FORMATION_TEMPERATURE:
            cooling_progress = (
                INITIAL_WORLD["temperature"] - world["temperature"]
            ) / (
                INITIAL_WORLD["temperature"] - OCEAN_FORMATION_TEMPERATURE
            )
            return min(max(cooling_progress, 0.0), 0.5)
        ocean_progress = min(world["ocean"] / 10, 1.0)
        return 0.5 + ocean_progress * 0.5
    if objective_id == "first_cell":
        ready = int(world["ocean"] >= 10) + int(
            0 <= world["temperature"] <= 60
        )
        return 1.0 if world["cells"] else ready / 2
    if objective_id == "five_cells":
        return min(world["cells"] / 5, 1.0)
    if objective_id == "first_evolution":
        return 1.0 if world["campaign"]["first_evolution"] else 0.0
    if objective_id == "first_life":
        return min(world["evolution_progress"]["photosynthetic"] / 30, 1.0)
    return 0.0


def reconcile_objectives(world):
    ensure_campaign_state(world)
    completed = world["campaign"]["completed_objectives"]
    for objective in OBJECTIVES:
        objective_id = objective["id"]
        if objective_id in completed:
            continue
        if not objective_is_complete(world, objective_id):
            break

        completed.append(objective_id)
        world["energy"] += objective["reward"]
        add_log(world, f"🎯 목표 완료: {objective['title']}")

        if objective_id == "first_life":
            campaign = world["campaign"]
            if "first_life" not in campaign["celebrated"]:
                campaign["celebrated"].append("first_life")
                campaign["celebration_pending"].append("first_life")


def discovery_is_available(world, event_id):
    if event_id == "ocean_formation":
        return world["ocean"] >= 10
    if event_id == "first_life":
        return world["organisms"]["photosynthetic"] > 0
    return False


def choose_discovery(event_id, choice_id):
    tick()
    world = st.session_state.genesis_world
    if world is None:
        return
    ensure_campaign_state(world)
    event = DISCOVERY_EVENTS.get(event_id)
    if (
        event is None
        or choice_id not in event["choices"]
        or not discovery_is_available(world, event_id)
        or world["campaign"]["discovery_choices"][event_id] is not None
    ):
        return

    choice = event["choices"][choice_id]
    world["campaign"]["discovery_choices"][event_id] = choice_id
    world["energy"] += choice["energy"]
    add_log(
        world,
        f"🔎 발견 선택: {event['title']} · {choice['label']}",
    )
    reconcile_objectives(world)


def choose_evolution(evolution_id):
    tick()
    world = st.session_state.genesis_world
    if world is None:
        return
    ensure_campaign_state(world)
    if (
        evolution_id not in EVOLUTION_TRAITS
        or world["cells"] < 5
        or world["campaign"]["first_evolution"] is not None
    ):
        return

    world["campaign"]["first_evolution"] = evolution_id
    trait = EVOLUTION_TRAITS[evolution_id]
    add_log(world, f"🧬 첫 진화 방향 선택: {trait['name']}")
    reconcile_objectives(world)


def evolution_effects(world):
    effects = {
        "energy_per_cell": 0.0,
        "growth_multiplier": 1.0,
        "adaptive_floor": 0.0,
    }

    for evolution_id in active_evolutions(world):
        trait = EVOLUTION_TRAITS[evolution_id]
        effects["energy_per_cell"] += trait["energy_per_cell"]
        effects["growth_multiplier"] *= trait["growth_multiplier"]
        effects["adaptive_floor"] = max(
            effects["adaptive_floor"],
            trait["adaptive_floor"],
        )

    campaign = world["campaign"]
    event_choices = (
        ("ocean_formation", "mineral_vein"),
        ("ocean_formation", "hydrothermal_chemistry"),
        ("first_life", "gene_archive"),
        ("first_life", "metabolic_enzyme"),
    )
    for event_id, choice_id in event_choices:
        if campaign["discovery_choices"][event_id] == choice_id:
            choice = DISCOVERY_EVENTS[event_id]["choices"][choice_id]
            effects["energy_per_cell"] += choice["energy_per_cell"]
            effects["growth_multiplier"] *= choice["growth_multiplier"]

    return effects


def export_world(world):
    ensure_campaign_state(world)
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
            **FIXED_ENVIRONMENT,
            "speed": SIMULATION_SPEED,
            "life_ready_logged": world["life_ready_logged"],
            "history": world["history"],
            "organisms": world["organisms"],
            "evolution_progress": world["evolution_progress"],
            "growth_progress": world["growth_progress"],
            "campaign": world["campaign"],
            "terrain_seed": world["terrain_seed"],
            "terrain_version": world["terrain_version"],
            "prelife_discoveries": world["prelife_discoveries"],
        },
    }


def validate_save_data(data):
    if not isinstance(data, dict) or set(data) != {"save_version", "world"}:
        raise ValueError("JSON 최상위 구조가 올바르지 않습니다.")

    save_version = data["save_version"]
    if type(save_version) is not int or save_version not in (1, 2, 3, 4, SAVE_VERSION):
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
    campaign_fields = {"campaign"}
    terrain_fields = {"terrain_seed", "terrain_version"}
    prelife_discovery_fields = {"prelife_discoveries"}
    fields = legacy_fields
    if save_version >= 2:
        fields |= biological_fields
    if save_version >= 3:
        fields |= campaign_fields
    if save_version >= 4:
        fields |= terrain_fields
    if save_version >= 5:
        fields |= prelife_discovery_fields
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
        "energy": "창조 에너지",
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
    if type(speed) is not int or speed not in (0, 1, 5, 20):
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
        for field, biological_values in (
            ("organisms", organisms),
            ("evolution_progress", evolution_progress),
            ("growth_progress", growth_progress),
        ):
            if (
                not isinstance(biological_values, dict)
                or set(biological_values) != set(SPECIES)
            ):
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

    campaign = new_campaign_state()
    if save_version >= 3:
        saved_campaign = saved_world["campaign"]
        if (
            not isinstance(saved_campaign, dict)
            or set(saved_campaign) != set(campaign)
        ):
            raise ValueError("목표와 발견 기록 형식이 올바르지 않습니다.")

        completed_objectives = saved_campaign["completed_objectives"]
        objective_ids = {objective["id"] for objective in OBJECTIVES}
        if (
            not isinstance(completed_objectives, list)
            or any(
                not isinstance(objective_id, str)
                or objective_id not in objective_ids
                for objective_id in completed_objectives
            )
            or len(set(completed_objectives)) != len(completed_objectives)
        ):
            raise ValueError("완료 목표 목록이 올바르지 않습니다.")

        discovery_choices = saved_campaign["discovery_choices"]
        if (
            not isinstance(discovery_choices, dict)
            or set(discovery_choices) != set(DISCOVERY_EVENTS)
        ):
            raise ValueError("발견 선택 기록이 올바르지 않습니다.")
        for event_id, event in DISCOVERY_EVENTS.items():
            choice = discovery_choices[event_id]
            if choice is not None and (
                not isinstance(choice, str)
                or choice not in event["choices"]
            ):
                raise ValueError("알 수 없는 발견 보상이 포함되어 있습니다.")
            if choice is not None and not (
                values["ocean"] >= 10
                if event_id == "ocean_formation"
                else biological_state["organisms"]["photosynthetic"] > 0
            ):
                raise ValueError("발견 조건을 만족하지 않은 이벤트가 선택되었습니다.")

        first_evolution = saved_campaign["first_evolution"]
        if first_evolution is not None and (
            not isinstance(first_evolution, str)
            or first_evolution not in EVOLUTION_TRAITS
        ):
            raise ValueError("첫 진화 선택이 올바르지 않습니다.")
        if first_evolution is not None and cells < 5:
            raise ValueError("세포 5개 이전에는 진화 선택을 할 수 없습니다.")

        researched_evolutions = saved_campaign["researched_evolutions"]
        research_to_evolution = {
            f"evolution_{evolution_id}": evolution_id
            for evolution_id in EVOLUTION_TRAITS
        }
        if (
            not isinstance(researched_evolutions, list)
            or any(
                not isinstance(evolution_id, str)
                or evolution_id not in EVOLUTION_TRAITS
                for evolution_id in researched_evolutions
            )
            or len(set(researched_evolutions)) != len(researched_evolutions)
        ):
            raise ValueError("후속 진화 연구 기록이 올바르지 않습니다.")
        if any(
            research_id in research
            and evolution_id not in researched_evolutions
            for research_id, evolution_id in research_to_evolution.items()
        ):
            raise ValueError("진화 연구 목록과 완료 연구가 일치하지 않습니다.")
        if {
            evolution_id
            for research_id, evolution_id in research_to_evolution.items()
            if research_id in research
        } != set(researched_evolutions):
            raise ValueError("후속 진화 연구 기록과 연구 목록이 일치하지 않습니다.")
        if researched_evolutions and first_evolution is None:
            raise ValueError("첫 진화 선택 이전에는 후속 진화를 연구할 수 없습니다.")
        if first_evolution in researched_evolutions:
            raise ValueError("이미 선택한 진화는 후속 연구로 다시 해금할 수 없습니다.")
        if any(
            f"evolution_{evolution_id}" in research
            and first_evolution is None
            for evolution_id in EVOLUTION_TRAITS
        ):
            raise ValueError("첫 진화 선택 이전에는 후속 진화를 연구할 수 없습니다.")

        for field in ("celebrated", "celebration_pending"):
            celebration_values = saved_campaign[field]
            if (
                not isinstance(celebration_values, list)
                or any(value != "first_life" for value in celebration_values)
                or len(set(celebration_values)) != len(celebration_values)
            ):
                raise ValueError("발견 연출 기록이 올바르지 않습니다.")
        if not set(saved_campaign["celebration_pending"]).issubset(
            saved_campaign["celebrated"]
        ):
            raise ValueError("대기 중인 연출 기록이 올바르지 않습니다.")
        if "first_life" in saved_campaign["celebrated"] and not biological_state[
            "organisms"
        ]["photosynthetic"]:
            raise ValueError("생명 발견 연출은 생물이 등장한 뒤에만 기록할 수 있습니다.")

        campaign = {
            "completed_objectives": completed_objectives,
            "discovery_choices": discovery_choices,
            "first_evolution": first_evolution,
            "researched_evolutions": researched_evolutions,
            "celebrated": saved_campaign["celebrated"],
            "celebration_pending": saved_campaign["celebration_pending"],
        }
        saved_state = {
            **values,
            "cells": cells,
            **biological_state,
            "campaign": campaign,
        }
        expected_completed = []
        for objective in OBJECTIVES:
            if not objective_is_complete(saved_state, objective["id"]):
                break
            expected_completed.append(objective["id"])
        if completed_objectives != expected_completed:
            raise ValueError("완료 목표와 현재 진행 상태가 일치하지 않습니다.")
    else:
        legacy_state = {
            **values,
            "cells": cells,
            **biological_state,
            "campaign": campaign,
        }
        for objective in OBJECTIVES:
            if not objective_is_complete(legacy_state, objective["id"]):
                break
            campaign["completed_objectives"].append(objective["id"])

    terrain_seed = (
        saved_world["terrain_seed"]
        if save_version >= 4
        else secrets.randbits(32)
    )
    terrain_version = (
        saved_world["terrain_version"]
        if save_version >= 4
        else TERRAIN_GENERATION_VERSION
    )
    if type(terrain_seed) is not int or not 0 <= terrain_seed <= 0xFFFFFFFF:
        raise ValueError("지형 seed 값이 올바르지 않습니다.")
    if (
        type(terrain_version) is not int
        or terrain_version != TERRAIN_GENERATION_VERSION
    ):
        raise ValueError("지원하지 않는 지형 생성 버전입니다.")

    prelife_discoveries = new_prelife_discovery_state()
    if save_version >= 5:
        saved_discoveries = saved_world["prelife_discoveries"]
        if (
            not isinstance(saved_discoveries, dict)
            or set(saved_discoveries) != set(prelife_discoveries)
        ):
            raise ValueError("원시 지구 발견 상태 형식이 올바르지 않습니다.")

        progress_seconds = saved_discoveries["progress_seconds"]
        next_id = saved_discoveries["next_id"]
        available_ids = saved_discoveries["available_ids"]
        claimed_total = saved_discoveries["claimed_total"]
        if (
            type(progress_seconds) not in (int, float)
            or (
                isinstance(progress_seconds, float)
                and not math.isfinite(progress_seconds)
            )
            or not 0 <= progress_seconds < PRELIFE_DISCOVERY_INTERVAL_SECONDS
        ):
            raise ValueError("발견 준비 진행 시간이 올바르지 않습니다.")
        if type(next_id) is not int or not 1 <= next_id <= 1_000_000_000_000:
            raise ValueError("발견 지점 번호가 올바르지 않습니다.")
        if (
            not isinstance(available_ids, list)
            or len(available_ids) > PRELIFE_DISCOVERY_CAPACITY
            or any(type(item) is not int or not 1 <= item < next_id for item in available_ids)
            or len(set(available_ids)) != len(available_ids)
        ):
            raise ValueError("준비된 발견 지점 목록이 올바르지 않습니다.")
        if type(claimed_total) is not int or not 0 <= claimed_total < next_id:
            raise ValueError("발견 보상 수령 기록이 올바르지 않습니다.")
        if claimed_total + len(available_ids) != next_id - 1:
            raise ValueError("발견 기회와 보상 수령 기록이 일치하지 않습니다.")
        prelife_discoveries = {
            "progress_seconds": float(progress_seconds),
            "next_id": next_id,
            "available_ids": available_ids,
            "claimed_total": claimed_total,
        }

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
        "campaign": campaign,
        "terrain_seed": terrain_seed,
        "terrain_version": terrain_version,
        "prelife_discoveries": prelife_discoveries,
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
        **FIXED_ENVIRONMENT,
        "last_tick": time.monotonic(),
        "life_ready_logged": saved["life_ready_logged"],
        "history": saved["history"],
        "organisms": saved["organisms"],
        "evolution_progress": saved["evolution_progress"],
        "growth_progress": saved["growth_progress"],
        "campaign": saved["campaign"],
        "terrain_seed": saved["terrain_seed"],
        "terrain_version": saved["terrain_version"],
        "prelife_discoveries": saved["prelife_discoveries"],
    }
    st.session_state.genesis_world = world
    for key in ("genesis_speed", "genesis_solar", "genesis_volcano"):
        st.session_state.pop(key, None)
    st.session_state.confirm_reset = False
    st.session_state.genesis_save_message = "저장 파일을 불러왔습니다."
    st.session_state.genesis_save_error = False
    reconcile_objectives(world)


def target_temperature(world):
    # 실제 기후 공식이 아닌 게임용 모델입니다.
    return (
        COOLING_TARGET_TEMPERATURE
        + (world["solar"] - 100) * 0.5
        + (world["volcano"] - 20) * 0.2
    )


def cool_temperature(current_temperature, target, elapsed_seconds):
    cooled_temperature = target + (
        current_temperature - target
    ) * math.exp(-COOLING_RATE * elapsed_seconds)
    return min(
        max(cooled_temperature, min(current_temperature, target)),
        max(current_temperature, target),
    )


def habitat_factor(world):
    """환경에 따른 생산 배율: 세포가 사라지지는 않습니다."""
    temperature = world["temperature"]

    if world["ocean"] < 10:
        factor = 0.0
    elif 0 <= temperature <= 50:
        factor = 1.0
    elif -20 <= temperature <= 80:
        factor = 0.25
    else:
        factor = 0.05

    return max(factor, evolution_effects(world)["adaptive_floor"])


def production_rate(world):
    multiplier = 1.0
    effects = evolution_effects(world)

    if "metabolism" in world["research"]:
        multiplier *= 2

    if "photosynthesis" in world["research"]:
        multiplier *= 3

    if "multicellular" in world["research"]:
        multiplier *= 5

    return (
        world["cells"]
        * multiplier
        * (1.0 + effects["energy_per_cell"])
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
            + species["growth_per_second"]
            * evolution_effects(world)["growth_multiplier"]
            * simulated_seconds
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
    ensure_campaign_state(world)
    now = time.monotonic()

    # 긴 연결 중단을 오프라인 보상으로 계산하지 않습니다.
    elapsed = min(max(now - world["last_tick"], 0.0), 5.0)
    world["last_tick"] = now

    world.update(FIXED_ENVIRONMENT)
    reconcile_objectives(world)
    simulated_seconds = elapsed

    if simulated_seconds <= 0:
        return

    biology_conditions = biological_conditions(world)

    # 환경 변화 전후의 생산량을 평균내어 자원을 계산합니다.
    old_rate = production_rate(world)

    target = target_temperature(world)

    # 시간 간격과 관계없이 목표 온도에 지수적으로 접근하고 목표를 넘지 않습니다.
    world["temperature"] = cool_temperature(
        world["temperature"],
        target,
        simulated_seconds,
    )
    advance_prelife_discoveries(world, simulated_seconds)

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
    reconcile_objectives(world)

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
            "life_ready_logged": False,
            "history": [
                "🌍 원시 지구 상태로 세계가 탄생했습니다."
            ],
            **new_biological_state(),
            "campaign": new_campaign_state(),
            "terrain_seed": secrets.randbits(32),
            "terrain_version": TERRAIN_GENERATION_VERSION,
            "prelife_discoveries": new_prelife_discovery_state(),
        }
    )

    st.session_state.genesis_world = world
    for key in ("genesis_speed", "genesis_solar", "genesis_volcano"):
        st.session_state.pop(key, None)
    st.session_state.confirm_reset = False


def restart_world():
    world = st.session_state.genesis_world
    if world is not None:
        create_world(world["name"])


def buy_cell():
    tick()
    world = st.session_state.genesis_world
    if world is None:
        return

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
    reconcile_objectives(world)


def buy_research(research_id):
    tick()
    world = st.session_state.genesis_world
    if world is None:
        return
    if research_id not in RESEARCH:
        return
    item = RESEARCH[research_id]
    ensure_campaign_state(world)

    if research_id in world["research"]:
        return

    required = item["requires"]

    if required and required not in world["research"]:
        return

    evolution_id = (
        research_id[len("evolution_"):]
        if research_id.startswith("evolution_")
        else None
    )
    if research_id.startswith("evolution_") and (
        world["campaign"]["first_evolution"] is None
        or evolution_id == world["campaign"]["first_evolution"]
        or evolution_id in world["campaign"]["researched_evolutions"]
    ):
        return

    if world["cells"] < 1 or world["energy"] < item["cost"]:
        return

    world["energy"] -= item["cost"]
    world["research"].append(research_id)
    if research_id.startswith("evolution_"):
        world["campaign"]["researched_evolutions"].append(evolution_id)

    add_log(
        world,
        f"🔬 {item['name']} 완료",
    )
    reconcile_objectives(world)


# ==================================================
# 3D 행성
# ==================================================

def render_planet(world):
    planet_component(
        terrain_seed=world["terrain_seed"],
        terrain_version=world["terrain_version"],
        temperature=world["temperature"],
        ocean=world["ocean"],
        plants=world["organisms"]["plants"],
        key="genesis_planet_view",
        default=None,
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

    ensure_campaign_state(world)
    reconcile_objectives(world)
    render_planet(world)
    if world["campaign"]["celebration_pending"]:
        world["campaign"]["celebration_pending"].remove("first_life")
        st.balloons()

    st.subheader(f"🌍 {world['name']}")

    st.caption(
        f"{stage_name(world)} · "
        f"경과 시간 {int(world['years']):,}년"
    )

    columns = st.columns(4)

    columns[0].metric(
        "✨ 창조 에너지",
        f"{world['energy']:,.1f}",
    )

    columns[1].metric(
        "🦠 세포",
        f"{world['cells']:,}",
    )

    columns[2].metric(
        "⚡ 현재 생산 / 현실 초",
        f"{production_rate(world) * SIMULATION_SPEED:,.1f}",
    )

    columns[3].metric(
        "🌡️ 평균 기온",
        f"{world['temperature']:,.1f} °C",
    )

    objective = next(
        (
            item
            for item in OBJECTIVES
            if item["id"]
            not in world["campaign"]["completed_objectives"]
        ),
        None,
    )
    if objective is None:
        st.success("🎉 첫 진화 장을 완료했습니다. 생태계와 연구를 계속 발전시키세요.")
    else:
        progress = objective_progress(world, objective["id"])
        reward_text = (
            f"완료 보상: 창조 에너지 +{objective['reward']:.0f}"
            if objective["reward"] > 0
            else "완료 시 첫 진화 선택이 열립니다."
        )
        with st.container(border=True):
            st.markdown(f"### 🎯 현재 목표: {objective['title']}")
            st.caption(objective["description"])
            if objective["id"] == "ocean_formed":
                if world["temperature"] > OCEAN_FORMATION_TEMPERATURE:
                    progress_label = (
                        f"지표 냉각 중 · "
                        f"{world['temperature']:.1f}°C → "
                        f"{OCEAN_FORMATION_TEMPERATURE:.0f}°C"
                    )
                else:
                    progress_label = f"바다 형성 중 · 바다 {world['ocean']:.1f}%"
                st.progress(progress, text=progress_label)
            else:
                st.progress(progress, text=f"진행률 {progress * 100:.0f}%")
            st.caption(reward_text)

    render_ecosystem(world)

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
            f"현재 창조 에너지 {world['energy']:.1f} "
            f"(세포 비용 {world['cell_cost']:.1f})"
        )
        st.progress(
            ready_conditions / 2,
            text=f"최초 세포 환경 조건 {ready_conditions}/2 충족",
        )

    discoveries = world["prelife_discoveries"]
    st.subheader("🔎 원시 지구 발견 지점")
    st.caption(
        "현재는 3D 표면 터치 대신 발견 카드를 제공합니다. "
        f"카드를 눌렀을 때만 창조 에너지 +{PRELIFE_DISCOVERY_REWARD:g}를 받고, "
        f"기회는 최대 {PRELIFE_DISCOVERY_CAPACITY}개까지 보관됩니다."
    )
    if discoveries["available_ids"]:
        discovery_columns = st.columns(
            min(len(discoveries["available_ids"]), PRELIFE_DISCOVERY_CAPACITY)
        )
        for column, discovery_id in zip(
            discovery_columns,
            discoveries["available_ids"],
        ):
            with column:
                with st.container(border=True):
                    st.markdown(f"**🪨 발견 지점 #{discovery_id}**")
                    st.caption("시간 제한 없음 · 조사 전까지 보관")
                    st.button(
                        f"발견 지점 조사 · 창조 에너지 +{PRELIFE_DISCOVERY_REWARD:g}",
                        key=f"prelife_discovery_{discovery_id}",
                        use_container_width=True,
                        on_click=collect_prelife_discovery,
                        args=(discovery_id,),
                    )
    if (
        world["cells"] == 0
        and world["temperature"] > OCEAN_FORMATION_TEMPERATURE
        and len(discoveries["available_ids"]) < PRELIFE_DISCOVERY_CAPACITY
    ):
        progress = (
            discoveries["progress_seconds"]
            / PRELIFE_DISCOVERY_INTERVAL_SECONDS
        )
        st.progress(
            progress,
            text=(
                "다음 발견 지점 준비 중 · "
                f"{discoveries['progress_seconds']:.0f}/"
                f"{PRELIFE_DISCOVERY_INTERVAL_SECONDS:.0f}초"
            ),
        )
    elif not discoveries["available_ids"]:
        st.caption("냉각 중 새로운 발견 지점이 일정 간격으로 준비됩니다.")
    elif len(discoveries["available_ids"]) >= PRELIFE_DISCOVERY_CAPACITY:
        st.caption("발견 기회가 가득 찼습니다. 시간 제한은 없으니 준비된 지점을 조사하세요.")

    available_events = [
        (event_id, event)
        for event_id, event in DISCOVERY_EVENTS.items()
        if discovery_is_available(world, event_id)
        and world["campaign"]["discovery_choices"][event_id] is None
    ]
    for event_id, event in DISCOVERY_EVENTS.items():
        selected_choice_id = world["campaign"]["discovery_choices"][event_id]
        if selected_choice_id is None:
            continue
        selected_choice = event["choices"][selected_choice_id]
        with st.container(border=True):
            st.subheader(f"🔎 발견 이벤트: {event['title']}")
            st.markdown(
                f"""
                <div class="genesis-selected-choice">
                  <span class="genesis-selected-choice__label">
                    ✓ 선택됨 · {selected_choice['label']}
                  </span><br>
                  {selected_choice['effect']}
                </div>
                """,
                unsafe_allow_html=True,
            )

    for event_id, event in available_events:
        with st.container(border=True):
            st.subheader(f"🔎 발견 이벤트: {event['title']}")
            st.caption(f"발견 조건: {event['trigger']} · 시간 제한 없음")
            choice_columns = st.columns(len(event["choices"]))
            for column, (choice_id, choice) in zip(
                choice_columns,
                event["choices"].items(),
            ):
                with column:
                    st.markdown(f"**{choice['label']}**")
                    st.caption(choice["effect"])
                    st.button(
                        "선택",
                        key=f"discovery_{event_id}_{choice_id}",
                        use_container_width=True,
                        on_click=choose_discovery,
                        args=(event_id, choice_id),
                    )

    if world["cells"] >= 5 and world["campaign"]["first_evolution"] is None:
        st.subheader("🧬 첫 진화 방향을 선택하세요")
        st.caption(
            "선택한 특성은 즉시 적용됩니다. 다른 두 특성은 이후 연구로 영구 해금할 수 있습니다."
        )
        evolution_columns = st.columns(len(EVOLUTION_TRAITS))
        for column, (evolution_id, trait) in zip(
            evolution_columns,
            EVOLUTION_TRAITS.items(),
        ):
            with column:
                with st.container(border=True):
                    st.markdown(f"### {trait['icon']} {trait['name']}")
                    st.caption(trait["effect"])
                    st.button(
                        f"{trait['name']} 선택",
                        key=f"evolution_choice_{evolution_id}",
                        type="primary",
                        use_container_width=True,
                        on_click=choose_evolution,
                        args=(evolution_id,),
                    )
    elif world["campaign"]["first_evolution"] is not None:
        selected_trait = EVOLUTION_TRAITS[
            world["campaign"]["first_evolution"]
        ]
        with st.container(border=True):
            st.subheader("🧬 선택한 첫 진화 방향")
            st.markdown(
                f"""
                <div class="genesis-selected-choice">
                  <span class="genesis-selected-choice__label">
                    ✓ 선택됨 · {selected_trait['icon']} {selected_trait['name']}
                  </span><br>
                  {selected_trait['effect']}
                </div>
                """,
                unsafe_allow_html=True,
            )

    st.subheader("🧬 생물 단계")
    st.caption(
        "생물 단계는 실제 진화 계통도를 정밀하게 재현한 것이 아닌 게임용 규칙입니다. "
        "육지가 존재하는 조건은 바다 비율 100% 미만으로 계산합니다. "
        "해금과 증식은 실제 경과 시간에 따라 진행됩니다."
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

    st.caption("▶ 자동 진행 중 · 고정 속도 ×1 · 실제 경과 시간 기준")

    st.subheader("🌍 환경 상태")
    environment_columns = st.columns(3)
    environment_columns[0].metric(
        "🌡️ 목표 온도",
        f"{target_temperature(world):.1f} °C",
    )
    environment_columns[1].metric(
        "🌊 바다 비율",
        f"{world['ocean']:.1f}%",
    )
    environment_columns[2].metric(
        "🌿 환경 생산 배율",
        f"×{habitat_factor(world):.2f}",
    )
    st.caption(
        "태양 에너지 100 · 화산 활동 20 고정. "
        "생산 최적 온도는 0~50°C이며, 환경이 나빠져도 현재 버전에서는 세포가 죽지 않습니다."
    )

    with st.container(border=True):
        st.subheader("🧬 생명과 진화")

        st.write(
            f"세포 구매 가격: "
            f"**{world['cell_cost']:,.2f} 창조 에너지**"
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
                "지구가 식고 바다가 형성되면 자동으로 생성할 수 있습니다."
            )
        else:
            st.caption(
                "세포는 기본적으로 초당 창조 에너지 1을 생산합니다. "
                "추가 구매 가격은 15%씩 증가합니다."
            )

        st.divider()

        research_columns = st.columns(3)
        for index, (research_id, item) in enumerate(RESEARCH.items()):
            column = research_columns[index % len(research_columns)]
            with column:
                completed = research_id in world["research"]
                required = item["requires"]

                unlocked = (
                    required is None
                    or required in world["research"]
                )
                evolution_id = (
                    research_id[len("evolution_"):]
                    if research_id.startswith("evolution_")
                    else None
                )
                if evolution_id is not None:
                    unlocked = (
                        unlocked
                        and world["campaign"]["first_evolution"] is not None
                        and evolution_id
                        != world["campaign"]["first_evolution"]
                        and evolution_id
                        not in world["campaign"]["researched_evolutions"]
                    )

                st.markdown(f"**{item['name']}**")
                st.caption(item["description"])

                label = (
                    "✅ 연구 완료"
                    if completed
                    else f"연구 · 창조 에너지 {item['cost']:,.0f}"
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
        export_world(world),
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


def render_ecosystem(world):
    water_fill = min(max(world["ocean"] / 70 * 100, 0), 100)
    heat = min(max((world["temperature"] - 15) / 985, 0), 1)
    life_icons = "".join(
        f"<span class='life'>{species['icon']}</span>"
        for species_id, species in SPECIES.items()
        if world["organisms"][species_id] > 0
    )
    if world["cells"] > 0:
        life_icons = f"<span class='life'>🦠</span>{life_icons}"

    st.markdown(
        f"""
        <div style="
            margin: 0.6rem 0 1rem;
            padding: 14px 18px;
            border: 1px solid #29405a;
            border-radius: 14px;
            background: linear-gradient(110deg, #10243a, #101b2c);
            display: flex;
            align-items: center;
            gap: 18px;
        ">
          <div style="
              position: relative;
              overflow: hidden;
              flex: 0 0 150px;
              height: 92px;
              border-radius: 50%;
              border: 2px solid #6c8499;
              background: linear-gradient(
                  180deg,
                  hsl(15, 42%, {22 + heat * 18:.0f}%),
                  hsl(25, 55%, {15 + heat * 14:.0f}%)
              );
              box-shadow: 0 0 20px rgba(49, 142, 194, 0.18);
          ">
            <div style="
                position: absolute;
                left: 0;
                right: 0;
                bottom: 0;
                height: {water_fill:.1f}%;
                min-height: {3 if world['ocean'] > 0 else 0}px;
                background: linear-gradient(180deg, #55c5d9, #1470ae 75%, #16477b);
                transition: height 0.8s ease;
                opacity: 0.94;
            "></div>
            <div style="
                position: absolute;
                inset: 0;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 5px;
                font-size: 19px;
                text-shadow: 0 1px 5px #07111c;
            ">{life_icons}</div>
          </div>
          <div style="color: #d7e5f3; line-height: 1.8;">
            <strong>행성 생태계</strong><br>
            바다 형성 {world['ocean']:.1f}% · 지표 {world['temperature']:.1f}°C<br>
            {("첫 생명이 행성에 자리 잡았습니다." if life_icons else
              "세포가 탄생하면 생태계에 생명이 나타납니다." if world["ocean"] >= 10 else
              "바다가 형성되면 행성 표면이 변합니다.")}
          </div>
        </div>
        """,
        unsafe_allow_html=True,
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
