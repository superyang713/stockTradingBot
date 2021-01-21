from ibapi.contract import Contract

from common.stream import stream
from common.utils import setup_log


logger = setup_log(__name__, "local")


if __name__ == '__main__':
    # example for streaming real time data
    apple_contract = Contract()
    apple_contract.symbol = 'AAPL'
    apple_contract.secType = 'STK'
    apple_contract.exchange = 'SMART'
    apple_contract.currency = 'USD'
    apple_contract.primaryExchange = "NASDAQ"

    tesla_contract = Contract()
    tesla_contract.symbol = 'TSLA'
    tesla_contract.secType = 'STK'
    tesla_contract.exchange = 'SMART'
    tesla_contract.currency = 'USD'
    tesla_contract.primaryExchange = "NASDAQ"

    details = [
        {
            "contract": apple_contract,
            "data_id": 1
        },
        {
            "contract": tesla_contract,
            "data_id": 2
        },
    ]
    stream(details)
