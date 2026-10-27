"""按需导出验证码服务，避免只读配置或并发状态时加载所有浏览器引擎。"""
from importlib import import_module


_EXPORTS = {
    "SliderConcurrencyManager": ("concurrency", "SliderConcurrencyManager"),
    "concurrency_manager": ("concurrency", "concurrency_manager"),
    "disabled_account_manager": ("concurrency", "disabled_account_manager"),
    "should_skip_account": ("concurrency", "should_skip_account"),
    "acquire_browser_slot": ("concurrency", "acquire_browser_slot"),
    "release_browser_slot": ("concurrency", "release_browser_slot"),
    "get_browser_stats": ("concurrency", "get_browser_stats"),
    "RetryStrategyStats": ("strategy_stats", "RetryStrategyStats"),
    "strategy_stats": ("strategy_stats", "strategy_stats"),
    "get_random_browser_features": ("browser_features", "get_random_browser_features"),
    "get_stealth_script": ("browser_features", "get_stealth_script"),
    "TrajectoryGenerator": ("trajectory", "TrajectoryGenerator"),
    "SliderElementFinder": ("slider_elements", "SliderElementFinder"),
    "VerificationChecker": ("verification_checker", "VerificationChecker"),
    "HistoryManager": ("history_manager", "HistoryManager"),
    "PlaywrightSliderService": ("slider_stealth", "PlaywrightSliderService"),
    "SliderStealth": ("slider_stealth", "PlaywrightSliderService"),
    "get_slider_stats": ("slider_stealth", "get_slider_stats"),
    "run_slider_verification": ("slider_stealth", "run_slider_verification"),
    "DrissionPageSliderService": ("drissionpage_slider", "DrissionPageSliderService"),
    "run_drissionpage_verification": ("drissionpage_slider", "run_drissionpage_verification"),
    "DRISSIONPAGE_AVAILABLE": ("drissionpage_slider", "DRISSIONPAGE_AVAILABLE"),
    "run_slider_verification_with_fallback": ("orchestrator", "run_slider_verification_with_fallback"),
}

__all__ = list(_EXPORTS)


def __getattr__(name):
    try:
        module, attribute = _EXPORTS[name]
    except KeyError:
        raise AttributeError(f"module {__name__!r} has no attribute {name!r}") from None
    value = getattr(import_module(f"common.services.captcha.{module}"), attribute)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
