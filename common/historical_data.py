import queue
import os
import time
import datetime
import csv

from ibapi.wrapper import EWrapper
from ibapi.client import EClient
from ibapi.contract import Contract
from ibapi.utils import iswrapper
from threading import Thread

from common.utils import setup_log


DEFAULT_HISTORIC_DATA_ID = 50
DEFAULT_GET_CONTRACT_ID = 43
FINISHED = None
STARTED = None
TIME_OUT = None

logger = setup_log(__name__, "local")


class finishableQueue:

    def __init__(self, queue_to_finish):

        self._queue = queue_to_finish
        self.status = STARTED

    def get(self, timeout):
        """
        Returns a list of queue elements once timeout is finished,
        or a FINISHED flag is received in the queue

        Params:
            timeout: how long to wait before giving up

        Return
            list of queue elements
        """
        contents_of_queue = []
        finished = False

        while not finished:
            try:
                current_element = self._queue.get(timeout=timeout)
                if current_element is FINISHED:
                    finished = True
                    self.status = FINISHED
                else:
                    contents_of_queue.append(current_element)
                    # keep going and try and get more data

            except queue.Empty:
                # If we hit a time out it's most probable we're not
                # getting a finished element any time soon give up
                # and return what we have
                finished = True
                self.status = TIME_OUT

        return contents_of_queue

    def timed_out(self):
        return self.status is TIME_OUT


class TestWrapper(EWrapper):
    def __init__(self):
        self._my_contract_details = {}
        self._my_historic_data_dict = {}
        self._my_errors = queue.Queue()

    def init_error(self):
        error_queue = queue.Queue()
        self._my_errors = error_queue

    def get_error(self, timeout=5):
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None

        return None

    def is_error(self):
        an_error_if = not self._my_errors.empty()
        return an_error_if

    @iswrapper
    def error(self, id, errorCode, errorString):
        errormsg = "IB error id {} errorcode {} string {}".format(
            id, errorCode, errorString
        )
        self._my_errors.put(errormsg)

    @iswrapper
    def contractDetails(self, reqId, contractDetails):

        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(contractDetails)

    @iswrapper
    def contractDetailsEnd(self, reqId):
        if reqId not in self._my_contract_details.keys():
            self.init_contractdetails(reqId)

        self._my_contract_details[reqId].put(FINISHED)

    @iswrapper
    def historicalData(self, tickerid, bar):
        bardata = (bar.date, bar.open, bar.high, bar.low, bar.close,
                   bar.volume)

        historic_data_dict = self._my_historic_data_dict

        # Add on to the current data
        if tickerid not in historic_data_dict.keys():
            self.init_historicprices(tickerid)

        historic_data_dict[tickerid].put(bardata)

    @iswrapper
    def historicalDataEnd(self, tickerid, start: str, end: str):
        if tickerid not in self._my_historic_data_dict.keys():
            self.init_historicprices(tickerid)

        self._my_historic_data_dict[tickerid].put(FINISHED)

    def init_contractdetails(self, reqId):
        """
        get contract details code
        """
        contract_details_queue = self._my_contract_details[
            reqId] = queue.Queue()

        return contract_details_queue

    def init_historicprices(self, tickerid):
        historic_data_queue = self._my_historic_data_dict[
            tickerid] = queue.Queue()

        return historic_data_queue


class TestClient(EClient):

    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

    def resolve_ib_contract(self, ibcontract, reqId=DEFAULT_GET_CONTRACT_ID):
        """
        From a partially formed contract, returns a fully fledged version
        :returns fully resolved IB contract
        """
        contract_details_queue = finishableQueue(
            self.init_contractdetails(reqId))

        print("Getting full contract details from the server... ")

        self.reqContractDetails(reqId, ibcontract)

        # Run until we get a valid contract(s) or get bored waiting
        MAX_WAIT_SECONDS = 10
        new_contract_details = contract_details_queue.get(
            timeout=MAX_WAIT_SECONDS)

        while self.wrapper.is_error():
            print(self.get_error())

        if contract_details_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished")

        if len(new_contract_details) == 0:
            print("Failed to get additional contract details")
            return ibcontract

        if len(new_contract_details) > 1:
            print("got multiple contracts using first one")

        new_contract_details = new_contract_details[0]

        resolved_ibcontract = new_contract_details.contract
        print(resolved_ibcontract)

        return resolved_ibcontract

    def get_IB_historical_data(
            self,
            ibcontract,
            durationStr="1 Y",
            barSizeSetting="1 day",
            tickerid=DEFAULT_HISTORIC_DATA_ID
    ):
        """
        Returns historical prices for a contract, up to today
        ibcontract is a Contract
        :returns list of prices in 4 tuples: Open high low close volume
        """
        historic_data_queue = finishableQueue(
            self.init_historicprices(tickerid))

        # Request some historical data. Native method in EClient
        today = datetime.datetime.today().strftime("%Y%m%d %H:%M:%S %Z")
        self.reqHistoricalData(
            tickerid,        # tickerId,
            ibcontract,      # contract,
            today,           # endDateTime,
            durationStr,     # durationStr,
            barSizeSetting,  # barSizeSetting,
            "TRADES",        # whatToShow,
            1,               # useRTH,
            1,               # formatDate
            False,           # KeepUpToDate <<==== added for api 9.73.2
            []               # chartoptions not used
        )

        MAX_WAIT_SECONDS = 10
        print("Getting historical data from the server...")
        historic_data = historic_data_queue.get(timeout=MAX_WAIT_SECONDS)

        while self.wrapper.is_error():
            print(self.get_error())

        if historic_data_queue.timed_out():
            print("Exceeded maximum wait for wrapper to confirm finished")

        self.cancelHistoricalData(tickerid)
        return historic_data


class TestApp(TestWrapper, TestClient):
    def __init__(self, ipaddress, portid, clientid):
        TestWrapper.__init__(self)
        TestClient.__init__(self, wrapper=self)

        self.connect(ipaddress, portid, clientid)

        thread = Thread(target=self.run)
        thread.start()

        setattr(self, "_thread", thread)

        self.init_error()


def write_to_csv(filename, data: list):
    csv_file_path = os.path.join(
        os.path.abspath(os.path.dirname(os.path.dirname(__file__))),
        "historical_data",
        filename,
    )
    fieldnames = ["Date", "Open", "High", "Low", "Close", "Volume"]
    with open(csv_file_path, "w") as fout:
        writer = csv.DictWriter(fout, fieldnames=fieldnames)
        writer.writeheader()
        for record in data:
            writer.writerow(dict(zip(fieldnames, record)))


def retrieve_historical_data(contract: Contract, filename=None):
    filename = f"{contract.symbol}.csv" if not filename else filename

    app = TestApp("127.0.0.1", 7497, 1)

    resolved_ibcontract = app.resolve_ib_contract(contract)
    historic_data = app.get_IB_historical_data(resolved_ibcontract)

    write_to_csv(filename, historic_data)
    time.sleep(3)

    app.disconnect()
