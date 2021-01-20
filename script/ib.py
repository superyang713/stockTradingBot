import logging
import datetime
import queue
import time
import threading

from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.common import BarData
from ibapi.utils import iswrapper

from utils import setup_log


"""
reuqest_ID = 1  -> apple
reuqest_ID = 2  -> tesla
"""

host = "127.0.0.1"
port = 7497
client_id = 1234

logger = setup_log(__name__, "local")


class IBAPIWrapper(EWrapper):
    """
    A derived subclass of the IB API EWrapper interface
    that deals with responses from IB server
    """

    @iswrapper
    def error(self, id, errorCode, errorString):
        # error_message = (
        #     "IB Error ID (%d), Error Code (%d) with "
        #     "response '%s'" % (id, errorCode, errorString)
        # )
        # logger.debug(error_message)
        if errorCode == "-1":
            self._handle_missing_data()

    @iswrapper
    def tickPrice(self, reqId, tickType, price, attrib):
        logger.debug('The current ask price is: %s with ID %s', price, reqId)

    @iswrapper
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        logger.debug("setting nextValidOrderId: %d", orderId)
        self.nextValidOrderId = orderId

    @iswrapper
    def orderStatus(
            self, orderId: int, status: str, filled: float,
            remaining: float, avgFillPrice: float, permId: int,
            parentId: int, lastFillPrice: float, clientId: int,
            whyHeld: str, mktCapPrice: float
    ):
        print("OrderStatus. Id:", orderId, "Status:", status, "Filled:", filled,
              "Remaining:", remaining, "AvgFillPrice:", avgFillPrice,
              "PermId:", permId, "ParentId:", parentId, "LastFillPrice:",
              lastFillPrice, "ClientId:", clientId, "WhyHeld:",
              whyHeld, "MktCapPrice:", mktCapPrice)


class IBAPIClient(EClient):
    """
    Used to send messages to the IB servers via the API.
    """

    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

    def obtain_apple_stock(self):
        apple_contract = Contract()
        apple_contract.symbol = 'TSLA'
        apple_contract.secType = 'STK'
        apple_contract.exchange = 'SMART'
        apple_contract.currency = 'USD'

        # Request Market Data
        self.reqMktData(1, apple_contract, '', False, False, [])

    def obtain_tesla_stock(self):
        tesla_contract = Contract()
        tesla_contract.symbol = 'GE'
        tesla_contract.secType = 'STK'
        tesla_contract.exchange = 'SMART'
        tesla_contract.currency = 'USD'

        # Request Market Data
        self.reqMktData(2, tesla_contract, '', False, False, [])

    def place_order(self):
        contract = Contract()
        contract.symbol = 'AAPL'
        contract.secType = 'STK'
        contract.exchange = 'SMART'
        contract.currency = 'USD'
        contract.primaryExchange = "NASDAQ"

        order = Order()
        order.action = "BUY"
        order.totalQuantity = 10
        order.orderType = "LMT"
        order.lmtPrice = 130

        self.placeOrder(self.wrapper.nextOrderId, contract, order)


class IBAPIApp(IBAPIWrapper, IBAPIClient):
    """
    The IB API application class creates the instances
    of IBAPIWrapper and IBAPIClient, through a multiple
    inheritance mechanism.

    When the class is initialised it connects to the IB
    server. At this stage multiple threads of execution
    are generated for the client and wrapper.

    Parameters
    ----------
    ipaddress : `str`
        The IP address of the TWS client/IB Gateway
    portid : `int`
        The port to connect to TWS/IB Gateway with
    clientid : `int`
        An (arbitrary) client ID, that must be a positive integer
    """

    def __init__(self, ipaddress, portid, clientid):
        IBAPIWrapper.__init__(self)
        IBAPIClient.__init__(self, wrapper=self)

        # Connects to the IB server with the
        # appropriate connection parameters
        self.connect(ipaddress, portid, clientid)

        # Initialise the threads for various components
        thread = threading.Thread(target=self.run)
        thread.start()
        setattr(self, "_thread", thread)

        # Num 3 means use delayed data.
        # Comment this if use real time data
        # self.reqMarketDataType(3)


if __name__ == '__main__':
    app = IBAPIApp(host, port, client_id)

    app.obtain_apple_stock()
    app.obtain_tesla_stock()
    # app.nextOrderId = 8
    # app.place_order()
    app.run()

    # Disconnect from the IB server
    app.disconnect()

    logger.debug("Disconnected from the IB API application. Finished.")
