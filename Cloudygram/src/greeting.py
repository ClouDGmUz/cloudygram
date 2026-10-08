from elyx import strings


def build_greeting(name: str) -> str:
    return strings("greeting", name=name)
