"""验证码服务的兼容导出；访问具体服务时才加载其依赖。"""
from . import _exports
from .strategy_stats import strategy_stats

# 与同名子模块区分，保留旧接口导出的统计单例。

__all__ = _exports.__all__


def __getattr__(name):
    value = getattr(_exports, name)
    globals()[name] = value
    return value


def __dir__():
    return sorted(set(globals()) | set(__all__))
