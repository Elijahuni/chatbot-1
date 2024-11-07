import streamlit as st
from openai import OpenAI

# 시스템 프롬프트 정의
SYSTEM_PROMPTS = {
    "travel": """당신은 전문적인 여행 상담사입니다. 다음 원칙들을 따라 사용자와 대화해주세요:

핵심 역할:
- 전 세계 여행지에 대한 맞춤형 추천과 정보 제공
- 여행 계획 수립 지원
- 예산과 일정에 맞는 최적의 제안 제시

대화 스타일:
- 친근하고 열정적인 톤 유지
- 구체적인 예시와 실용적인 팁 제공
- 사용자의 선호도와 제약사항을 항상 고려""",

    "coding": """당신은 친절하고 전문적인 프로그래밍 튜터입니다. 다음 원칙들을 따라 학습자를 지도해주세요:

핵심 역할:
- 프로그래밍 개념 설명
- 코드 리뷰와 디버깅 지원
- 모범 사례와 패턴 안내
- 학습 경로 추천

교육 방식:
- 단계별 설명 제공
- 실제 예제 코드 활용
- 학습자의 수준에 맞춘 설명
- 실수를 통한 학습 장려"""
}

# 사이드바에서 챗봇 유형 선택
st.sidebar.title("챗봇 유형 선택")
bot_type = st.sidebar.radio(
    "원하시는 챗봇을 선택하세요:",
    ("travel", "coding"),
    format_func=lambda x: "여행 상담 챗봇" if x == "travel" else "코딩 튜터 챗봇"
)

# 메인 타이틀과 설명
st.title(f"💬 {'여행 상담' if bot_type == 'travel' else '코딩 튜터'} 챗봇")
st.write(
    f"이 챗봇은 OpenAI의 GPT-3.5 모델을 사용하여 {'여행 상담' if bot_type == 'travel' else '코딩 학습'}을 도와드립니다. "
    "사용하려면 OpenAI API 키가 필요합니다."
)

# OpenAI API 키 입력
openai_api_key = st.text_input("OpenAI API Key", type="password")

if not openai_api_key:
    st.info("OpenAI API 키를 입력해주세요.", icon="🗝️")
else:
    # OpenAI 클라이언트 생성
    client = OpenAI(api_key=openai_api_key)

    # 세션 상태 초기화 (챗봇 유형이 변경될 때도 초기화)
    if "messages" not in st.session_state or "current_bot_type" not in st.session_state or st.session_state.current_bot_type != bot_type:
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPTS[bot_type]}
        ]
        st.session_state.current_bot_type = bot_type

    # 기존 대화 메시지 표시
    for message in st.session_state.messages:
        if message["role"] != "system":  # 시스템 메시지는 표시하지 않음
            with st.chat_message(message["role"]):
                st.markdown(message["content"])

    # 채팅 입력 필드
    help_text = "여행 계획에 대해 물어보세요!" if bot_type == "travel" else "프로그래밍 관련 질문을 해주세요!"
    if prompt := st.chat_input(help_text):
        # 현재 프롬프트 저장 및 표시
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # OpenAI API를 통한 응답 생성
        stream = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": m["role"], "content": m["content"]}
                for m in st.session_state.messages
            ],
            stream=True,
        )

        # 응답 스트리밍 및 저장
        with st.chat_message("assistant"):
            response = st.write_stream(stream)
        st.session_state.messages.append({"role": "assistant", "content": response})
