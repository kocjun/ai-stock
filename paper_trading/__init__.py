"""
Paper Trading 모듈
"""

# paper_trading.py 모듈에서 필요한 함수들을 export
from .paper_trading import (
    get_portfolio,
    update_portfolio_values,
    execute_buy,
    execute_sell,
    get_latest_price
)

__all__ = [
    'get_portfolio',
    'update_portfolio_values',
    'execute_buy',
    'execute_sell',
    'get_latest_price'
]
