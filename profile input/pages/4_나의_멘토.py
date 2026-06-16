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
# [채팅방 화면 모드]
# ==========================================
if "current_chat_match" in st.session_state:
    match = st.session_state.current_chat_match
    st.subheader(f"💬 {match['partner_name']} 멘토님과의 대화")
    
    if st.button("◀ 목록으로 돌아가기"):
        del st.session_state.current_chat_match
        st.rerun()
        
    supabase.table("chat_messages").update({"is_read": True}).eq("match_id", match['id']).neq("sender_id", st.session_state.student_id).execute()
    
    chat_res = supabase.table("chat_messages").select("*").eq("match_id", match['id']).order("created_at", desc=False).execute()
    messages = chat_res.data
    
    chat_box = st.container(height=400)
    with chat_box:
        if not messages:
            st.info("궁금한 점이나 첫 인사를 남겨보세요!")
        for msg in messages:
            is_me = (msg["sender_id"] == st.session_state.student_id)
            with st.chat_message("assistant" if is_me else "user"):
                st.write(msg["message"])
                
    prompt = st.chat_input("메시지를 입력하세요...")
    if prompt:
        supabase.table("chat_messages").insert({
            "match_id": match['id'],
            "sender_id": st.session_state.student_id,
            "message": prompt
        }).execute()
        st.rerun()
        
    st.stop()

# ==========================================
# [목록 화면 모드]
# ==========================================
st.title("👩‍🎓 나의 멘토 연락망")
st.write("나와 매칭된 멘토 목록입니다. 궁금한 점을 채팅으로 편하게 물어보세요!")

try:
    # 내가 멘티이고 상태가 '수락됨'인 매칭 찾기
    my_mentors_res = supabase.table("matches").select("*").eq("mentee_id", st.session_state.student_id).eq("status", "수락됨").execute()
    my_mentors = my_mentors_res.data
    
    profiles_res = supabase.table("profiles").select("student_id, name").execute()
    profile_dict = {p["student_id"]: p["name"] for p in profiles_res.data}
    
    if not my_mentors:
        st.info("현재 매칭되어 진행 중인 멘토가 없습니다. '매칭 시스템'에서 멘토에게 신청해 보세요!")
    else:
        for match in my_mentors:
            mentor_id = match["mentor_id"]
            mentor_name = profile_dict.get(mentor_id, "알 수 없는 멘토")
            
            unread_res = supabase.table("chat_messages").select("id", count="exact").eq("match_id", match["id"]).eq("is_read", False).neq("sender_id", st.session_state.student_id).execute()
            unread_count = unread_res.count
            
            with st.container(border=True):
                col1, col2 = st.columns([3, 1])
                with col1:
                    alert = f" 🔴 **새 메시지 {unread_count}건**" if unread_count > 0 else ""
                    st.write(f"**👨‍🏫 멘토:** {mentor_name} ({mentor_id}) {alert}")
                with col2:
                    if st.button("💬 질문하기", key=f"chat_{match['id']}", use_container_width=True):
                        st.session_state.current_chat_match = {"id": match["id"], "partner_name": mentor_name}
                        st.rerun()

except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
