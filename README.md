# evolution-lab
가상 진화 실험

3D 행성과 생물 발견 장면은 `planet_component/index.html`의 Streamlit 커스텀 컴포넌트에서 렌더링합니다. 배포 시 이 폴더를 앱과 함께 포함하고 브라우저에서 jsDelivr의 Three.js 0.170.0 모듈에 접근할 수 있어야 합니다. 별도 프런트엔드 빌드는 필요하지 않습니다.

최초 세포는 절차적 3D로 표시하며 외부 자산이 필요하지 않습니다. 나중에 교체할 GLB 모델 또는 PNG/WebP 이미지가 있으면 `planet_component/assets/creatures/`에 넣고 `app.py`의 `CREATURE_PRESENTATIONS`에서 표시 이름·설명·`renderer`·상대 `asset_path`를 설정하세요. 해당 폴더의 자산 파일은 `.gitignore`에 포함되어 공개 커밋되지 않습니다.
