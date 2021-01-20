import queue
import datetime
import time
from threading import Thread

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.order import Order
from ibapi.utils import iswrapper

from utils import setup_log


logger = setup_log(__name__, "local")


class IBWrapper(EWrapper):

    def init_error(self):
        error_queue = queue.Queue()
        self.my_errors_queue = error_queue

    def is_error(self):
        error_exist = not self.my_errors_queue.empty()
        return error_exist

    def get_error(self, timeout=6):
        if self.is_error():
            try:
                return self.my_errors_queue.get(timeout=timeout)
            except queue.Empty:
                return None
        return None

    @iswrapper
    def error(self, id, errorCode, errorString):
        # Overrides the native method
        errormessage = (
            f"IB returns an error with {id} errorcode {errorCode} "
            f"that says {errorString}"
        )
        self.my_errors_queue.put(errormessage)

    def init_time(self):
        time_queue = queue.Queue()
        self.my_time_queue = time_queue
        return time_queue

    @iswrapper
    def currentTime(self, server_time):
        self.my_time_queue.put(server_time)

    @iswrapper
    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.nextorderId = orderId

    @iswrapper
    def orderStatus(
            self, orderId: int, status: str, filled: float,
            remaining: float, avgFillPrice: float, permId: int,
            parentId: int, lastFillPrice: float, clientId: int,
            whyHeld: str, mktCapPrice: float
    ):
        print("OrderStatus. Id:", orderId, "Status:", status,
              "Filled:", filled, "Remaining:", remaining, "AvgFillPrice:",
              avgFillPrice, "PermId:", permId, "ParentId:", parentId,
              "LastFillPrice:", lastFillPrice, "ClientId:", clientId,
              "WhyHeld:", whyHeld, "MktCapPrice:", mktCapPrice)


class IBClient(EClient):

    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

    def server_clock(self):
        logger.debug("Asking server for Unix time")

        # Creates a queue to store the time
        time_storage = self.wrapper.init_time()

        # Sets up a request for unix time from the Eclient
        self.reqCurrentTime()

        # Specifies a max wait time if there is no connection
        max_wait_time = 10

        try:
            requested_time = time_storage.get(timeout=max_wait_time)
        except queue.Empty:
            logger.debug("The queue was empty or max time reached")
            requested_time = None

        while self.wrapper.is_error():
            logger.debug("Error:")
            logger.debug(self.get_error(timeout=5))

        return requested_time


class IBApp(IBWrapper, IBClient):

    def __init__(self, ipaddress, portid, clientid):
        self.init_error()

        IBWrapper.__init__(self)
        IBClient.__init__(self, wrapper=self)

        self.connect(ipaddress, portid, clientid)

        thread = Thread(target=self.run)
        thread.start()
        setattr(self, "_thread", thread)


def create_contract(symbol):
    """
    Fills out the contract object
    Since I am going to deal with the stock only and most probably
    in the US market, the rest of the contract will be hard coded.

    In the API side, NASDAQ is always defined as ISLAND in the exchange field

    SKT: stock
    SMART: smart routing function that uses an algorithm to use the best
        routing at the time of the order in terms of price and liquidity

    contract1.PrimaryExch = "NYSE"
    """
    contract = Contract()
    contract.symbol = symbol
    contract.secType = "STK"   # Defines the security type as stock
    contract.currency = "USD"  # Currency is US dollars
    contract.exchange = "SMART"
    return contract    # Returns the contract object


def orderCreate(action: str, quantity: int):
    """
    Fills out the order object

    action: "BUY" or "SELL"
    """
    order = Order()
    order.action = action
    order.orderType = "MKT"
    order.transmit = True
    order.totalQuantity = quantity
    return order   # Returns the order object


def orderExecution(app: IBApp, symbol: str, action: str, quantity: int):
    """
    Places the order with the returned contract and order objects
    """
    contractObject = create_contract(symbol)
    orderObject = orderCreate(action, quantity)
    app.placeOrder(app.nextorderId, contractObject, orderObject)


if __name__ == '__main__':
    logger.debug("Connecting to the server...")
    app = IBApp("127.0.0.1", 7497, 0)

    time.sleep(10)

    logger.debug("Getting server time")
    requested_time = app.server_clock()

    logger.info(f"The current time from the server is {requested_time}")

    symbol = "AAPL"
    logger.debug("Buying apple stock")
    orderExecution(app, symbol=symbol, action="BUY", quantity=10)

    time.sleep(5)

    logger.debug("Disconnecting from the server...")
    app.disconnect()
