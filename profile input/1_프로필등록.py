import streamlit as st
from supabase import create_client
import datetime

# 1. 수파베이스 클라이언트 초기화
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"수파베이스 연결 오류: {e}")
    st.stop()

st.set_page_config(page_title="교내 멘토-멘티 시스템", page_icon="🏫")

# 2. 로그인 상태 관리용 세션 초기화
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
    st.session_state.student_id = None
    st.session_state.name = None

def logout():
    st.session_state.logged_in = False
    st.session_state.student_id = None
    st.session_state.name = None
    st.rerun()

# ==========================================
# 3. 로그인 및 회원가입 화면
# ==========================================
if not st.session_state.logged_in:
    st.title("🏫 교내 멘토-멘티 시스템")
    st.write("서비스를 이용하시려면 로그인이나 회원가입을 해주세요.")
    
    tab1, tab2 = st.tabs(["🔑 로그인", "📝 회원가입"])
    
    with tab1:
        st.subheader("로그인")
        login_id = st.text_input("학번 (예: 10101)", key="login_id")
        login_pw = st.text_input("비밀번호", type="password", key="login_pw")
        
        if st.button("로그인하기"):
            if login_id and login_pw:
                res = supabase.table("students").select("*").eq("student_id", login_id).execute()
                if len(res.data) > 0 and res.data[0]["password"] == login_pw:
                    st.session_state.logged_in = True
                    st.session_state.student_id = login_id
                    st.session_state.name = res.data[0]["name"]
                    st.success(f"환영합니다, {res.data[0]['name']}님!")
                    st.rerun()
                else:
                    st.error("학번이나 비밀번호가 일치하지 않습니다.")
            else:
                st.warning("학번과 비밀번호를 모두 입력해 주세요.")
                
    with tab2:
        st.subheader("신규 회원가입")
        new_id = st.text_input("학번 (예: 10101)", key="new_id")
        new_name = st.text_input("이름 (실명)", key="new_name")
        new_pw = st.text_input("사용할 비밀번호", type="password", key="new_pw")
        
        if st.button("가입하기"):
            if new_id and new_name and new_pw:
                check = supabase.table("students").select("*").eq("student_id", new_id).execute()
                if len(check.data) > 0:
                    st.error("이미 가입된 학번입니다! 로그인을 시도해 주세요.")
                else:
                    new_student_data = {
                        "student_id": new_id,
                        "name": new_name,
                        "password": new_pw
                    }
                    supabase.table("students").insert(new_student_data).execute()
                    st.success("🎉 회원가입이 완료되었습니다! '로그인' 탭에서 로그인해 주세요.")
            else:
                st.warning("모든 칸을 빠짐없이 입력해 주세요.")

