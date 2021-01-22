import boto3


# main index
table_name = "stock"
partition_key = "symbol"
sort_key = "timestamp"


def create_table():
    dynamodb = boto3.resource("dynamodb")
    dynamodb.create_table(
        AttributeDefinitions=[
            {"AttributeName": partition_key, "AttributeType": "S"},
            {"AttributeName": sort_key,      "AttributeType": "N"},
        ],
        TableName=table_name,
        KeySchema=[
            {"AttributeName": partition_key, "KeyType": "HASH"},
            {"AttributeName": sort_key,      "KeyType": "RANGE"},
        ],
        BillingMode="PAY_PER_REQUEST",
        SSESpecification={
            "Enabled": False,
        },
        Tags=[
            {
                "Key": "purpose",
                "Value": "stock_trading"
            },
        ],
        StreamSpecification={
            "StreamEnabled": True,
            "StreamViewType": "NEW_IMAGE",
        },
    )


if __name__ == "__main__":
    create_table()
