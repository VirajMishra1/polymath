# Run from backend/: venv/bin/python -m tests.test_gemini_provider  (also collected by pytest)
import asyncio
import httpx
from app.llm import gemini_provider as gp


def _run(handler, groq_key, calls=None):
    calls = [] if calls is None else calls

    def record(req):
        calls.append(req.url.path)
        return handler(req)

    real = httpx.AsyncClient
    saved = (gp.settings.GEMINI_API_KEY, gp.settings.GROQ_API_KEY)
    gp.httpx.AsyncClient = lambda **kw: real(transport=httpx.MockTransport(record), **kw)
    gp.settings.GEMINI_API_KEY, gp.settings.GROQ_API_KEY = "test", groq_key
    try:
        return asyncio.run(gp.GeminiProvider().generate_json("x")), calls
    finally:
        gp.httpx.AsyncClient = real
        gp.settings.GEMINI_API_KEY, gp.settings.GROQ_API_KEY = saved


def test_falls_through_chain_on_429_and_503():
    def handler(req):
        if "googleapis" in req.url.host:
            return httpx.Response(429 if "lite" in req.url.path else 503)
        return httpx.Response(200, json={"choices": [{"message": {"content": '{"via": "groq"}'}}]})

    out, calls = _run(handler, "test")
    assert out == {"via": "groq"}
    assert calls == [
        "/v1beta/models/gemini-2.5-flash-lite:generateContent",
        "/v1beta/models/gemini-2.5-flash:generateContent",
        "/openai/v1/chat/completions",
    ]


def test_first_model_success_parses_json():
    def handler(req):
        return httpx.Response(200, json={"candidates": [{"content": {"parts": [{"text": '{"ok": true}'}]}}]})

    out, calls = _run(handler, None)
    assert out == {"ok": True}
    assert len(calls) == 1


def test_non_retryable_error_skips_second_model_and_raises_without_groq():
    calls = []
    try:
        _run(lambda req: httpx.Response(400), None, calls)
    except RuntimeError as e:
        assert "GROQ_API_KEY" in str(e)
        assert calls == ["/v1beta/models/gemini-2.5-flash-lite:generateContent"]
    else:
        raise AssertionError("expected RuntimeError")


if __name__ == "__main__":
    for name, fn in list(globals().items()):
        if name.startswith("test_"):
            fn()
            print("ok", name)
