import streamlit as st
from openai import OpenAI
from datetime import datetime, timedelta
import pandas as pd
import random

# 가상의 항공편 데이터를 생성하는 함수
def generate_flight_data(departure, arrival, date):
    airlines = ["대한항공", "아시아나", "제주항공", "진에어", "에어부산"]
    flights = []
    
    # 해당 날짜의 다양한 시간대에 대한 항공편 생성
    for _ in range(5):  # 각 경로당 5개의 항공편
        departure_time = datetime.strptime(date, "%Y-%m-%d") + timedelta(hours=random.randint(0, 23))
        duration = timedelta(hours=random.randint(1, 8))
        arrival_time = departure_time + duration
        
        price = random.randint(150000, 1500000)  # 15만원 ~ 150만원
        airline = random.choice(airlines)
        
        flights.append({
            "항공사": airline,
            "출발지": departure,
            "도착지": arrival,
            "출발시간": departure_time.strftime("%Y-%m-%d %H:%M"),
            "도착시간": arrival_time.strftime("%Y-%m-%d %H:%M"),
            "소요시간": str(duration).split(".")[0],
            "가격": f"{price:,}원"
        })
    
    return pd.DataFrame(flights)

# 시스템 프롬프트 수정 - 항공편 검색 기능 추가
SYSTEM_PROMPTS = {
    "travel": """당신은 전문적인 여행 상담사입니다. 다음 원칙들을 따라 사용자와 대화해주세요:

핵심 역할:
- 전 세계 여행지에 대한 맞춤형 추천과 정보 제공
- 여행 계획 수립 지원
- 예산과 일정에 맞는 최적의 제안 제시
- 항공편 검색 지원 (출발지, 도착지, 날짜 정보 파악)

대화 스타일:
- 친근하고 열정적인 톤 유지
- 구체적인 예시와 실용적인 팁 제공
- 사용자의 선호도와 제약사항을 항상 고려

항공편 검색 시:
- "항공편 검색"이라는 키워드를 포함하여 응답
- 출발지, 도착지, 날짜 정보를 명확히 파악하여 제시""",
    
    "coding": """...[이전과 동일]..."""
}

# 메인 앱
def main():
    st.sidebar.title("챗봇 유형 선택")
    bot_type = st.sidebar.radio(
        "원하시는 챗봇을 선택하세요:",
        ("travel", "coding"),
        format_func=lambda x: "여행 상담 챗봇" if x == "travel" else "코딩 튜터 챗봇"
    )

    st.title(f"💬 {'여행 상담' if bot_type == 'travel' else '코딩 튜터'} 챗봇")
    st.write(
        f"이 챗봇은 OpenAI의 GPT-3.5 모델을 사용하여 {'여행 상담' if bot_type == 'travel' else '코딩 학습'}을 도와드립니다. "
        "사용하려면 OpenAI API 키가 필요합니다."
    )

    # 여행 챗봇일 경우 항공편 검색 섹션 추가
    if bot_type == "travel":
        with st.expander("✈️ 항공편 직접 검색"):
            col1, col2, col3 = st.columns(3)
            with col1:
                departure = st.text_input("출발지", "서울")
            with col2:
                arrival = st.text_input("도착지", "제주")
            with col3:
                flight_date = st.date_input("날짜", datetime.now())
            
            if st.button("항공편 검색"):
                flights_df = generate_flight_data(departure, arrival, flight_date.strftime("%Y-%m-%d"))
                st.dataframe(flights_df, use_container_width=True)

    # OpenAI API 키 입력
    openai_api_key = st.text_input("OpenAI API Key", type="password")

    if not openai_api_key:
        st.info("OpenAI API 키를 입력해주세요.", icon="🗝️")
        return

    # OpenAI 클라이언트 생성
    client = OpenAI(api_key=openai_api_key)

    # 세션 상태 초기화
    if "messages" not in st.session_state or "current_bot_type" not in st.session_state or st.session_state.current_bot_type != bot_type:
        st.session_state.messages = [
            {"role": "system", "content": SYSTEM_PROMPTS[bot_type]}
        ]
        st.session_state.current_bot_type = bot_type

    # 기존 대화 메시지 표시
    for message in st.session_state.messages:
        if message["role"] != "system":
            with st.chat_message(message["role"]):
                st.markdown(message["content"])
                
                # 항공편 검색 결과 표시 (여행 챗봇의 경우)
                if bot_type == "travel" and message["role"] == "assistant" and "항공편 검색" in message["content"]:
                    # 응답에서 출발지, 도착지, 날짜 정보 추출 (실제로는 더 정교한 파싱 필요)
                    try:
                        flights_df = generate_flight_data("서울", "제주", datetime.now().strftime("%Y-%m-%d"))
                        st.dataframe(flights_df, use_container_width=True)
                    except Exception as e:
                        st.error("항공편 검색 중 오류가 발생했습니다.")

    # 채팅 입력 필드
    help_text = "여행 계획이나 항공편에 대해 물어보세요!" if bot_type == "travel" else "프로그래밍 관련 질문을 해주세요!"
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
            
            # 항공편 검색 키워드가 있는 경우 항공편 정보 표시
            if "항공편 검색" in response:
                try:
                    flights_df = generate_flight_data("서울", "제주", datetime.now().strftime("%Y-%m-%d"))
                    st.dataframe(flights_df, use_container_width=True)
                except Exception as e:
                    st.error("항공편 검색 중 오류가 발생했습니다.")
                    
        st.session_state.messages.append({"role": "assistant", "content": response})

if __name__ == "__main__":
    main()
