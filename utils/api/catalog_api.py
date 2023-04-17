import os
import json
import uuid
import requests
from utils.rabbitmq.rabbitmq_receive import *
from utils.db.db_utils import MSSQLConnector
from utils.rabbitmq.rabbit_messages import RabbitMessages
from dotenv import load_dotenv
from utils.rabbitmq.rabbit_messages import RabbitMessages


load_dotenv()
usercheckout=os.getenv('USERCHECKOUT')
exchange=os.getenv('EXCHANGE')
instock=os.getenv('STOCKCONFIRMERD')
stockreject=os.getenv('STOCKREJECT')
paymentfail=os.getenv('PAYMENTFAIL')
paymentsucceeded=os.getenv('PAYMENTSUCCEEDED')

class CatalogApi:

    def stock_stockconfirmed(self):
        body = RabbitMessages().stockconfirmed()
        with RabbitMQ() as mq:
            mq.publish(exchange=exchange, routing_key=instock, body=json.dumps(body))

    def stock_reject(self):
        body = RabbitMessages().stockreject()
        with RabbitMQ() as mq:
            mq.publish(exchange=exchange, routing_key=stockreject, body=json.dumps(body))