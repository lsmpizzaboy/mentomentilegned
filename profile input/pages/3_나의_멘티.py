import streamlit as st
from supabase import create_client

# 1. 수파베이스 클라이언트 초기화
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"수파베이스 연결 오류: {e}")
    st.stop()

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 로그인이 필요합니다.")
    st.stop()

# ==========================================
# [채팅방 화면 모드] 특정 멘티를 선택했을 때 켜지는 화면
# ==========================================
if "current_chat_match" in st.session_state:
    match = st.session_state.current_chat_match
    st.subheader(f"💬 {match['partner_name']} 멘티와의 대화")
    
    if st.button("◀ 목록으로 돌아가기"):
        del st.session_state.current_chat_match
        st.rerun()
        
    # 들어오면 상대방이 보낸 안 읽은 메시지를 '읽음(True)'으로 처리
    supabase.table("chat_messages").update({"is_read": True}).eq("match_id", match['id']).neq("sender_id", st.session_state.student_id).execute()
    
    # 채팅 내역 불러오기
    chat_res = supabase.table("chat_messages").select("*").eq("match_id", match['id']).order("created_at", desc=False).execute()
    messages = chat_res.data
    
    # 채팅창 출력
    chat_box = st.container(height=400)
    with chat_box:
        if not messages:
            st.info("아직 나눈 대화가 없습니다. 먼저 인사를 건네보세요!")
        for msg in messages:
            is_me = (msg["sender_id"] == st.session_state.student_id)
            # 내가 보낸 건 오른쪽(assistant 스타일), 받은 건 왼쪽(user 스타일)으로 표시
            with st.chat_message("assistant" if is_me else "user"):
                st.write(msg["message"])
                
    # 메시지 입력창
    prompt = st.chat_input("메시지를 입력하세요...")
    if prompt:
        supabase.table("chat_messages").insert({
            "match_id": match['id'],
            "sender_id": st.session_state.student_id,
            "message": prompt
        }).execute()
        st.rerun()
        
    st.stop() # 채팅창 모드일 때는 아래의 목록 코드가 실행되지 않도록 막음

# ==========================================
# [목록 화면 모드] 기본 화면
# ==========================================
st.title("👨‍🏫 나의 멘티 관리실")
st.write("나와 매칭된 멘티 목록입니다. 대화를 나누거나 멘토링을 종료할 수 있습니다.")

try:
    # 내가 멘토이고 상태가 '수락됨'인 매칭 찾기
    my_mentees_res = supabase.table("matches").select("*").eq("mentor_id", st.session_state.student_id).eq("status", "수락됨").execute()
    my_mentees = my_mentees_res.data
    
    # 멘티 이름 찾기 위한 전체 프로필
    profiles_res = supabase.table("profiles").select("student_id, name").execute()
    profile_dict = {p["student_id"]: p["name"] for p in profiles_res.data}
    
    if not my_mentees:
        st.info("현재 매칭되어 진행 중인 멘티가 없습니다.")
    else:
        for match in my_mentees:
            mentee_id = match["mentee_id"]
            mentee_name = profile_dict.get(mentee_id, "알 수 없는 멘티")
            
            # 안 읽은 메시지 개수 확인
            unread_res = supabase.table("chat_messages").select("id", count="exact").eq("match_id", match["id"]).eq("is_read", False).neq("sender_id", st.session_state.student_id).execute()
            unread_count = unread_res.count
            
            with st.container(border=True):
                col1, col2, col3 = st.columns([3, 1, 1])
                with col1:
                    alert = f" 🔴 **새 메시지 {unread_count}건**" if unread_count > 0 else ""
                    st.write(f"**👤 멘티:** {mentee_name} ({mentee_id}) {alert}")
                with col2:
                    if st.button("💬 채팅하기", key=f"chat_{match['id']}", use_container_width=True):
                        st.session_state.current_chat_match = {"id": match["id"], "partner_name": mentee_name}
                        st.rerun()
                with col3:
                    if st.button("🏁 종료하기", key=f"end_{match['id']}", use_container_width=True):
                        supabase.table("matches").update({"status": "종료됨"}).eq("id", match["id"]).execute()
                        st.success("멘토링을 성공적으로 종료했습니다.")
                        st.rerun()

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
