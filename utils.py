import streamlit as st

@st.cache_data(ttl=60)
def get_cached_profiles(_supabase):
    try:
        res = _supabase.table("profiles").select("*").execute()
        return res.data
    except Exception:
        return []

def render_global_notification_center(supabase):
    st.sidebar.markdown("---") 
    
    try:
        student_id = st.session_state.student_id
        
        # [A] 매칭 요청
        mentor_req = supabase.table("matches").select("id, mentee_id").eq("mentor_id", student_id).eq("status", "대기중").execute()
        pending_matches = mentor_req.data
        
        # [B] 안 읽은 채팅
        res1 = supabase.table("matches").select("id").eq("mentor_id", student_id).execute()
        res2 = supabase.table("matches").select("id").eq("mentee_id", student_id).execute()
        my_match_ids = [m["id"] for m in res1.data] + [m["id"] for m in res2.data]
        
        unread_chats = []
        if my_match_ids:
            chat_res = supabase.table("chat_messages").select("*").in_("match_id", my_match_ids).eq("is_read", False).neq("sender_id", student_id).execute()
            unread_chats = chat_res.data
            
        # [C] QnA 댓글
        my_posts_res = supabase.table("qna_board").select("id, title").eq("author_id", student_id).execute()
        my_post_ids = [p["id"] for p in my_posts_res.data]
        
        recent_comments = []
        if my_post_ids:
            comments_res = supabase.table("qna_comments").select("*").in_("post_id", my_post_ids).eq("is_read", False).order("created_at", desc=True).execute()
            recent_comments = comments_res.data

        total_notifications = len(pending_matches) + len(unread_chats) + len(recent_comments)
        badge = f" 🔴 ({total_notifications})" if total_notifications > 0 else ""
        
        with st.sidebar.popover(f"🔔 실시간 알림 센터{badge}", use_container_width=True):
            st.markdown("### 🗂️ 새로운 소식")
            
            if total_notifications == 0:
                st.caption("새로운 알림이 없습니다. 아주 평화롭네요! ✨")
            else:
                # 💡 [새로운 기능] 클릭 한 번에 알림을 싹 지워주는 청소 버튼!
                if st.button("🧹 새 알림 모두 확인(지우기)", use_container_width=True):
                    # 1. 내 글에 달린 안 읽은 QnA 댓글 모두 읽음 처리
                    if my_post_ids:
                        supabase.table("qna_comments").update({"is_read": True}).in_("post_id", my_post_ids).eq("is_read", False).execute()
                    # 2. 내게 온 안 읽은 채팅 모두 읽음 처리
                    if my_match_ids:
                        supabase.table("chat_messages").update({"is_read": True}).in_("match_id", my_match_ids).neq("sender_id", student_id).eq("is_read", False).execute()
                    
                    st.rerun()

            if pending_matches:
                st.markdown("**🤝 멘토링 요청**")
                for m in pending_matches:
                    st.info(f"🙋‍♂️ `{m['mentee_id']}` 학생이 멘토링 신청을 보냈습니다!")
                st.caption("※ 매칭 요청은 [매칭 시스템]에서 수락/거절해야 지워집니다.")
            
            if unread_chats:
                st.markdown("**💬 안 읽은 메시지**")
                unique_match_ids = set([c["match_id"] for c in unread_chats])
                st.warning(f"현재 답변을 기다리는 대화방이 {len(unique_match_ids)}개 있습니다.")
                
            if recent_comments:
                st.markdown("**💡 내 질문에 달린 새 댓글**")
                post_title_dict = {p["id"]: p["title"] for p in my_posts_res.data}
                for c in recent_comments:
                    p_title = post_title_dict.get(c["post_id"], "내 질문")
                    st.caption(f"📌 '{p_title}' 글")
                    st.write(f"👉 {c['comment']}")

    except Exception as e:
        st.sidebar.caption("알림을 불러오는 중 오류가 발생했습니다.")
