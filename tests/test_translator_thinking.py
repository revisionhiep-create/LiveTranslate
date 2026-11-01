import translator as translator_module
from translator import Translator, resolve_thinking_style, thinking_disable_body


class _DummyClient:
    pass


def _make_translator(monkeypatch, api_base, model, **kwargs):
    monkeypatch.setattr(
        translator_module,
        "make_openai_client",
        lambda *args, **client_kwargs: _DummyClient(),
    )
    kwargs.setdefault("no_think", True)
    return Translator(
        api_base=api_base,
        api_key="test-key",
        model=model,
        **kwargs,
    )


def _extra_body(translator):
    return translator._build_request_kwargs("system", "hello").get("extra_body")


# ── auto style detection ──


def test_deepseek_model_uses_nested_thinking_toggle(monkeypatch):
    translator = _make_translator(
        monkeypatch, "https://example.com/v1", "deepseek-v4-pro"
    )

    assert _extra_body(translator) == {"thinking": {"type": "disabled"}}


def test_official_deepseek_endpoint_supports_model_aliases(monkeypatch):
    translator = _make_translator(
        monkeypatch, "https://api.deepseek.com/v1", "production-alias"
    )

    assert _extra_body(translator) == {"thinking": {"type": "disabled"}}


def test_deepseek_proxy_endpoint_uses_nested_thinking_toggle(monkeypatch):
    translator = _make_translator(
        monkeypatch, "https://deepseek.gateway.example.com/v1", "production-alias"
    )

    assert _extra_body(translator) == {"thinking": {"type": "disabled"}}


def test_volcano_ark_endpoint_uses_nested_thinking_toggle(monkeypatch):
    translator = _make_translator(
        monkeypatch, "https://ark.cn-beijing.volces.com/api/v3", "ep-2026-alias"
    )

    assert _extra_body(translator) == {"thinking": {"type": "disabled"}}


def test_glm_model_uses_nested_thinking_toggle(monkeypatch):
    translator = _make_translator(monkeypatch, "https://example.com/v1", "glm-4.6")

    assert _extra_body(translator) == {"thinking": {"type": "disabled"}}


def test_non_deepseek_models_keep_legacy_toggle(monkeypatch):
    translator = _make_translator(monkeypatch, "https://example.com/v1", "qwen3")

    assert _extra_body(translator) == {"enable_thinking": False}


def test_official_openai_endpoint_sends_no_thinking_param(monkeypatch):
    translator = _make_translator(
        monkeypatch, "https://api.openai.com/v1", "gpt-5.1"
    )

    assert _extra_body(translator) is None


# ── explicit styles ──


def test_explicit_vllm_style_uses_chat_template_kwargs(monkeypatch):
    translator = _make_translator(
        monkeypatch,
        "https://example.com/v1",
        "deepseek-r1-distill",
        thinking_style="vllm",
    )

    assert _extra_body(translator) == {
        "chat_template_kwargs": {"enable_thinking": False}
    }


def test_explicit_openai_style_uses_reasoning_effort(monkeypatch):
    translator = _make_translator(
        monkeypatch, "https://example.com/v1", "grok-4.3", thinking_style="openai"
    )

    assert _extra_body(translator) == {"reasoning_effort": "none"}


def test_explicit_off_style_sends_nothing(monkeypatch):
    translator = _make_translator(
        monkeypatch, "https://example.com/v1", "deepseek-v4", thinking_style="off"
    )

    assert _extra_body(translator) is None


def test_explicit_deepseek_style_overrides_detection(monkeypatch):
    translator = _make_translator(
        monkeypatch, "https://example.com/v1", "ep-custom", thinking_style="deepseek"
    )

    assert _extra_body(translator) == {"thinking": {"type": "disabled"}}


# ── legacy no_think migration ──


def test_legacy_no_think_false_sends_nothing(monkeypatch):
    translator = _make_translator(
        monkeypatch, "https://api.deepseek.com/v1", "deepseek-v4", no_think=False
    )

    assert _extra_body(translator) is None


# ── interaction with explicit extra_body ──


def test_explicit_extra_body_overrides_automatic_toggle(monkeypatch):
    translator = _make_translator(
        monkeypatch,
        "https://api.deepseek.com",
        "deepseek-v4-pro",
        extra_body={"thinking": {"type": "enabled"}, "user_id": "test"},
    )

    assert _extra_body(translator) == {
        "thinking": {"type": "enabled"},
        "user_id": "test",
    }


def test_target_language_clone_preserves_thinking_control(monkeypatch):
    translator = _make_translator(
        monkeypatch, "https://api.deepseek.com", "deepseek-v4-pro"
    )

    clone = translator.with_target_language("ja")

    assert _extra_body(clone) == {"thinking": {"type": "disabled"}}


# ── helpers ──


