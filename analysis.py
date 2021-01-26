import datetime as dt
import pprint

import pandas as pd
import matplotlib.pyplot as plt
import boto3
from boto3.dynamodb.conditions import Key

from common.utils import convert_decimal_to_float


today = dt.date.today()
market_start = dt.datetime(
    year=today.year, month=today.month, day=today.day-1, hour=9
).timestamp()
table = boto3.resource("dynamodb").Table("stock")
keycondition = KeyConditionExpression=Key("symbol").eq("AAPL") &\
    Key("timestamp").gte(int(market_start))
records = table.query(KeyConditionExpression=keycondition)["Items"]

records = [
    convert_decimal_to_float(record) for record in records
]

df = pd.DataFrame(records)
df.plot(x="timestamp", y="price")
plt.show()
