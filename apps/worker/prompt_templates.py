PROMPT_TEMPLATES = {
    "post_text": (
        "너는 SNS 자동화 봇의 콘텐츠 작성기다.\n"
        "[페르소나]\n{persona}\n\n"
        "[주제]\n{topic}\n\n"
        "[톤]\n{tone}\n\n"
        "요구사항:\n"
        "1) 한국어 1~2문장\n"
        "2) 과장 금지, 실무형 문장\n"
        "3) 해시태그는 최대 2개\n"
    ),
    "comment_text": (
        "너는 SNS 봇 댓글 작성기다.\n"
        "[페르소나]\n{persona}\n\n"
        "[대상 게시글]\n{post_title}\n{post_content}\n\n"
        "[톤]\n{tone}\n\n"
        "요구사항:\n"
        "1) 한국어 1문장\n"
        "2) 공격적 표현 금지\n"
        "3) 공감 또는 질문 중심\n"
    ),
}


def render_prompt(template_name: str, **kwargs: str) -> str:
    template = PROMPT_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"unknown template: {template_name}")
    return template.format(**kwargs)
