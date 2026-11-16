# evolution-lab
가상 진화 실험

3D 행성과 생물 발견 장면은 `planet_component/index.html`의 Streamlit 커스텀 컴포넌트에서 렌더링합니다. 배포 시 이 폴더를 앱과 함께 포함하고 브라우저에서 jsDelivr의 Three.js 0.170.0 모듈에 접근할 수 있어야 합니다. 별도 프런트엔드 빌드는 필요하지 않습니다.

최초 세포는 절차적 3D로 표시하며 외부 자산이 필요하지 않습니다. 나중에 교체할 GLB 모델 또는 PNG/WebP 이미지가 있으면 `planet_component/assets/creatures/`에 넣고 `app.py`의 `CREATURE_PRESENTATIONS`에서 표시 이름·설명·`renderer`·상대 `asset_path`를 설정하세요. 해당 폴더의 자산 파일은 `.gitignore`에 포함되어 공개 커밋되지 않습니다.

물 순환은 IAPWS SR1-86(1992)의 포화수증기압을 물의 삼중점~임계점 범위에서만 사용합니다. 한 시나리오에서는 대기와 지표 온도를 같게 두고, 일정 중력의 수직 기둥을 가정해 `p_total = g × (M_dry + M_vapor + M_cloud) / A`, `p_vapor = g × M_vapor / A`, `M_vapor,sat = p_sat × A / g`로 계산합니다. \(M_\mathrm{vapor}>M_\mathrm{vapor,sat}\)인 초과분은 구름 응결수로 옮기고, 구름 물은 설정된 강수 시간척도로 지표에 이동하며, 불포화 시에는 구름 물과 지표 물을 증발시켜 총 물 질량을 보존합니다.

게임 시나리오는 지구와 같은 행성 면적·중력, 건조 대기 1 bar 상당, 총 물 약 `1.337 × 10²¹ kg`을 가정합니다. 이는 USGS의 지구 전체 물 부피 약 `1.386 × 10⁹ km³` 중 바다가 약 96.5%라는 추정에 물의 밀도 약 `1000 kg/m³`를 적용해 얻은 **현대 지구 해양 규모의 근사치**이며, 초기 지구의 확정값이 아닙니다. 초기 1000°C도 게임 시작 조건입니다. 대기·구름·지표 사이의 물 질량은 보존하고, 강수 시간척도와 지표 물을 최대 70% 바다 표시 면적으로 바꾸는 매핑은 게임 설정입니다. 잠열, 얼음·승화, 연직 온도 구조 및 고압 비이상성은 계산하지 않습니다. 약 5분에 냉각 곡선의 80°C 기준점에 도달하는 설정도 물리 상수가 아닌 플레이 시간 압축값이며, 이 온도는 응결 조건이 아닙니다. 생물의 0~50°C 범위는 게임용 적합 조건으로 유지합니다.

참고: [IAPWS 포화 물성 릴리스](https://www.iapws.org/relguide/Supp-sat.html), [USGS 지구의 물 분포](https://www.usgs.gov/special-topics/water-science-school/science/how-much-water-there-earth).