def test_resolve_thinking_style_passthrough():
    assert resolve_thinking_style("vllm", "https://api.deepseek.com", "x") == "vllm"
    assert resolve_thinking_style("off", "https://api.deepseek.com", "x") == "off"


def test_thinking_disable_body_returns_fresh_dicts():
    first = thinking_disable_body("deepseek")
    first["thinking"]["type"] = "mutated"

    assert thinking_disable_body("deepseek") == {"thinking": {"type": "disabled"}}


# ── Local Qwen Thinking Mode Disabled ──


def test_local_qwen_translator_prompt_disables_thinking(monkeypatch):
    from translator import LocalQwenTranslator
    from unittest.mock import MagicMock

    mock_tok = MagicMock()
    mock_tok.apply_chat_template.return_value = "<system>sys</system><user>hi</user><think>\n\n</think>\n"
    monkeypatch.setattr(LocalQwenTranslator, "_shared_tokenizer", mock_tok)
    monkeypatch.setattr(LocalQwenTranslator, "_shared_model", MagicMock())
    monkeypatch.setattr(LocalQwenTranslator, "_shared_model_path", "Qwen/Qwen3.5-4B")

    translator = LocalQwenTranslator(model_name_or_path="Qwen/Qwen3.5-4B", target_language="en")
    prompt = translator._build_prompt("こんにちは", "ja")

    assert mock_tok.apply_chat_template.called
    call_kwargs = mock_tok.apply_chat_template.call_args.kwargs
    assert call_kwargs.get("enable_thinking") is False


def test_local_qwen_translator_scrubs_thinking_tags(monkeypatch):
    import torch
    from translator import LocalQwenTranslator
    from unittest.mock import MagicMock

    mock_tok = MagicMock()
    mock_model = MagicMock()
    mock_model.device = "cpu"

    # Simulated token encoding and generation
    mock_tok.return_value = MagicMock(input_ids=torch.zeros((1, 5), dtype=torch.long))
    mock_tok.return_value.to.return_value = mock_tok.return_value
    mock_model.generate.return_value = torch.zeros((1, 10), dtype=torch.long)
    mock_tok.decode.return_value = "<think>Wait, how to say hello?</think>Hello!"

    monkeypatch.setattr(LocalQwenTranslator, "_shared_tokenizer", mock_tok)
    monkeypatch.setattr(LocalQwenTranslator, "_shared_model", mock_model)
    monkeypatch.setattr(LocalQwenTranslator, "_shared_model_path", "Qwen/Qwen3.5-4B")

    translator = LocalQwenTranslator(model_name_or_path="Qwen/Qwen3.5-4B", target_language="en")
    result = translator.translate("こんにちは", "ja")

    assert result == "Hello!"
    assert "<think>" not in result


def test_local_qwen_warmup_primes_model_and_usage(monkeypatch):
    import torch
    from translator import LocalQwenTranslator
    from unittest.mock import MagicMock

    mock_tok = MagicMock()
    mock_model = MagicMock()
    mock_model.device = "cpu"

    mock_tok.return_value = MagicMock(input_ids=torch.zeros((1, 5), dtype=torch.long))
    mock_tok.return_value.to.return_value = mock_tok.return_value
    mock_model.generate.return_value = torch.zeros((1, 8), dtype=torch.long)
    mock_tok.decode.return_value = "Hello"

    monkeypatch.setattr(LocalQwenTranslator, "_shared_tokenizer", mock_tok)
    monkeypatch.setattr(LocalQwenTranslator, "_shared_model", mock_model)
    monkeypatch.setattr(LocalQwenTranslator, "_shared_model_path", "Qwen/Qwen3.5-4B")
    monkeypatch.setattr(LocalQwenTranslator, "_shared_warmed_up", False)

    translator = LocalQwenTranslator(model_name_or_path="Qwen/Qwen3.5-4B", target_language="en")
    assert LocalQwenTranslator.is_warmed_up() is False

    translator.warmup()
    assert LocalQwenTranslator.is_warmed_up() is True
    # Warmup dummy pass resets token usage counters
    assert translator.last_usage == (0, 0)


def test_app_translator_warmup_coordination(monkeypatch):
    from unittest.mock import MagicMock
    from main import LiveTranslateApp
    from translator import LocalQwenTranslator

    monkeypatch.setattr(LocalQwenTranslator, "_shared_warmed_up", False)
    mock_translator = MagicMock()
    mock_translator.is_warmed_up.return_value = False

    app = LiveTranslateApp.__new__(LiveTranslateApp)
    import threading
    app._translator_ready = threading.Event()
    app._translator = mock_translator

    assert app.needs_translator_warmup() is True
    assert app._translator_ready.is_set() is False

    app.warmup_translator()
    assert mock_translator.warmup.called
    assert app._translator_ready.is_set() is True
