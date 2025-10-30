import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import database as db
import json
import os
from openai import OpenAI

client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

db.init_db()

st.set_page_config(
    page_title="전송장비 학습 대시보드",
    page_icon="📡",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #0066cc;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.8rem;
        font-weight: bold;
        color: #333;
        margin-top: 1.5rem;
        margin-bottom: 0.8rem;
    }
    .info-box {
        background-color: #f0f8ff;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #0066cc;
        margin: 1rem 0;
    }
    .warning-box {
        background-color: #fff3cd;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #ffc107;
        margin: 1rem 0;
    }
    .success-box {
        background-color: #d4edda;
        padding: 1rem;
        border-radius: 0.5rem;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 2rem;
    }
    .stTabs [data-baseweb="tab"] {
        height: 3rem;
        padding: 0 1.5rem;
    }
</style>
""", unsafe_allow_html=True)

equipment_comparison = {
    "MSPP": {
        "스위칭용량": "320G 이하",
        "전달기술": "SDH",
        "수용신호": "DS0, DS1E, DS1, DS3, STM-1/4/16/64, FE/GE (EoS)",
        "토폴로지": "Linear, Ring",
        "서비스": "E-Line (PtP, PtMP)",
        "동기기술": "외부, 망동기(SDH), 자체, 유도, Holdover",
        "회선관리": "기본 프레임내 Overhead 사용(SDH)",
        "회선보호": "50ms 절체 (H/W기반)",
        "대역효율": "대역 전용 (VC12/3/4)",
        "회선보안": "물리적(VC12/3/4) 회선분리",
        "주요용도": "TDM신호 전송",
        "장점": "안정적인 TDM 전송, H/W 기반 빠른 절체",
        "대표모델": "WMSP-340A, BMSP-4016C, AMSP-C1200A"
    },
    "PTN": {
        "스위칭용량": "400G 이하",
        "전달기술": "MPLS-TP",
        "수용신호": "FE, GE, 10GE, DS0/DS1E/STM-1 (CES)",
        "토폴로지": "Linear, Ring, Mesh",
        "서비스": "E-Line, E-Lan, E-Tree (PtP, PtMP, MPtMP)",
        "동기기술": "외부, 망동기(Sync-E), 자체, 유도, Holdover",
        "회선관리": "별도 OAM Packet 사용(MPLS-TP)",
        "회선보호": "50ms 절체 (S/W기반)",
        "대역효율": "대역 공유 (CIR, PIR)",
        "회선보안": "논리적(PW) 회선분리",
        "주요용도": "Ethernet 신호 전송",
        "장점": "유연한 대역 공유, 다양한 서비스",
        "대표모델": "APN-400A, APN-200A, APN-100A, APN-60A, APN-50A, APN-20A/D"
    },
    "POTN": {
        "스위칭용량": "2.4Tbps 이하",
        "전달기술": "MPLS-TP, OTN, DWDM",
        "수용신호": "FE, GE, 10GE, 100GE, STM-1/4/16/64, OTU-1/2/4, DS1E/STM-1 (CES)",
        "토폴로지": "Linear, Ring, Mesh",
        "서비스": "E-Line, E-Lan, E-Tree (PtP, PtMP, MPtMP)",
        "동기기술": "외부, 망동기(Sync-E), 자체, 유도, Holdover",
        "회선관리": "기본 프레임내 Overhead(OTN) + OAM Packet(MPLS-TP)",
        "회선보호": "50ms 절체 (H/W 및 S/W 기반)",
        "대역효율": "대역전용(ODU0/1/2/F) 및 대역 공유(CIR/PIR)",
        "회선보안": "물리적(ODU) 및 논리적(PW) 회선분리",
        "주요용도": "Ethernet 신호 전송 (대용량)",
        "장점": "초대용량, OTN+MPLS-TP 통합, DWDM 지원",
        "대표모델": "OPN-3100, OPN-3000, OPN-1000"
    }
}

equipment_specs = pd.DataFrame({
    "모델명": ["OPN-3100", "OPN-3000", "OPN-1000", "APN-400A", "APN-200A", "APN-100A", "APN-60A", "APN-50A", "APN-20A", "APN-20D", "APN-S40"],
    "분류": ["POTN", "POTN", "POTN", "PTN", "PTN", "PTN", "PTN", "PTN", "PTN", "PTN", "PTN"],
    "스위칭용량": ["2.4Tera", "1.16Tera", "560G", "400G", "200G", "200G", "64G", "60G", "32G/14G", "32G/14G", "44G"],
    "크기(U)": [14, 12, 6, 12, 8, 4, 2, 1, 1, 1, 1],
    "10GbE포트": [240, 240, 96, 56, 32, 24, 4, 4, 2, 2, 2],
    "1GbE포트": [400, 400, 160, 192, 96, 96, 24, 20, 14, 14, 16],
    "소모전력(W)": [1956, 1560, 1150, 1000, 400, 400, 120, 100, 20, 35, 55],
    "주요특징": [
        "초대용량 백본, 100GE/OTU4 지원, DWDM",
        "백본용, OTU4 지원, DWDM",
        "지역망용, OTU4 지원, DWDM",
        "대용량 액세스, CES 지원",
        "중용량 액세스, CES 지원",
        "중용량 액세스, CES Ext",
        "소용량 액세스, CES 지원",
        "소형 액세스",
        "Compact 1U, CES 지원",
        "채널MUX 일체형, DSO 지원",
        "LEA-256 암호화, PQC/양자암호"
    ]
})

detailed_equipment = {
    "OPN-3100": {
        "용량": "2.4Tbps",
        "크기": "19인치 14U",
        "주요인터페이스": [
            "OTU4*2 (200G): 10 Port",
            "OTU4 (100G): 20 Port", 
            "OTU2 (10G): 200 Port",
            "100GbE: 20 Port",
            "10GbE: 240 Port",
            "1GbE: 400 Port"
        ],
        "적용분야": "백본망 (장거리망) 구성",
        "특징": [
            "단일 플랫폼에서 OTN/Ethernet/SDH/CES 통합 수용",
            "DWDM 16ch/40ch Mux/Demux, EDFA 증폭기 지원",
            "주요 유니트 이중화로 고가용성 제공",
            "ODU 스위칭 및 MPLS-TP 동시 지원"
        ]
    },
    "OPN-3000": {
        "용량": "1.16Tbps",
        "크기": "19인치 12U",
        "주요인터페이스": [
            "OTU4 (100G): 10 Port",
            "OTU2 (10G): 100 Port",
            "10GbE: 240 Port",
            "1GbE: 400 Port",
            "STM-1 (CES): 80 Port"
        ],
        "적용분야": "백본망 및 지역간선망",
        "특징": [
            "중대용량 백본 장비",
            "DWDM 지원",
            "OTN/MPLS-TP 통합",
            "효율적인 공간 활용 (12U)"
        ]
    },
    "OPN-1000": {
        "용량": "560Gbps",
        "크기": "19인치 6U",
        "주요인터페이스": [
            "OTU4 (100G): 4 Port",
            "OTU2 (10G): 40 Port",
            "10GbE: 96 Port",
            "1GbE: 160 Port"
        ],
        "적용분야": "지역망 및 COT",
        "특징": [
            "컴팩트한 지역망 장비",
            "DWDM 지원",
            "6U 소형 설계로 공간 절약",
            "OTN 기능 제공"
        ]
    },
    "APN-400A": {
        "용량": "400Gbps",
        "크기": "19인치 12U",
        "주요인터페이스": [
            "10GbE: 56 Port",
            "1GbE: 192 Port",
            "STM-1 (CES): 24 Port"
        ],
        "적용분야": "대용량 액세스망, COT",
        "특징": [
            "대용량 PTN 액세스",
            "CES 기능으로 TDM 수용",
            "MPLS-TP 기반",
            "다양한 서비스 제공 (E-Line/E-LAN/E-Tree)"
        ]
    },
    "APN-200A": {
        "용량": "200Gbps",
        "크기": "19인치 8U",
        "주요인터페이스": [
            "10GbE: 32 Port",
            "1GbE: 96 Port",
            "STM-1 (CES): 24 Port",
            "E1 (CES): 96 Port"
        ],
        "적용분야": "중용량 액세스망, Drop용 RT",
        "특징": [
            "중용량 PTN",
            "CES 지원",
            "프리밴 서비스 적용",
            "유연한 대역 관리"
        ]
    },
    "APN-100A": {
        "용량": "200Gbps",
        "크기": "19인치 4U",
        "주요인터페이스": [
            "10GbE: 24 Port",
            "1GbE: 96 Port"
        ],
        "적용분야": "중소용량 액세스망",
        "특징": [
            "CES Ext 전용",
            "컴팩트 4U",
            "외부 CES Shelf 연동",
            "효율적인 공간 활용"
        ]
    },
    "APN-60A": {
        "용량": "64Gbps",
        "크기": "19인치 2U",
        "주요인터페이스": [
            "10GbE: 4 Port",
            "1GbE: 24 Port",
            "STM-1 (CES): 16 Port",
            "E1 (CES): 16 Port"
        ],
        "적용분야": "소용량 액세스망, RT",
        "특징": [
            "소용량 PTN",
            "CES 내장",
            "2U 컴팩트",
            "경제적인 소규모 구성"
        ]
    },
    "APN-50A": {
        "용량": "60Gbps",
        "크기": "19인치 1U",
        "주요인터페이스": [
            "10GbE: 4 Port",
            "1GbE: 20 Port"
        ],
        "적용분야": "소형 액세스망, 지사/지점",
        "특징": [
            "초소형 1U 컴팩트 설계",
            "작은 공간에 최적화",
            "소규모 사업장용",
            "경제적인 솔루션"
        ]
    },
    "APN-20D": {
        "용량": "14G/32Gbps",
        "크기": "19인치 1U",
        "주요인터페이스": [
            "10GbE: 2 Port",
            "1GbE: 6~14 Port",
            "E1: 6 Port (이중화)",
            "DSO (FXS/2WE&M): 16 Port"
        ],
        "적용분야": "저속급 서비스 (E1/DSO), 음성 서비스",
        "특징": [
            "채널MUX 일체형",
            "DSO 서비스 제공 (FXS/2WE&M)",
            "외장형 배터리 연결 가능",
            "상면 및 투자비 절감"
        ]
    },
    "APN-S40": {
        "용량": "44Gbps",
        "크기": "19인치 1U",
        "주요인터페이스": [
            "10GbE: 2 Port",
            "1GbE: 16 Port"
        ],
        "적용분야": "보안 전송망, 암호화 서비스",
        "특징": [
            "LEA-256 암호화 (국내표준)",
            "PQC (양자내성암호) 지원",
            "QKD (양자암호) 연동 가능",
            "MACsec (Layer 2) 암호화",
            "KCMVP 인증 진행 중"
        ]
    }
}

encryption_comparison = {
    "OTNsec": {
        "암호화계위": "Layer 1 (전송 네트워크 구간)",
        "암호화단위": "ODU 단위",
        "전송효율": "100% (별도 Overhead 사용)",
        "암호화알고리즘": "AES-256, LEA-256 (KCMVP인증)",
        "KEY": "공용키, 양자키(QKD), Hybrid 키",
        "장점": [
            "대역폭 유실 없음",
            "암호등급 높음 (양자키 적용)",
            "KCMVP 인증"
        ],
        "단점": [
            "투자비 높음"
        ],
        "적용장비": "OPN 시리즈"
    },
    "MACsec": {
        "암호화계위": "Layer 2 (이더넷 링크 구간)",
        "암호화단위": "이더넷 패킷 단위",
        "전송효율": "패킷 크기에 따라 손실 (최대 3~40%)",
        "암호화알고리즘": "AES-128 (기본), AES-256 (선택)",
        "KEY": "공용키",
        "장점": [
            "투자비 낮음",
            "표준 프로토콜"
        ],
        "단점": [
            "대역폭 유실",
            "암호등급 낮음 (공용키만 사용)"
        ],
        "적용장비": "일반 이더넷 장비"
    },
    "APN-S40 (PQC)": {
        "암호화계위": "Layer 2 (이더넷 링크 구간)",
        "암호화단위": "이더넷 패킷 단위 (VLAN)",
        "전송효율": "패킷 크기에 따라 손실 (최대 3~40%)",
        "암호화알고리즘": "LEA-256 (국내표준)",
        "KEY": "공용키, 양자내성키(PQC), 양자키(QKD), Hybrid 키",
        "장점": [
            "양자내성키 Software 구현",
            "양자키(QKD) 연동 가능",
            "투자비 낮음 (QKD 미적용시)",
            "KCMVP 인증 진행 중"
        ],
        "단점": [
            "대역폭 유실"
        ],
        "적용장비": "APN-S40"
    }
}

glossary = {
    "MSPP": {
        "정의": "Multi-Service Provisioning Platform",
        "설명": "다양한 서비스를 하나의 플랫폼에서 제공하는 전송장비로, 주로 TDM(Time Division Multiplexing) 기반의 SDH 신호를 전송합니다.",
        "쉬운설명": "여러 종류의 통신 신호를 하나의 장비로 처리하는 전송장비입니다. 주로 전통적인 전화선이나 전용회선 서비스에 사용됩니다."
    },
    "PTN": {
        "정의": "Packet Transport Network",
        "설명": "패킷 기반 전송 네트워크로, MPLS-TP 기술을 사용하여 이더넷 신호를 효율적으로 전송합니다.",
        "쉬운설명": "인터넷 데이터를 효율적으로 전송하는 장비입니다. 대역폭을 유연하게 공유할 수 있어 경제적입니다."
    },
    "POTN": {
        "정의": "Packet Optical Transport Network",
        "설명": "패킷과 광전송 기술을 결합한 차세대 전송 네트워크로, OTN, MPLS-TP, DWDM 기술을 통합하여 초대용량 전송을 지원합니다.",
        "쉬운설명": "PTN의 진화된 형태로, 광케이블을 이용해 엄청난 양의 데이터를 장거리로 전송할 수 있습니다. 백본망에 주로 사용됩니다."
    },
    "MPLS-TP": {
        "정의": "Multi-Protocol Label Switching - Transport Profile",
        "설명": "MPLS 기술을 전송망에 최적화한 프로토콜로, 패킷에 라벨을 붙여 빠르고 효율적으로 전달합니다.",
        "쉬운설명": "데이터에 주소 라벨을 붙여서 빠르게 목적지까지 전달하는 기술입니다. 택배에 송장을 붙이는 것과 비슷합니다."
    },
    "OTN": {
        "정의": "Optical Transport Network",
        "설명": "광전송 네트워크 기술로, ODU 프레임을 사용하여 대용량 데이터를 안정적으로 전송합니다.",
        "쉬운설명": "광케이블로 대용량 데이터를 안전하게 전송하는 기술입니다. 데이터 손실 없이 장거리 전송이 가능합니다."
    },
    "SDH": {
        "정의": "Synchronous Digital Hierarchy",
        "설명": "동기식 디지털 계위 방식으로, 전통적인 TDM 기반 전송 기술입니다.",
        "쉬운설명": "과거부터 사용해온 전송 방식으로, 시간을 나눠서 여러 신호를 동시에 보냅니다. 전화망에서 많이 사용했습니다."
    },
    "DWDM": {
        "정의": "Dense Wavelength Division Multiplexing",
        "설명": "고밀도 파장 분할 다중화 기술로, 하나의 광섬유에 여러 파장의 빛을 동시에 전송하여 용량을 대폭 증가시킵니다.",
        "쉬운설명": "하나의 광케이블에 여러 색깔(파장)의 빛을 동시에 보내서 용량을 크게 늘리는 기술입니다. 한 도로에 여러 차선을 만드는 것과 비슷합니다."
    },
    "CES": {
        "정의": "Circuit Emulation Service",
        "설명": "패킷 네트워크에서 TDM 회선을 에뮬레이션하는 기술로, E1이나 STM-1 같은 전통적 신호를 패킷망에서 전송할 수 있게 합니다.",
        "쉬운설명": "옛날 방식의 전화선 신호를 최신 인터넷 망에서도 사용할 수 있게 변환해주는 기술입니다."
    },
    "E1": {
        "정의": "E-carrier level 1",
        "설명": "2.048 Mbps의 전송속도를 가진 디지털 전송 표준으로, 주로 전용회선이나 음성 서비스에 사용됩니다.",
        "쉬운설명": "전용회선이나 PBX(사내교환기) 연결에 사용하는 통신 선로입니다. 약 30개의 전화 통화를 동시에 처리할 수 있습니다."
    },
    "STM-1": {
        "정의": "Synchronous Transport Module level 1",
        "설명": "155 Mbps의 전송속도를 가진 SDH의 기본 전송 단위입니다.",
        "쉬운설명": "SDH 방식에서 사용하는 기본 전송 단위로, E1보다 훨씬 빠른 속도를 제공합니다."
    },
    "Sync-E": {
        "정의": "Synchronous Ethernet",
        "설명": "이더넷에 동기 클럭 기능을 추가한 기술로, 네트워크 전체의 시간을 정확하게 맞춥니다.",
        "쉬운설명": "네트워크의 모든 장비가 같은 시계를 보도록 하는 기술입니다. 정확한 타이밍이 필요한 서비스에 중요합니다."
    },
    "OAM": {
        "정의": "Operations, Administration and Maintenance",
        "설명": "네트워크의 운용, 관리, 유지보수를 위한 기능 및 프로토콜입니다.",
        "쉬운설명": "네트워크가 잘 동작하는지 감시하고, 문제가 생기면 찾아내는 기능입니다."
    },
    "QoS": {
        "정의": "Quality of Service",
        "설명": "서비스 품질을 보장하기 위한 기술로, 중요한 트래픽에 우선순위를 부여합니다.",
        "쉬운설명": "중요한 데이터를 먼저 보내서 서비스 품질을 유지하는 기술입니다. VIP 전용 통로를 만드는 것과 비슷합니다."
    },
    "LEA-256": {
        "정의": "Lightweight Encryption Algorithm 256-bit",
        "설명": "한국에서 개발한 경량 암호화 알고리즘으로, 국내 표준 암호입니다.",
        "쉬운설명": "한국형 암호화 기술로, 데이터를 안전하게 보호합니다. KCMVP 국내 인증을 받았습니다."
    },
    "QKD": {
        "정의": "Quantum Key Distribution",
        "설명": "양자역학 원리를 이용한 암호키 분배 기술로, 이론적으로 해킹이 불가능합니다.",
        "쉬운설명": "양자물리학을 이용한 최첨단 보안 기술입니다. 누군가 엿보려고 하면 즉시 알 수 있습니다."
    },
    "PQC": {
        "정의": "Post-Quantum Cryptography",
        "설명": "미래의 양자컴퓨터 공격에도 안전한 암호화 기술입니다.",
        "쉬운설명": "미래에 나올 슈퍼컴퓨터(양자컴퓨터)로도 풀 수 없는 강력한 암호 기술입니다."
    }
}

network_configs = {
    "전용회선": {
        "설명": "고객 간 점대점(Point-to-Point) 전용 통신 서비스",
        "구성": [
            "고객사 ↔ 수용국사(COT) ↔ 백본국사 ↔ 수용국사(COT) ↔ 고객사",
            "지역간선망: 1G/10G Ring (PTN 또는 MSPP)",
            "백본망: RoADM/OTN (PTN 기간망)",
            "선로구간: CWDM/DWDM"
        ],
        "적용장비": "OPN-3000, APN-200A, MSPP 장비",
        "특징": [
            "안정적인 전용 대역 제공",
            "보안성 우수",
            "SLA 보장"
        ]
    },
    "인터넷(프리밴)": {
        "설명": "업무용 전용회선 + 인터넷용 회선을 하나로 제공하는 서비스",
        "구성": [
            "업무용: 1G/10G Ring (PTN 기간망)",
            "인터넷용: IP망 Core 연결",
            "백본국사: FBS 스위치 + PTN COT (OPN-3000)",
            "Drop용 RT: APN-200A"
        ],
        "적용장비": "OPN-3000, APN-200A, FBS 스위치",
        "특징": [
            "전용회선 + 인터넷 통합 제공",
            "비용 효율적",
            "유연한 대역 관리"
        ]
    },
    "저속급(E1/DSO)": {
        "설명": "음성 및 저속 데이터 서비스 (E1, DSO)",
        "구성": [
            "10G Ring ↔ 10G Ring ↔ 1G Ring",
            "채널MUX 일체형 PTN장비 (APN-20D)",
            "FXS/2WE&M 포트로 DSO 서비스 제공"
        ],
        "적용장비": "APN-20D, AMSP-M155U",
        "특징": [
            "단일 PTN장비에서 채널급 서비스 제공",
            "외장형 배터리 연동으로 상면 절감",
            "부대설비 투자비 절감 (FADP, 정류기, 배터리, 채널MUX 불필요)",
            "단일 EMS 통합 관리"
        ]
    }
}

def show_home():
    st.markdown('<p class="main-header">📡 전송장비 학습 대시보드</p>', unsafe_allow_html=True)
    st.markdown("**SK브로드밴드 B2B 영업 담당자를 위한 전송장비 기술 가이드**")
    
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### 🎯 MSPP")
        st.markdown("**전통적 TDM 전송장비**")
        st.markdown("- 스위칭: ~320G")
        st.markdown("- 기술: SDH")
        st.markdown("- 용도: TDM 신호")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### 🚀 PTN")
        st.markdown("**패킷 전송 네트워크**")
        st.markdown("- 스위칭: ~400G")
        st.markdown("- 기술: MPLS-TP")
        st.markdown("- 용도: Ethernet")
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col3:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("### ⚡ POTN")
        st.markdown("**차세대 광전송 네트워크**")
        st.markdown("- 스위칭: ~2.4Tbps")
        st.markdown("- 기술: OTN+MPLS-TP+DWDM")
        st.markdown("- 용도: 대용량 백본")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("### 📊 주요 장비 성능 비교")
    
    fig = go.Figure()
    
    capacity_map = {
        "2.4Tera": 2400,
        "1.16Tera": 1160,
        "560G": 560,
        "400G": 400,
        "200G": 200,
        "64G": 64,
        "60G": 60,
        "32G/14G": 32,
        "44G": 44
    }
    
    df_chart = equipment_specs.copy()
    df_chart["용량(G)"] = df_chart["스위칭용량"].apply(lambda x: capacity_map.get(x, 0))
    df_chart = df_chart.sort_values("용량(G)", ascending=True)
    
    colors = {"POTN": "#0066cc", "PTN": "#00cc66", "MSPP": "#cc6600"}
    
    fig.add_trace(go.Bar(
        y=df_chart["모델명"],
        x=df_chart["용량(G)"],
        orientation='h',
        marker=dict(
            color=[colors[cat] for cat in df_chart["분류"]],
        ),
        text=df_chart["스위칭용량"],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="장비별 스위칭 용량 비교",
        xaxis_title="스위칭 용량 (Gbps)",
        yaxis_title="모델명",
        height=500,
        showlegend=False
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    st.markdown("---")
    st.markdown("### 📋 전체 장비 스펙 요약")
    st.dataframe(
        equipment_specs[["모델명", "분류", "스위칭용량", "크기(U)", "10GbE포트", "1GbE포트", "소모전력(W)"]],
        use_container_width=True,
        hide_index=True
    )

def show_comparison():
    st.markdown('<p class="main-header">⚖️ 기술 비교</p>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["📊 MSPP/PTN/POTN 비교", "🔒 암호화 기술 비교"])
    
    with tab1:
        st.markdown("### MSPP vs PTN vs POTN 상세 비교")
        
        comparison_df = pd.DataFrame({
            "비교항목": ["스위칭용량", "전달기술", "토폴로지", "회선보호", "대역효율", "주요용도"],
            "MSPP": [
                "320G 이하",
                "SDH",
                "Linear, Ring",
                "50ms 절체 (H/W)",
                "대역 전용",
                "TDM신호 전송"
            ],
            "PTN": [
                "400G 이하",
                "MPLS-TP",
                "Linear, Ring, Mesh",
                "50ms 절체 (S/W)",
                "대역 공유 (CIR, PIR)",
                "Ethernet 전송"
            ],
            "POTN": [
                "2.4Tbps 이하",
                "MPLS-TP, OTN, DWDM",
                "Linear, Ring, Mesh",
                "50ms 절체 (H/W+S/W)",
                "대역전용+공유 혼용",
                "대용량 Ethernet"
            ]
        })
        
        st.dataframe(comparison_df, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        st.markdown("### 📈 기술별 특성 레이더 차트")
        
        categories = ['용량', '유연성', '효율성', '안정성', '확장성']
        
        fig = go.Figure()
        
        fig.add_trace(go.Scatterpolar(
            r=[3, 2, 3, 5, 2],
            theta=categories,
            fill='toself',
            name='MSPP',
            line=dict(color='#cc6600')
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=[4, 5, 4, 4, 4],
            theta=categories,
            fill='toself',
            name='PTN',
            line=dict(color='#00cc66')
        ))
        
        fig.add_trace(go.Scatterpolar(
            r=[5, 5, 5, 5, 5],
            theta=categories,
            fill='toself',
            name='POTN',
            line=dict(color='#0066cc')
        ))
        
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 5])),
            showlegend=True,
            height=500
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("#### MSPP 장점")
            st.markdown("✅ 안정적인 TDM 전송")
            st.markdown("✅ H/W 기반 빠른 절체")
            st.markdown("✅ 검증된 기술")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown("#### PTN 장점")
            st.markdown("✅ 유연한 대역 공유")
            st.markdown("✅ 다양한 서비스 제공")
            st.markdown("✅ Mesh 구성 가능")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("#### POTN 장점")
            st.markdown("✅ 초대용량 (2.4Tbps)")
            st.markdown("✅ OTN+MPLS-TP 통합")
            st.markdown("✅ DWDM 지원")
            st.markdown("</div>", unsafe_allow_html=True)
    
    with tab2:
        st.markdown("### 🔐 암호화 기술 상세 비교")
        
        enc_comparison = pd.DataFrame({
            "항목": ["암호화 계위", "암호화 단위", "전송 효율", "암호화 알고리즘", "투자비", "암호 등급"],
            "OTNsec": [
                "Layer 1",
                "ODU 단위",
                "100% (손실 없음)",
                "AES-256, LEA-256",
                "높음",
                "높음 (양자키)"
            ],
            "MACsec": [
                "Layer 2",
                "패킷 단위",
                "3~40% 손실",
                "AES-128/256",
                "낮음",
                "낮음 (공용키)"
            ],
            "APN-S40 (PQC)": [
                "Layer 2",
                "패킷/VLAN 단위",
                "3~40% 손실",
                "LEA-256",
                "낮음",
                "높음 (PQC/QKD)"
            ]
        })
        
        st.dataframe(enc_comparison, use_container_width=True, hide_index=True)
        
        st.markdown("---")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown("#### OTNsec")
            st.markdown("**최고 보안 + 성능**")
            st.markdown("- ✅ 대역폭 손실 없음")
            st.markdown("- ✅ 양자키 지원")
            st.markdown("- ❌ 투자비 높음")
            st.markdown("- 적용: OPN 시리즈")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown('<div class="warning-box">', unsafe_allow_html=True)
            st.markdown("#### MACsec")
            st.markdown("**표준 보안**")
            st.markdown("- ✅ 투자비 낮음")
            st.markdown("- ✅ 표준 프로토콜")
            st.markdown("- ❌ 대역폭 손실")
            st.markdown("- 적용: 일반 장비")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col3:
            st.markdown('<div class="success-box">', unsafe_allow_html=True)
            st.markdown("#### APN-S40 (PQC)")
            st.markdown("**차세대 보안**")
            st.markdown("- ✅ 양자내성암호")
            st.markdown("- ✅ 양자키 연동")
            st.markdown("- ✅ 국내표준(LEA)")
            st.markdown("- 적용: APN-S40")
            st.markdown("</div>", unsafe_allow_html=True)
        
        st.markdown("---")
        st.markdown("### 🔑 KEY 생성 방식")
        
        key_info = pd.DataFrame({
            "KEY 방식": ["공용키 (Public Key)", "양자내성키 (PQC)", "양자키 (QKD)", "Hybrid Key"],
            "설명": [
                "일반적인 암호키 생성 방식",
                "양자컴퓨터 공격에 안전한 키",
                "양자역학 기반 절대 안전 키",
                "공용키 + PQC 또는 QKD 조합"
            ],
            "보안수준": ["보통", "높음", "매우높음", "매우높음"],
            "적용기술": ["MACsec", "APN-S40", "OTNsec, APN-S40", "OTNsec, APN-S40"]
        })
        
        st.dataframe(key_info, use_container_width=True, hide_index=True)

def show_equipment_details():
    st.markdown('<p class="main-header">🔍 장비 상세 정보</p>', unsafe_allow_html=True)
    
    category = st.selectbox(
        "장비 분류 선택",
        ["POTN", "PTN", "PTN 특수장비"]
    )
    
    if category == "POTN":
        models = ["OPN-3100", "OPN-3000", "OPN-1000"]
    elif category == "PTN":
        models = ["APN-400A", "APN-200A", "APN-100A", "APN-60A", "APN-50A"]
    else:
        models = ["APN-20D", "APN-S40"]
    
    selected_model = st.selectbox("모델 선택", models)
    
    if selected_model in detailed_equipment:
        equipment = detailed_equipment[selected_model]
        
        col1, col2 = st.columns([1, 2])
        
        with col1:
            st.markdown('<div class="info-box">', unsafe_allow_html=True)
            st.markdown(f"### {selected_model}")
            st.markdown(f"**스위칭 용량:** {equipment['용량']}")
            st.markdown(f"**크기:** {equipment['크기']}")
            st.markdown(f"**적용 분야:**")
            st.markdown(f"{equipment['적용분야']}")
            st.markdown("</div>", unsafe_allow_html=True)
        
        with col2:
            st.markdown("#### 주요 인터페이스")
            for interface in equipment["주요인터페이스"]:
                st.markdown(f"- {interface}")
        
        st.markdown("---")
        st.markdown("#### 주요 특징")
        
        cols = st.columns(2)
        for idx, feature in enumerate(equipment["특징"]):
            with cols[idx % 2]:
                st.markdown(f"✅ {feature}")
        
        st.markdown("---")
        
        spec_row = equipment_specs[equipment_specs["모델명"] == selected_model]
        if not spec_row.empty:
            st.markdown("#### 상세 스펙")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("10GbE 포트", f"{spec_row.iloc[0]['10GbE포트']} Port")
            with col2:
                st.metric("1GbE 포트", f"{spec_row.iloc[0]['1GbE포트']} Port")
            with col3:
                st.metric("크기", f"{spec_row.iloc[0]['크기(U)']} U")
            with col4:
                st.metric("소모전력", f"{spec_row.iloc[0]['소모전력(W)']} W")

def show_glossary():
    st.markdown('<p class="main-header">📚 전문 용어 사전</p>', unsafe_allow_html=True)
    st.markdown("**전송장비 관련 주요 용어를 쉽게 이해하세요**")
    
    st.markdown("---")
    
    category_filter = st.selectbox(
        "카테고리 선택",
        ["전체", "장비 유형", "전송 기술", "프로토콜", "보안/암호화", "기타"]
    )
    
    category_mapping = {
        "장비 유형": ["MSPP", "PTN", "POTN"],
        "전송 기술": ["SDH", "OTN", "DWDM", "CES"],
        "프로토콜": ["MPLS-TP", "Sync-E", "OAM"],
        "보안/암호화": ["LEA-256", "QKD", "PQC"],
        "기타": ["E1", "STM-1", "QoS"]
    }
    
    if category_filter == "전체":
        filtered_terms = list(glossary.keys())
    else:
        filtered_terms = category_mapping.get(category_filter, [])
    
    search_term = st.text_input("🔍 용어 검색", placeholder="예: MPLS, OTN, 암호화...")
    
    if search_term:
        filtered_terms = [term for term in glossary.keys() if search_term.upper() in term.upper()]
    
    for term in filtered_terms:
        if term in glossary:
            with st.expander(f"**{term}** - {glossary[term]['정의']}", expanded=False):
                st.markdown(f"**기술적 설명:**")
                st.markdown(glossary[term]['설명'])
                
                st.markdown(f"**쉬운 설명:**")
                st.markdown(f"💡 {glossary[term]['쉬운설명']}")

def show_network_config():
    st.markdown('<p class="main-header">🌐 망 구성도 가이드</p>', unsafe_allow_html=True)
    
    config_type = st.selectbox(
        "망 구성 유형 선택",
        ["전용회선", "인터넷(프리밴)", "저속급(E1/DSO)"]
    )
    
    config = network_configs[config_type]
    
    st.markdown(f"### {config_type} 서비스")
    
    st.markdown('<div class="info-box">', unsafe_allow_html=True)
    st.markdown(f"**서비스 설명:** {config['설명']}")
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    st.markdown("#### 망 구성")
    
    for item in config["구성"]:
        st.markdown(f"- {item}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("#### 적용 장비")
        st.markdown(config["적용장비"])
        st.markdown("</div>", unsafe_allow_html=True)
    
    with col2:
        st.markdown('<div class="info-box">', unsafe_allow_html=True)
        st.markdown("#### 주요 특징")
        for feature in config["특징"]:
            st.markdown(f"✅ {feature}")
        st.markdown("</div>", unsafe_allow_html=True)
    
    st.markdown("---")
    
    if config_type == "전용회선":
        st.markdown("#### 전용회선 망 구성 플로우")
        st.markdown("""
        ```
        고객사 A
            ↓ (선로)
        수용국사 (COT)
            ↓ (1G/10G Ring - PTN/MSPP)
        백본국사 
            ↓ (RoADM/OTN - 장거리망)
        백본국사
            ↓ (1G/10G Ring - PTN/MSPP)
        수용국사 (COT)
            ↓ (선로)
        고객사 B
        ```
        """)
        
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("**💡 영업 포인트:**")
        st.markdown("- 고객 전용 대역으로 안정적인 품질 보장")
        st.markdown("- SLA 제공으로 비즈니스 연속성 확보")
        st.markdown("- 보안이 중요한 금융/공공기관에 최적")
        st.markdown("</div>", unsafe_allow_html=True)
    
    elif config_type == "인터넷(프리밴)":
        st.markdown("#### 프리밴 서비스 구성")
        st.markdown("""
        ```
        고객사
            ↓
        1G/10G Ring (PTN)
            ↓
        백본국사 (FBS)
            ├─→ PTN 기간망 (업무용 전용회선)
            └─→ IP망 Core (인터넷)
        ```
        """)
        
        st.markdown('<div class="warning-box">', unsafe_allow_html=True)
        st.markdown("**💡 영업 포인트:**")
        st.markdown("- 전용회선 + 인터넷을 하나의 회선으로 통합")
        st.markdown("- 투자비 절감 (회선 통합)")
        st.markdown("- 유연한 대역 조절 가능")
        st.markdown("- 중소기업에 경제적인 솔루션")
        st.markdown("</div>", unsafe_allow_html=True)
    
    else:
        st.markdown("#### 저속급 서비스 구성 (채널MUX 일체형)")
        st.markdown("""
        ```
        고객사
            ↓ (E1 또는 DSO)
        APN-20D (채널MUX 일체형)
            ↓ (1G Ring)
        상위 PTN 장비
            ↓ (10G Ring)
        백본망
        ```
        """)
        
        st.markdown('<div class="success-box">', unsafe_allow_html=True)
        st.markdown("**💡 우리넷 차별점:**")
        st.markdown("- **기존 방식:** PTN + 별도 채널MUX + FADP + 정류기 + 배터리 필요")
        st.markdown("- **APN-20D:** 단일 장비로 모든 기능 통합")
        st.markdown("- **비용 절감:** 부대설비 투자비 대폭 절감")
        st.markdown("- **상면 절감:** 랙 공간 효율 향상")
        st.markdown("- **관리 편의:** 단일 EMS로 통합 관리")
        st.markdown("</div>", unsafe_allow_html=True)

def perform_search(query):
    results = []
    query_lower = query.lower()
    
    for model, specs in detailed_equipment.items():
        if query_lower in model.lower():
            results.append({
                "유형": "장비",
                "제목": model,
                "내용": f"{specs['용량']} | {specs['적용분야']}",
                "카테고리": "장비 상세"
            })
        elif any(query_lower in feature.lower() for feature in specs.get("특징", [])):
            results.append({
                "유형": "장비",
                "제목": model,
                "내용": f"{specs['용량']} | {specs['적용분야']}",
                "카테고리": "장비 상세"
            })
    
    for term, info in glossary.items():
        if query_lower in term.lower() or query_lower in info['설명'].lower() or query_lower in info['쉬운설명'].lower():
            results.append({
                "유형": "용어",
                "제목": term,
                "내용": info['쉬운설명'],
                "카테고리": "용어 사전"
            })
    
    for tech, details in equipment_comparison.items():
        if query_lower in tech.lower():
            results.append({
                "유형": "기술",
                "제목": tech,
                "내용": details['주요용도'],
                "카테고리": "기술 비교"
            })
        for key, value in details.items():
            if isinstance(value, str) and query_lower in value.lower():
                results.append({
                    "유형": "기술",
                    "제목": tech,
                    "내용": f"{key}: {value}",
                    "카테고리": "기술 비교"
                })
                break
    
    return results

def show_search():
    st.markdown('<p class="main-header">🔍 통합 검색</p>', unsafe_allow_html=True)
    
    search_query = st.text_input(
        "🔎 검색어를 입력하세요",
        placeholder="예: MPLS, OPN-3000, 암호화, 전용회선...",
        key="main_search"
    )
    
    if search_query:
        results = perform_search(search_query)
        
        if results:
            st.success(f"**{len(results)}개의 결과를 찾았습니다.**")
            
            for idx, result in enumerate(results):
                with st.expander(f"[{result['유형']}] {result['제목']}", expanded=(idx < 3)):
                    st.markdown(f"**카테고리:** {result['카테고리']}")
                    st.markdown(f"**내용:** {result['내용']}")
        else:
            st.warning("검색 결과가 없습니다. 다른 검색어를 시도해보세요.")
    else:
        st.info("장비명, 기술명, 용어 등을 검색해보세요.")
        
        st.markdown("### 💡 추천 검색어")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**장비 검색**")
            if st.button("OPN-3000"):
                st.session_state.main_search = "OPN-3000"
                st.rerun()
            if st.button("APN-200A"):
                st.session_state.main_search = "APN-200A"
                st.rerun()
        
        with col2:
            st.markdown("**기술 검색**")
            if st.button("MPLS-TP"):
                st.session_state.main_search = "MPLS-TP"
                st.rerun()
            if st.button("암호화"):
                st.session_state.main_search = "암호화"
                st.rerun()
        
        with col3:
            st.markdown("**서비스 검색**")
            if st.button("전용회선"):
                st.session_state.main_search = "전용회선"
                st.rerun()
            if st.button("프리밴"):
                st.session_state.main_search = "프리밴"
                st.rerun()

def recommend_equipment():
    st.markdown('<p class="main-header">💡 장비 추천 시스템</p>', unsafe_allow_html=True)
    st.markdown("**고객의 요구사항을 입력하시면 최적의 장비를 추천해드립니다.**")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 📝 요구사항 입력")
        
        service_type = st.selectbox(
            "서비스 유형",
            ["전용회선", "인터넷(프리밴)", "저속급(E1/DSO)", "보안 전송", "백본망", "액세스망"]
        )
        
        capacity_need = st.selectbox(
            "필요 용량",
            ["소용량 (100G 이하)", "중용량 (100G~500G)", "대용량 (500G~1T)", "초대용량 (1T 이상)"]
        )
        
        space_constraint = st.selectbox(
            "공간 제약",
            ["여유있음", "보통 (6U 이하)", "제약있음 (2U 이하)"]
        )
        
        security_need = st.checkbox("암호화 필요")
        ces_need = st.checkbox("TDM 신호 수용 필요 (CES)")
        dwdm_need = st.checkbox("DWDM 필요")
    
    with col2:
        st.markdown("### 🎯 추천 결과")
        
        if st.button("장비 추천 받기", type="primary"):
            recommendations = []
            
            if service_type == "보안 전송" or security_need:
                recommendations.append({
                    "모델": "APN-S40",
                    "이유": "LEA-256 암호화 지원, PQC/QKD 연동 가능",
                    "적합도": "⭐⭐⭐⭐⭐"
                })
            
            if service_type == "백본망" or "초대용량" in capacity_need:
                if "여유있음" in space_constraint:
                    recommendations.append({
                        "모델": "OPN-3100",
                        "이유": "2.4Tbps 초대용량, DWDM 지원, 100GE/OTU4*2",
                        "적합도": "⭐⭐⭐⭐⭐"
                    })
                recommendations.append({
                    "모델": "OPN-3000",
                    "이유": "1.16Tbps 대용량, 12U 컴팩트, DWDM 지원",
                    "적합도": "⭐⭐⭐⭐⭐"
                })
            
            if service_type == "저속급(E1/DSO)":
                recommendations.append({
                    "모델": "APN-20D",
                    "이유": "채널MUX 일체형, DSO 서비스 제공, 1U 초소형",
                    "적합도": "⭐⭐⭐⭐⭐"
                })
            
            if service_type in ["전용회선", "인터넷(프리밴)"]:
                if "중용량" in capacity_need or "대용량" in capacity_need:
                    recommendations.append({
                        "모델": "APN-200A",
                        "이유": "200G 중용량, CES 지원, 프리밴 적용",
                        "적합도": "⭐⭐⭐⭐"
                    })
                    recommendations.append({
                        "모델": "OPN-3000",
                        "이유": "1.16T 대용량, COT/백본 적용",
                        "적합도": "⭐⭐⭐⭐⭐"
                    })
                
                if "소용량" in capacity_need:
                    if "제약있음" in space_constraint:
                        recommendations.append({
                            "모델": "APN-50A",
                            "이유": "60G 소용량, 1U 초소형",
                            "적합도": "⭐⭐⭐⭐"
                        })
                    else:
                        recommendations.append({
                            "모델": "APN-60A",
                            "이유": "64G 소용량, CES 지원, 2U",
                            "적합도": "⭐⭐⭐⭐"
                        })
            
            if ces_need and not service_type == "저속급(E1/DSO)":
                recommendations.append({
                    "모델": "APN-200A",
                    "이유": "STM-1/E1 CES 지원, 중용량",
                    "적합도": "⭐⭐⭐⭐"
                })
            
            if dwdm_need:
                recommendations.append({
                    "모델": "OPN-3100",
                    "이유": "DWDM 16/40ch 지원, 초대용량",
                    "적합도": "⭐⭐⭐⭐⭐"
                })
            
            if not recommendations:
                recommendations.append({
                    "모델": "APN-100A",
                    "이유": "범용 중용량 PTN 장비, 4U",
                    "적합도": "⭐⭐⭐"
                })
            
            st.success(f"**{len(recommendations)}개의 장비를 추천합니다!**")
            
            for idx, rec in enumerate(recommendations, 1):
                st.markdown(f"### {idx}. {rec['모델']}")
                st.markdown(f"**적합도:** {rec['적합도']}")
                st.markdown(f"**추천 이유:** {rec['이유']}")
                
                if st.button(f"{rec['모델']} 상세보기", key=f"detail_{idx}"):
                    st.session_state.selected_equipment = rec['모델']
                    st.session_state.goto_detail = True
                
                st.markdown("---")

def show_bookmarks():
    st.markdown('<p class="main-header">⭐ 즐겨찾기</p>', unsafe_allow_html=True)
    
    bookmarks = db.get_bookmarks()
    
    if bookmarks:
        st.success(f"**{len(bookmarks)}개의 즐겨찾기가 있습니다.**")
        
        for bookmark in bookmarks:
            col1, col2 = st.columns([4, 1])
            
            with col1:
                st.markdown(f"### [{bookmark.item_type}] {bookmark.title}")
                st.markdown(f"**카테고리:** {bookmark.category}")
                st.markdown(f"**추가일:** {bookmark.created_at.strftime('%Y-%m-%d %H:%M')}")
            
            with col2:
                if st.button("삭제", key=f"del_bm_{bookmark.id}"):
                    if db.remove_bookmark(bookmark.item_id):
                        st.success("삭제되었습니다!")
                        st.rerun()
            
            st.markdown("---")
    else:
        st.info("저장된 즐겨찾기가 없습니다.")
        st.markdown("### 💡 사용 방법")
        st.markdown("- 장비 상세 정보, 용어 사전 등에서 ⭐ 버튼을 클릭하여 즐겨찾기에 추가할 수 있습니다.")

def show_learning_progress():
    st.markdown('<p class="main-header">📈 학습 진도</p>', unsafe_allow_html=True)
    
    pages = ["홈 (대시보드)", "기술 비교", "장비 상세 정보", "용어 사전", "망 구성도", "장비 추천", "퀴즈"]
    
    progress_data = db.get_learning_progress()
    completed_pages = {p.page_name for p in progress_data if p.completed}
    
    total_pages = len(pages)
    completed_count = len(completed_pages)
    progress_percent = (completed_count / total_pages) * 100
    
    st.markdown("### 📊 전체 진행률")
    st.progress(progress_percent / 100)
    st.markdown(f"**{completed_count}/{total_pages}** 페이지 완료 ({progress_percent:.1f}%)")
    
    st.markdown("---")
    st.markdown("### 📋 페이지별 진도")
    
    for page in pages:
        col1, col2 = st.columns([3, 1])
        
        with col1:
            completed = page in completed_pages
            status = "✅" if completed else "⬜"
            st.markdown(f"{status} **{page}**")
        
        with col2:
            if completed:
                if st.button("미완료", key=f"undo_{page}"):
                    db.update_learning_progress(page, False)
                    st.rerun()
            else:
                if st.button("완료", key=f"complete_{page}"):
                    db.update_learning_progress(page, True)
                    st.rerun()
    
    if completed_count == total_pages:
        st.balloons()
        st.success("🎉 축하합니다! 모든 학습을 완료하셨습니다!")

def show_quiz():
    st.markdown('<p class="main-header">✏️ 전송장비 퀴즈</p>', unsafe_allow_html=True)
    st.markdown("**전송장비에 대한 이해도를 테스트해보세요!**")
    
    quizzes = {
        "기본": [
            {
                "question": "MSPP, PTN, POTN 중 가장 큰 스위칭 용량을 가진 것은?",
                "options": ["MSPP", "PTN", "POTN"],
                "answer": "POTN",
                "explanation": "POTN은 최대 2.4Tbps의 스위칭 용량을 가지고 있어 세 가지 중 가장 큽니다."
            },
            {
                "question": "MPLS-TP 기술을 사용하는 전송장비는?",
                "options": ["MSPP만", "PTN과 POTN", "MSPP와 PTN"],
                "answer": "PTN과 POTN",
                "explanation": "PTN과 POTN은 MPLS-TP 기술을 사용합니다. MSPP는 SDH 기술을 사용합니다."
            },
            {
                "question": "채널MUX 일체형 PTN 장비는?",
                "options": ["APN-20D", "APN-200A", "OPN-3000"],
                "answer": "APN-20D",
                "explanation": "APN-20D는 채널MUX 기능이 내장된 일체형 장비로, DSO 서비스를 제공합니다."
            }
        ],
        "중급": [
            {
                "question": "LEA-256 암호화를 지원하는 장비는?",
                "options": ["APN-S40", "OPN-3000", "MSPP"],
                "answer": "APN-S40",
                "explanation": "APN-S40는 국내 표준 LEA-256 암호화를 지원하며, PQC와 QKD 연동도 가능합니다."
            },
            {
                "question": "DWDM을 지원하지 않는 장비는?",
                "options": ["OPN-3100", "OPN-3000", "APN-200A"],
                "answer": "APN-200A",
                "explanation": "APN-200A는 PTN 장비로 DWDM을 지원하지 않습니다. OPN 시리즈는 DWDM을 지원합니다."
            },
            {
                "question": "프리밴 서비스에 주로 사용되는 장비는?",
                "options": ["APN-20D", "OPN-3000과 APN-200A", "MSPP"],
                "answer": "OPN-3000과 APN-200A",
                "explanation": "프리밴 서비스는 전용회선+인터넷 통합 서비스로, OPN-3000과 APN-200A가 주로 사용됩니다."
            }
        ]
    }

    
    tab1, tab2, tab3 = st.tabs(["📝 퀴즈 풀기","📊 결과 보기", "🏆 통계"])
    
    with tab1:
        quiz_level = st.selectbox("난이도 선택", ["기본", "중급"])
        selected_quiz = quizzes[quiz_level]
        
        st.markdown(f"### {quiz_level} 퀴즈 ({len(selected_quiz)}문제)")
        
        if 'quiz_answers' not in st.session_state:
            st.session_state.quiz_answers = {}
        
        for idx, q in enumerate(selected_quiz):
            st.markdown(f"**Q{idx+1}. {q['question']}**")
            answer = st.radio(
                "답을 선택하세요:",
                q['options'],
                key=f"q_{quiz_level}_{idx}"
            )
            st.session_state.quiz_answers[f"{quiz_level}_{idx}"] = answer
            st.markdown("---")
        
        if st.button("제출하기", type="primary"):
            score = 0
            results = []
            
            for idx, q in enumerate(selected_quiz):
                user_answer = st.session_state.quiz_answers.get(f"{quiz_level}_{idx}")
                correct = user_answer == q['answer']
                if correct:
                    score += 1
                
                results.append({
                    "question": q['question'],
                    "user_answer": user_answer,
                    "correct_answer": q['answer'],
                    "correct": correct,
                    "explanation": q['explanation']
                })
            
            db.save_quiz_result(quiz_level, score, len(selected_quiz), results)
            
            st.session_state.quiz_results = results
            st.session_state.quiz_score = score
            st.session_state.quiz_total = len(selected_quiz)
            st.session_state.show_quiz_result = True
            st.rerun()
    
    with tab2:
        if hasattr(st.session_state, 'show_quiz_result') and st.session_state.show_quiz_result:
            score = st.session_state.quiz_score
            total = st.session_state.quiz_total
            results = st.session_state.quiz_results
            
            percentage = (score / total) * 100
            
            if percentage >= 80:
                st.success(f"🎉 훌륭합니다! {score}/{total}점 ({percentage:.0f}%)")
            elif percentage >= 60:
                st.info(f"👍 잘하셨습니다! {score}/{total}점 ({percentage:.0f}%)")
            else:
                st.warning(f"💪 조금 더 학습이 필요합니다. {score}/{total}점 ({percentage:.0f}%)")
            
            st.markdown("---")
            st.markdown("### 상세 결과")
            
            for idx, result in enumerate(results, 1):
                if result['correct']:
                    st.markdown(f"**Q{idx}. {result['question']}** ✅")
                else:
                    st.markdown(f"**Q{idx}. {result['question']}** ❌")
                
                st.markdown(f"- 내 답: {result['user_answer']}")
                if not result['correct']:
                    st.markdown(f"- 정답: {result['correct_answer']}")
                st.markdown(f"- 해설: {result['explanation']}")
                st.markdown("---")
            
            if st.button("다시 풀기"):
                st.session_state.quiz_answers = {}
                st.session_state.show_quiz_result = False
                st.rerun()
        else:
            st.info("퀴즈를 풀고 제출하면 결과를 확인할 수 있습니다.")
    
    with tab3:
        results = db.get_quiz_results()
        
        if results:
            st.markdown(f"### 총 {len(results)}회 퀴즈 응시")
            
            for result in results[:10]:
                percentage = (result.score / result.total_questions) * 100
                st.markdown(f"**{result.quiz_id}** - {result.score}/{result.total_questions}점 ({percentage:.0f}%) - {result.completed_at.strftime('%Y-%m-%d %H:%M')}")
        else:
            st.info("아직 퀴즈 응시 기록이 없습니다.")

def call_openai_web_search(query: str, country: str = "KR"):
    """
    OpenAI Responses API (web_search_preview) 호출.
    반환: [{'text': str, 'citations': [{'title':..., 'url':...}]}]
    """
    if not os.getenv("OPENAI_API_KEY"):
        return [{"text": "⚠️ OPENAI_API_KEY가 설정되지 않았습니다.", "citations": []}]

    try:
        input_text = (
            f"Today is {pd.Timestamp.now(tz='Asia/Seoul').strftime('%Y-%m-%d')}. "
            f"Country context: {country}. "
            f"Find positive, verifiable news related to: {query}. "
            "Summarize concisely (3-5 bullets). Provide inline citations."
        )

        resp = client.responses.create(
            model="gpt-4.1",
            tools=[{"type": "web_search_preview"}],  # 최소 형태(중요)
            input=input_text,
            temperature=0.3,
            top_p=1.0
        )

        results = []
        for item in getattr(resp, "output", []) or []:
            if getattr(item, "type", "") == "message":
                for c in getattr(item, "content", []) or []:
                    if getattr(c, "type", "") == "output_text":
                        text = getattr(c, "text", "") or ""
                        cites = []
                        for ann in getattr(c, "annotations", []) or []:
                            if getattr(ann, "type", "") == "url_citation":
                                cites.append({
                                    "title": getattr(ann, "title", "") or "Source",
                                    "url": getattr(ann, "url", "") or ""
                                })
                        results.append({"text": text, "citations": cites})

        if not results:
            results = [{"text": "검색 결과를 파싱하지 못했습니다. 쿼리를 바꿔 다시 시도해보세요.", "citations": []}]
        return results

    except Exception as e:
        msg = getattr(e, "message", str(e))
        return [{"text": f"⚠️ OpenAI 호출 오류: {msg}", "citations": []}]

def show_openai_web_search_page():
    st.markdown("## 📰 웹 서치 (OpenAI)")
    st.markdown("키워드를 입력하면 ‘관련 최신 뉴스(주가 관련 뉴스 제외)/블로그 자료’ 등을 중심으로 간단 요약과 출처를 보여줍니다.")
    st.markdown("---")

    col1, col2 = st.columns([3, 1])
    with col1:
        query = st.text_input(
            "검색어",
            value="MSPP 장비",
            placeholder="예: AI datacenter, 5G enterprise ..."
        )
    with col2:
        country = st.selectbox("국가", options=["KR", "US", "JP", "EU"], index=0)

    if st.button("검색 실행", type="primary"):
        with st.spinner("OpenAI 웹서치 중..."):
            results = call_openai_web_search(query, country)

        for idx, r in enumerate(results, 1):
            st.markdown(f"### 결과 {idx}")
            st.markdown(r.get("text", ""))
            if r.get("citations"):
                st.markdown("**🔗 출처**")
                for c in r["citations"]:
                    url = c.get("url") or ""
                    title = c.get("title") or "Source"
                    if url:
                        st.markdown(f"- [{title}]({url})")
            st.markdown("---")
    else:
        st.info("검색어를 입력하고 **검색 실행**을 눌러주세요.")

st.sidebar.title("📡 전송장비 학습")
st.sidebar.markdown("---")

st.sidebar.markdown("### 🔍 빠른 검색")
quick_search = st.sidebar.text_input("검색", placeholder="장비명, 기술명...")
if quick_search:
    st.session_state.quick_search_query = quick_search
    st.session_state.show_search_page = True

st.sidebar.markdown("---")

page = st.sidebar.radio(
    "메뉴 선택",
    ["🏠 홈 (대시보드)", "🔎 통합 검색", "⚖️ 기술 비교", "🔍 장비 상세 정보",
     "📚 용어 사전", "🌐 망 구성도", "💡 장비 추천", "⭐ 즐겨찾기",
     "📈 학습 진도", "✏️ 퀴즈", "📰 웹 서치 (OpenAI)"]
)

st.sidebar.markdown("---")
st.sidebar.markdown("### 📥 원본 자료")
st.sidebar.markdown("**PDF 파일 다운로드:**")
st.sidebar.markdown("- [전송장비 교육자료](attached_assets/1.%20전송장비%20교육(전송망%20및%20암호화장비)_V2.0_250121_1761714836860.pdf)")
st.sidebar.markdown("- [우리넷 장비 소개](attached_assets/우리넷%20전송장비%20소개자료(PTN,MSPP,CWDM)_V7_241114_1761714836861.pdf)")

st.sidebar.markdown("---")
st.sidebar.markdown("### 💡 빠른 참조")

with st.sidebar.expander("주요 장비 분류"):
    st.markdown("**POTN (백본)**")
    st.markdown("- OPN-3100 (2.4T)")
    st.markdown("- OPN-3000 (1.16T)")
    st.markdown("- OPN-1000 (560G)")
    st.markdown("")
    st.markdown("**PTN (액세스)**")
    st.markdown("- APN-400A (대용량)")
    st.markdown("- APN-200A (중용량)")
    st.markdown("- APN-60A (소용량)")
    st.markdown("- APN-20D (채널MUX)")
    st.markdown("- APN-S40 (암호화)")

with st.sidebar.expander("서비스별 적용 장비"):
    st.markdown("**전용회선**")
    st.markdown("→ OPN-3000, APN-200A")
    st.markdown("")
    st.markdown("**프리밴**")
    st.markdown("→ OPN-3000, APN-200A")
    st.markdown("")
    st.markdown("**E1/DSO**")
    st.markdown("→ APN-20D")
    st.markdown("")
    st.markdown("**보안 전송**")
    st.markdown("→ APN-S40, OPN (OTNsec)")

st.sidebar.markdown("---")
st.sidebar.info("**Version 1.0**  \n개발: SK브로드밴드 B2B 영업지원 (김연홍M)  \n최종 업데이트: 2025년 10월 30일")

if hasattr(st.session_state, 'show_search_page') and st.session_state.show_search_page:
    page = "🔎 통합 검색"
    if hasattr(st.session_state, 'quick_search_query'):
        st.session_state.main_search = st.session_state.quick_search_query
        delattr(st.session_state, 'quick_search_query')
    st.session_state.show_search_page = False

if page == "🏠 홈 (대시보드)":
    show_home()
elif page == "🔎 통합 검색":
    show_search()
elif page == "⚖️ 기술 비교":
    show_comparison()
elif page == "🔍 장비 상세 정보":
    show_equipment_details()
elif page == "📚 용어 사전":
    show_glossary()
elif page == "🌐 망 구성도":
    show_network_config()
elif page == "💡 장비 추천":
    recommend_equipment()
elif page == "⭐ 즐겨찾기":
    show_bookmarks()
elif page == "📈 학습 진도":
    show_learning_progress()
elif page == "✏️ 퀴즈":
    show_quiz()
elif page == "📰 웹 서치 (OpenAI)":
    show_openai_web_search_page()