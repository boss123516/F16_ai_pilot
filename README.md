# F16_ai_pilot

F16 AI Pilot 대회 프로젝트
프로젝트 소개
F16 AI Pilot은 실전 공중전 시뮬레이션을 기반으로, F16 전투기의 가능한 모든 기동을 AI가 직접 학습하고 수행하도록 설계된 자율 전투기 조종 AI 개발 대회입니다. 해당 대회는 중력(G-force)의 영향을 무시하고, 전투기가 기체 한계(G-limit)로 파괴되지 않는 선에서의 모든 기동을 허용하는 환경을 가정합니다. 목표는 위치 기하학적 요소를 활용한 전략적 전투 기동 구현입니다.

목표
G 제한을 제외한 현실 가능한 모든 기동에 대한 AI 구현

주어진 적기와의 위치/방향/속도 관계에 기반한 공중전 전략 최적화

공중전 상황에서 유리한 위치 확보 및 미사일 사용 타이밍 최적화

기술 스택
Simulation Framework: 제공되는 Custom Air Combat Environment (기반 엔진 미정)

AI/ML Framework: PyTorch, TensorFlow (선택 가능)

Visualization: Matplotlib, OpenGL (또는 Unity 기반 시각화 환경)

Deployment: 로컬 및 대회 전용 클라우드 서버

위치 기하학 요소 (Geometric Factors)
1. Aspect Angle
적기 꼬리를 기준으로 내 기체가 어느 각도에 위치해 있는지 나타냄

예시:

Aspect Angle = 180° → 적기가 나를 정면으로 향해 돌진 중

Aspect Angle = 0° → 적기가 내 반대 방향으로 비행 중 (내가 적기 꼬리를 쫓고 있음)

활용: 미사일 조준, 회피 기동 판단에 매우 중요

2. Angle Off
내 비행 방향과 적기의 위치 벡터 사이의 각도

즉, 내가 어느 정도 방향을 틀어야 적기를 향하게 되는지 나타냄

활용: 방향 전환, Lock-on 거리 유지 판단에 핵심 지표

프로젝트 구조 (예정)
bash
복사
편집
f16_ai_pilot/
├── data/                  # 시뮬레이션 로그 및 기동 데이터
├── docs/                  # 대회 룰북, 참고 논문
├── models/                # AI 모델 정의 및 학습 코드
├── envs/                  # 공중전 시뮬레이션 환경
├── utils/                 # 수학/물리 연산 유틸
├── tests/                 # 유닛 테스트
├── main.py                # 실행 진입점
├── README.md              # 프로젝트 소개 문서
└── requirements.txt       # Python 의존성 목록
