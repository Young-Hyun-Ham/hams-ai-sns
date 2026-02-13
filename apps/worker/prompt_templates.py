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
    )
}


def render_prompt(template_name: str, **kwargs: str) -> str:
    template = PROMPT_TEMPLATES.get(template_name)
    if not template:
        raise ValueError(f"unknown template: {template_name}")
    return template.format(**kwargs)
