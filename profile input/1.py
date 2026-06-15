import streamlit as st
from supabase import create_client, APIError
import datetime

# 1. 수파베이스 클라이언트 초기화 (Secrets에 저장한 정보 불러오기)
try:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    supabase = create_client(url, key)
except Exception as e:
    st.error("스트림릿 Secrets 설정에 오류가 있습니다. URL과 KEY를 다시 확인해 주세요.")
    st.stop()

st.set_page_config(page_title="멘토-멘티 매칭 시스템", page_icon="🤝")

# --- 로그인 상태 관리 ---
# 세션 상태(session_state)를 이용해 로그인 정보를 웹브라우저 메모리에 유지합니다.
if "user" not in st.session_state:
    st.session_state.user = None

# 로그아웃 기능
def logout():
    st.session_state.user = None
    st.rerun()

# --- 화면 1: 로그인 / 회원가입 화면 ---
if st.session_state.user is None:
    st.title("🔐 멘토-멘티 시스템 로그인")
    
    menu = ["로그인", "회원가입"]
    choice = st.selectbox("원하는 작업을 선택하세요", menu)
    
    email = st.text_input("이메일 주소")
    password = st.text_input("비밀번호", type="password")
    
    if choice == "회원가입":
        if st.button("새 계정 만들기"):
            try:
                # 수파베이스 인증 기능으로 회원가입 진행
                res = supabase.auth.sign_up({"email": email, "password": password})
                st.success("회원가입 신청이 완료되었습니다! 입력하신 이메일의 인증 메일함을 확인하거나 바로 로그인을 시도해 보세요.")
            except APIError as e:
                st.error(f"회원가입 실패: {e.message}")
                
    elif choice == "로그인":
        if st.button("로그인"):
            try:
                # 수파베이스 인증 기능으로 로그인 진행
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                # 로그인 성공 시 유저 정보를 세션에 저장
                st.session_state.user = res.user
                st.success("로그인 성공!")
                st.rerun()
            except APIError as e:
                st.error(f"로그인 실패: {e.message}")

# --- 화면 2: 프로필 등록 화면 (로그인 성공 시 진입) ---
else:
    current_user = st.session_state.user
    st.sidebar.write(f"Logged in: {current_user.email}")
    if st.sidebar.button("로그아웃"):
        logout()

    st.title("📝 멘토-멘티 프로필 등록")
    st.write("아래 정보를 입력해 프로필을 완성해 주세요. 수파베이스 DB에 안전하게 저장됩니다.")

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
                        # 3. 데이터베이스에 저장할 데이터 꾸러미 구성
                        profile_data = {
                            "id": current_user.id,        # 수파베이스 로그인 유저의 UUID 핵심!!
                            "role": role,
                            "name": name,
                            "subjects": subjects,         # 파이썬 리스트는 수파베이스 TEXT[] 배열로 쏙 들어갑니다
                            "available_times": available_times,
                            "bio": bio
                        }
                        
                        # 수파베이스의 'profiles' 테이블에 데이터 삽입(Insert)
                        # 만약 이미 등록한 프로필이 있다면 덮어쓰기(upsert) 하도록 설정 가능
                        supabase.table("profiles").upsert(profile_data).execute()
                        
                        st.success(f"🎉 {name}님의 프로필이 수파베이스 데이터베이스에 성공적으로 저장되었습니다!")
                        
                        if role == "멘티":
                            start_date, end_date = date_range
                            st.info(f"🗓️ 설정된 도움 기한: {start_date} ~ {end_date} (이 정보는 추후 매칭 화면 필터링에 활용됩니다)")
                            
                    except APIError as e:
                        st.error(f"데이터베이스 저장 실패: {e.message}")
