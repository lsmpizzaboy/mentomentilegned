import streamlit as st
from supabase import create_client
import datetime

# 1. 수파베이스 클라이언트 초기화 (새로운 가로 정렬 방식)
try:
    # [supabase] 섹션 안에서 url과 key를 깔끔하게 가져옵니다.
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"스트림릿 Secrets 설정에 오류가 있습니다: {e}")
    st.stop()

st.set_page_config(page_title="멘토-멘티 매칭 시스템", page_icon="🤝")

if "user" not in st.session_state:
    st.session_state.user = None

def logout():
    st.session_state.user = None
    st.rerun()

# --- 로그인 / 회원가입 화면 ---
if st.session_state.user is None:
    st.title("🔐 멘토-멘티 시스템 로그인")
    
    menu = ["로그인", "회원가입"]
    choice = st.selectbox("원하는 작업을 선택하세요", menu)
    
    email = st.text_input("이메일 주소")
    password = st.text_input("비밀번호", type="password")
    
    if choice == "회원가입":
        if st.button("새 계정 만들기"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.success("회원가입 신청이 완료되었습니다! 로그인을 시도해 보세요.")
            except Exception as e:
                st.error(f"회원가입 실패: {e}")
                
    elif choice == "로그인":
        if st.button("로그인"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state.user = res.user
                st.success("로그인 성공!")
                st.rerun()
            except Exception as e:
                st.error(f"로그인 실패: {e}")

# --- 프로필 등록 화면 ---
else:
    current_user = st.session_state.user
    st.sidebar.write(f"Logged in: {current_user.email}")
    if st.sidebar.button("로그아웃"):
        logout()

    st.title("📝 멘토-멘티 프로필 등록")
    
    role = st.radio("당신의 역할은 무엇인가요?", ("멘토", "멘티"))

    with st.form("profile_form"):
        name = st.text_input("이름 (또는 닉네임)")
        subject_list = ["국어", "수학", "영어", "과학", "사회", "파이썬", "C언어", "기타"]
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
                        profile_data = {
                            "id": current_user.id,
                            "role": role,
                            "name": name,
                            "subjects": subjects,
                            "available_times": available_times,
                            "bio": bio
                        }
                        supabase.table("profiles").upsert(profile_data).execute()
                        st.success(f"🎉 {name}님의 프로필이 성공적으로 저장되었습니다!")
                    except Exception as e:
                        st.error(f"데이터베이스 저장 실패: {e}")
