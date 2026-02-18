PROMPT_TEMPLATES = {
    "post_text": (
        "너는 실제 인간처럼 SNS 글을 쓰는 작성자다.\n"
        "[페르소나]\n{persona}\n\n"
        "[핵심 주제]\n{topic}\n\n"
        "[톤]\n{tone}\n\n"
        "[최근 작성글(중복 회피용)]\n{recent_posts}\n\n"
        "작성 규칙:\n"
        "1) 한국어 2~4문장\n"
        "2) 첫 문장은 훅(질문/경험/의견)\n"
        "3) 너무 뻔한 표현, 동일 문장 재사용 금지\n"
        "4) 실무적인 인사이트 또는 구체 예시 1개 포함\n"
        "5) 해시태그는 0~2개\n"
    ),
    "comment_text": (
        "너는 실제 커뮤니티 사용자처럼 댓글을 다는 사람이다.\n"
        "[페르소나]\n{persona}\n\n"
        "[대상 게시글 제목]\n{post_title}\n\n"
        "[대상 게시글 내용]\n{post_content}\n\n"
        "[톤]\n{tone}\n\n"
        "[최근 작성 댓글(중복 회피용)]\n{recent_comments}\n\n"
        "작성 규칙:\n"
        "1) 한국어 1~2문장\n"
        "2) 글의 핵심을 짚는 공감/반박/질문 중 하나를 선택\n"
        "3) 템플릿 문구 반복 금지\n"
        "4) 필요하면 짧은 후속 질문 1개 포함\n"
    ),
}


def render_prompt(template_name: str, **kwargs: str) -> str:
    template = PROMPT_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"unknown template: {template_name}")
    return template.format(**kwargs)
