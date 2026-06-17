import streamlit as st
from supabase import create_client
import base64

# 1. 수파베이스 클라이언트 초기화
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["key"]
    supabase = create_client(url, key)
except Exception as e:
    st.error(f"수파베이스 연결 오류: {e}")
    st.stop()

if "logged_in" not in st.session_state or not st.session_state.logged_in:
    st.warning("🔒 로그인이 필요한 서비스입니다.")
    st.stop()

# 프로필 정보 가져오기 (작성자 이름 표시용)
try:
    profiles_res = supabase.table("profiles").select("student_id, name").execute()
    profile_dict = {p["student_id"]: p["name"] for p in profiles_res.data}
except:
    profile_dict = {}

# ==========================================
# 🔍 [상세 보기 화면 모드] 글을 클릭했을 때 켜지는 새로운 창
# ==========================================
if "current_post" in st.session_state:
    post = st.session_state.current_post
    author_name = profile_dict.get(post["author_id"], "알 수 없는 사용자")
    
    # 뒤로가기 버튼
    if st.button("◀ 목록으로 돌아가기"):
        del st.session_state.current_post
        st.rerun()
        
    st.title(f"📌 {post['title']}")
    st.caption(f"👤 작성자: {author_name} | 🕒 작성일: {post['created_at'][:10]}")
    st.markdown("---")
    
    # 1. 본문 내용 표시
    st.write(post["content"])
    
    # 2. 이미지가 있다면 화면에 꽉 차지 않게 width=400으로 제한하여 출력
    if post.get("image_data"):
        img_base64 = post["image_data"].replace("DATA_IMAGE:", "")
        st.image(f"data:image/png;base64,{img_base64}", width=400)
        
    st.markdown("---")
    st.subheader("💬 댓글")
    
    # 이 게시글에 달린 댓글만 최신순으로 가져오기
    comments_res = supabase.table("qna_comments").select("*").eq("post_id", post["id"]).order("created_at", desc=False).execute()
    comments = comments_res.data
    
    if not comments:
        st.info("아직 댓글이 없습니다. 첫 번째 답변을 남겨주세요!")
    else:
        for c in comments:
            c_author_name = profile_dict.get(c["author_id"], "알 수 없는 사용자")
            st.markdown(f"- **{c_author_name}**: {c['comment']}")
            
    st.write("") # 시각적 여백 띄우기
    
    # 💡 [핵심 해결] 폼(form)을 사용해 댓글 작성 후 입력칸 자동 초기화!
    with st.form(f"comment_form_{post['id']}", clear_on_submit=True):
        new_comment = st.text_input("새 댓글 남기기", placeholder="여기에 답변이나 의견을 입력하세요...")
        submitted = st.form_submit_button("등록")
        
        if submitted:
            if new_comment:
                supabase.table("qna_comments").insert({
                    "post_id": post["id"],
                    "author_id": st.session_state.student_id,
                    "comment": new_comment
                }).execute()
                st.rerun() # 저장 후 즉시 새로고침하여 반영
            else:
                st.warning("댓글 내용을 입력해 주세요.")
                
    st.stop() # 상세 보기 모드일 때는 아래의 '목록 화면' 코드가 실행되지 않도록 여기서 프로그램 멈춤

# ==========================================
# 📋 [목록 화면 모드] 기본 게시판 화면
# ==========================================
st.title("💡 실시간 Q&A 질문게시판")
st.write("모르는 문제를 올리거나, 다른 친구들의 질문에 답변을 달아주세요!")

# 상단: 새로운 질문 작성 공간 (폼 형태로 제출 후 텍스트 자동 비움)
with st.expander("📝 새로운 질문 작성하기"):
    with st.form("new_post_form", clear_on_submit=True):
        new_title = st.text_input("제목 (어떤 과목/내용인지 간략히 적어주세요)")
        new_content = st.text_area("질문 내용", height=150)
        uploaded_image = st.file_uploader("사진 첨부 (선택사항)", type=["png", "jpg", "jpeg"])
        
        if st.form_submit_button("🚀 질문 등록하기"):
            if new_title and new_content:
                image_base64 = None
                if uploaded_image:
                    image_base64 = base64.b64encode(uploaded_image.read()).decode("utf-8")
                
                post_data = {
                    "author_id": st.session_state.student_id,
                    "title": new_title,
                    "content": new_content,
                    "image_data": f"DATA_IMAGE:{image_base64}" if image_base64 else None
                }
                supabase.table("qna_board").insert(post_data).execute()
                st.success("질문이 등록되었습니다!")
                st.rerun()
            else:
                st.warning("제목과 내용을 모두 입력해 주세요.")

st.markdown("---")
st.subheader("📋 전체 질문 목록")

try:
    # 전체 게시물 가져오기
    posts_res = supabase.table("qna_board").select("*").order("created_at", desc=True).execute()
    posts = posts_res.data
    
    # 댓글 개수 파악을 위해 전체 댓글 데이터 가져오기
    comments_res = supabase.table("qna_comments").select("post_id").execute()
    comment_counts = {}
    for c in comments_res.data:
        pid = c["post_id"]
        comment_counts[pid] = comment_counts.get(pid, 0) + 1
        
    if not posts:
        st.info("아직 등록된 질문이 없습니다. 첫 번째 질문의 주인공이 되어보세요!")
    else:
        # 게시판 목록 출력
        for post in posts:
            author_name = profile_dict.get(post["author_id"], "알 수 없는 사용자")
            ccount = comment_counts.get(post["id"], 0)
            
            # 각 질문을 깔끔한 상자(container)로 감싸고 옆에 버튼 배치
            with st.container(border=True):
                col1, col2 = st.columns([5, 1])
                with col1:
                    st.markdown(f"**{post['title']}**")
                    st.caption(f"👤 {author_name}  |  💬 댓글 {ccount}개")
                with col2:
                    # 버튼을 누르면 해당 게시글 정보를 세션에 저장하고 새로고침 -> 상세 화면으로 이동!
                    if st.button("자세히 보기", key=f"view_{post['id']}", use_container_width=True):
                        st.session_state.current_post = post
                        st.rerun()

except Exception as e:
    st.error(f"게시판 데이터를 불러오는 중 오류가 발생했습니다: {e}")