# ==========================================
# 4. 메인 화면: 내 프로필 통합 관리 창 (등록 및 수정)
# ==========================================
else:
    # 사이드바 프로필 영역 및 로그아웃
    st.sidebar.write(f"👤 **{st.session_state.name}** 학생")
    st.sidebar.write(f"🆔 학번: {st.session_state.student_id}")
    if st.sidebar.button("로그아웃"):
        logout()

    st.title("📝 멘토-멘티 프로필 관리")
    st.write(f"**{st.session_state.name}**님, 나의 멘토 프로필과 멘티 프로필을 각각 관리할 수 있습니다.")
    
    # [핵심 로직] 현재 학번으로 등록된 모든 프로필 데이터베이스에서 조회하기
    try:
        profile_res = supabase.table("profiles").select("*").eq("student_id", st.session_state.student_id).execute()
        existing_profiles = profile_res.data
    except Exception as e:
        st.error(f"기존 프로필을 불러오는 중 오류 발생: {e}")
        existing_profiles = []
        
    # 내가 가질 수 있는 2가지 프로필 분리 검색
    mentor_profile = next((p for p in existing_profiles if p.get("role") == "멘토"), None)
    mentee_profile = next((p for p in existing_profiles if p.get("role") == "멘티"), None)
    
    # 📊 상단에 내 프로필 등록 상태 시각적으로 보여주기
    st.markdown("### 📊 나의 프로필 현황")
    col_m1, col_m2 = st.columns(2)
    with col_m1:
        if mentor_profile:
            st.success("👨‍🏫 멘토 프로필: **등록 완료** (수정 가능)")
        else:
            st.info("👨‍🏫 멘토 프로필: **미등록**")
    with col_m2:
        if mentee_profile:
            st.success("👩‍🎓 멘티 프로필: **등록 완료** (수정 가능)")
        else:
            st.info("👩‍🎓 멘티 프로필: **미등록**")
            
    st.markdown("---")
    
    # 작성 및 수정할 역할 선택
    role = st.radio("어떤 프로필을 편집하시겠습니까?", ("멘토", "멘티"))
    
    # 선택한 역할에 따라 불러올 타겟 프로필 지정
    target_profile = mentor_profile if role == "멘토" else mentee_profile
    is_edit_mode = target_profile is not None # 이미 프로필이 존재하면 수정 모드(True)가 됨
    
    if is_edit_mode:
        st.info(f"✨ 기존에 작성한 **{role} 프로필** 정보를 불러왔습니다. 수정 후 하단 버튼을 누르면 업데이트됩니다.")
    else:
        st.caption(f"✨ 아직 작성된 **{role} 프로필**이 없습니다. 새로 입력해 주세요.")

    # 수정 모드일 때는 기존 데이터, 새 등록 모드일 때는 빈 값을 기본값으로 세팅
    default_subjects = target_profile.get("subjects", []) if is_edit_mode else []
    default_bio = target_profile.get("bio", "") if is_edit_mode else ""
    default_times = target_profile.get("available_times", []) if is_edit_mode else []
    
    # 기한 입력 기본값 세팅 (멘티 수정 전용)
    default_date = (datetime.date.today(), datetime.date.today() + datetime.timedelta(days=7))
    if is_edit_mode and role == "멘티" and target_profile.get("mentee_deadline"):
        try:
            dates = target_profile["mentee_deadline"].split(" ~ ")
            if len(dates) == 2:
                default_date = (datetime.date.fromisoformat(dates[0]), datetime.date.fromisoformat(dates[1]))
        except:
            pass

    # 폼 내부 구성 (key값에 role을 주어 라디오 버튼 전환 시 캐시가 부드럽게 리셋되도록 유도)
    with st.form(f"profile_form_{role}"):
        st.text_input("이름", value=st.session_state.name, disabled=True)
        
        subject_list = ["국어", "수학", "영어", "과탐", "사탐", "기타"]
        time_list = ["평일 방과후", "평일 저녁", "주말 오전", "주말 오후", "주말 저녁"]
        
        if role == "멘토":
            # 기존 저장 데이터 중 유효한 데이터만 필터링해서 디폴트 설정
            valid_subjects = [s for s in default_subjects if s in subject_list]
            subjects = st.multiselect("자신 있게 가르칠 수 있는 과목을 선택해 주세요.", subject_list, default=valid_subjects)
            bio = st.text_area("한줄 자기소개 (나의 멘토링 방식이나 장점은 무엇인가요?)", value=default_bio)
        else:
            valid_subjects = [s for s in default_subjects if s in subject_list]
            subjects = st.multiselect("도움받고 싶은 과목을 선택해 주세요.", subject_list, default=valid_subjects)
            bio = st.text_area("질문하고 싶은 부분이나 현재 고민을 편하게 적어주세요!", value=default_bio)
            
            today = datetime.date.today()
            st.write("---")
            st.subheader("📅 도움 요청 기한")
            date_range = st.date_input("도움이 필요한 기간을 선택해 주세요 (시작일과 종료일 클릭)", value=default_date, min_value=today)
            st.write("---")
            
        valid_times = [t for t in default_times if t in time_list]
        available_times = st.multiselect("멘토링이 가능한 시간대를 모두 골라주세요.", time_list, default=valid_times)
        
        # 상태에 따라 버튼 글자 자동 변경
        button_text = "🔧 프로필 수정 완료하기" if is_edit_mode else "🚀 프로필 등록 완료하기"
        submitted = st.form_submit_button(button_text)
        
        if submitted:
            is_date_valid = True
            mentee_deadline = None
            
            if role == "멘티":
                if not isinstance(date_range, tuple) or len(date_range) < 2:
                    is_date_valid = False
                    st.warning("⚠️ 기간 선택을 완료해 주세요! (시작일과 종료일 모두 클릭)")
                else:
                    mentee_deadline = f"{date_range[0]} ~ {date_range[1]}"
            
            if not subjects or not available_times or not is_date_valid:
                st.warning("⚠️ 필수 항목(과목, 시간대)을 올바르게 입력해 주세요!")
            else:
                with st.spinner("데이터베이스에 저장 중..."):
                    try:
                        profile_data = {
                            "student_id": st.session_state.student_id,
                            "role": role,
                            "name": st.session_state.name,
                            "subjects": subjects,
                            "available_times": available_times,
                            "bio": bio,
                            "mentee_deadline": mentee_deadline
                        }
                        
                        if is_edit_mode:
                            # 1. 수정 모드일 때: 내 학번과 역할(멘토/멘티)이 일치하는 행을 찾아 내용 덮어쓰기(update)
                            supabase.table("profiles").update(profile_data).eq("student_id", st.session_state.student_id).eq("role", role).execute()
                            st.success(f"🎉 {st.session_state.name}님의 {role} 프로필 수정이 완벽하게 반영되었습니다!")
                        else:
                            # 2. 신규 등록 모드일 때: 그냥 데이터베이스에 한 줄 삽입(insert)
                            supabase.table("profiles").insert(profile_data).execute()
                            st.success(f"🎉 {st.session_state.name}님의 {role} 프로필이 성공적으로 신규 등록되었습니다!")
                        
                        # 상단 현황판 새로고침을 위한 화면 갱신
                        st.rerun()
                        
                    except Exception as e:
                        st.error(f"데이터베이스 저장 실패: {e}")
