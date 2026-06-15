import streamlit as st
from supabase import create_client
import datetime

# 1. 수파베이스 클라이언트 초기화
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"스트림릿 Secrets 설정에 오류가 있습니다: {e}")
    st.stop()

# 페이지 기본 설정
st.set_page_config(page_title="멘토-멘티 매칭 시스템", page_icon="🤝")

st.title("📝 멘토-멘티 프로필 등록")
st.write("매칭 시스템에 등록할 프로필 정보를 입력해 주세요.")

# 멘토/멘티 선택
role = st.radio("당신의 역할은 무엇인가요?", ("멘토", "멘티"))

# 프로필 입력 폼
with st.form("profile_form"):
    name = st.text_input("이름 (또는 닉네임)")
    subject_list = ["국어", "수학", "영어", "과탐", "사탐", "기타"]
    time_list = ["평일 방과후", "평일 저녁", "주말 오전", "주말 오후", "주말 저녁"]
    
    date_range = []
    
    if role == "멘토":
        subjects = st.multiselect("자신 있게 가르칠 수 있는 과목을 선택해 주세요.", subject_list)
        bio = st.text_area("한줄 자기소개 (나의 장점은 무엇인가요?)")
    else:
        subjects = st.multiselect("도움받고 싶은 과목을 선택해 주세요.", subject_list)
        bio = st.text_area("질문하고 싶은 부분이나 현재 고민을 편하게 적어주세요!")
        
        today = datetime.date.today()
        next_week = today + datetime.timedelta(days=7)
        st.write("---")
        st.subheader("📅 도움 요청 기한")
        date_range = st.date_input("도움이 필요한 기간을 선택해 주세요", value=(today, next_week), min_value=today)
        st.write("---")
        
    available_times = st.multiselect("가능한 시간대를 모두 골라주세요.", time_list)
    submitted = st.form_submit_button("프로필 등록하기")
    
    if submitted:
        # 데이터 유효성 검사
        is_date_valid = True
        if role == "멘티":
            if not isinstance(date_range, tuple) or len(date_range) < 2:
                is_date_valid = False
                st.warning("⚠️ 기간 선택을 완료해 주세요! (시작일과 종료일 모두 클릭)")
        
        if not name or not subjects or not available_times or not is_date_valid:
            st.warning("⚠️ 모든 필수 항목을 올바르게 입력해 주세요!")
        else:
            with st.spinner("수파베이스 데이터베이스에 저장 중..."):
                try:
                    # 보낼 데이터 가공 (id를 제외하고 삽입)
                    profile_data = {
                        "role": role,
                        "name": name,
                        "subjects": subjects,
                        "available_times": available_times,
                        "bio": bio
                    }
                    
                    # 수파베이스 테이블에 데이터 추가
                    supabase.table("profiles").insert(profile_data).execute()
                    st.success(f"🎉 {name}님의 프로필이 성공적으로 저장되었습니다!")
                    
                except Exception as e:
                    st.error(f"데이터베이스 저장 실패: {e}")
