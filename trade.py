from ibapi.contract import Contract

from common.historical_data import retrieve_historical_data
from common.trade import orderExecution
from common.utils import setup_log


logger = setup_log(__name__, "local")


if __name__ == '__main__':
    # example for retrieving historical data
    contract = Contract()
    contract.symbol = 'AAPL'
    contract.secType = 'STK'
    contract.exchange = 'SMART'
    contract.currency = 'USD'
    contract.primaryExchange = "NASDAQ"

    retrieve_historical_data(contract)

    # example for placing an order
    symbol = "AAPL"
    logger.debug("Starting the process of buying %s stock", symbol)
    orderExecution(symbol=symbol, action="BUY", quantity=1)
