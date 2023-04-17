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

class PaymentApi:
    def payment_succses(self):
        body = RabbitMessages().paymentsuccses()
        with RabbitMQ() as mq:
            mq.publish(exchange=exchange, routing_key=paymentsucceeded, body=json.dumps(body))

    def payment_fail(self):
        body = RabbitMessages().paymentfail()
        with RabbitMQ() as mq:
            mq.publish(exchange=exchange, routing_key=paymentfail, body=json.dumps(body))