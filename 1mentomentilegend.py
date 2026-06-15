import streamlit as st
import datetime

# 페이지 기본 설정
st.set_page_config(page_title="멘토-멘티 매칭", page_icon="🤝")

st.title("📝 멘토-멘티 프로필 등록")
st.write("환영합니다! 아래 정보를 입력해 프로필을 완성해 주세요.")

# 1. 역할 선택 (멘토 or 멘티)
role = st.radio("당신의 역할은 무엇인가요?", ("멘토", "멘티"))

# 2. 폼(Form) 생성
with st.form("profile_form"):
    name = st.text_input("이름 (또는 닉네임)")
    
    subject_list = ["국어", "수학", "영어", "과탐", "사탐", "수행평가" "기타"]
    time_list = ["평일 방과후", "평일 저녁", "주말 오전", "주말 오후", "주말 저녁"]
    
    # 변수 초기화
    date_range = []
    
    if role == "멘토":
        subjects = st.multiselect("자신 있게 가르칠 수 있는 과목을 선택해 주세요. (다중 선택 가능)", subject_list)
        bio = st.text_area("한줄 자기소개 (어떤 식으로 가르치는지, 나의 장점은 무엇인지 적어주세요!)")
    else:
        subjects = st.multiselect("도움받고 싶은 과목을 선택해 주세요. (다중 선택 가능)", subject_list)
        bio = st.text_area("질문하고 싶은 부분이나 현재 고민을 편하게 적어주세요!")
        
        # 📅 [멘티 전용 항목] 도움이 필요한 기간 설정 (기본값: 오늘 ~ 일주일 뒤)
        today = datetime.date.today()
        next_week = today + datetime.timedelta(days=7)
        
        st.write("---")
        st.subheader("📅 도움 요청 기한")
        st.write("설정한 기간이 지나면 멘토들에게 더 이상 이 요청이 보이지 않습니다.")
        date_range = st.date_input(
            "도움이 필요한 기간을 선택해 주세요",
            value=(today, next_week),
            min_value=today, # 오늘 이전 날짜는 선택 불가능하게 설정
            help="시작 날짜와 끝 날짜를 차례대로 클릭해 주세요."
        )
        st.write("---")
        
    available_times = st.multiselect("가능한 시간대를 모두 골라주세요.", time_list)
    
    # 제출 버튼
    submitted = st.form_submit_button("프로필 등록하기")
    
    if submitted:
        # 멘티일 경우 기한이 올바르게 선택되었는지 검증 (시작일과 종료일이 모두 클릭되어야 배열 길이가 2가 됨)
        is_date_valid = True
        if role == "멘티":
            if not isinstance(date_range, tuple) or len(date_range) < 2:
                is_date_valid = False
                st.warning("⚠️ 기간 선택을 완료해 주세요! (시작일과 종료일을 모두 클릭해야 합니다.)")
        
        # 필수 입력값 체크
        if not name or not subjects or not available_times or not is_date_valid:
            st.warning("⚠️ 모든 필수 항목을 올바르게 입력해 주세요!")
        else:
            st.success(f"🎉 환영합니다, {name} {role}님! 등록이 완료되었습니다.")
            st.info(f"선택한 과목: {', '.join(subjects)}")
            st.info(f"가능한 시간: {', '.join(available_times)}")
            
            # 멘티인 경우 기간 정보를 화면에 출력
            if role == "멘티":
                start_date, end_date = date_range
                st.info(f"🗓️ 도움 요청 기한: {start_date} ~ {end_date} 까지")
                
                # 🚧 이 날짜 데이터(start_date, end_date)를 수파베이스의 profiles 테이블에 함께 저장하게 됩니다.