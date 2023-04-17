import os
import json
import uuid
import requests
from utils.rabbitmq.rabbitmq_receive import *
from utils.db.db_utils import MSSQLConnector
from utils.rabbitmq.rabbitmq_receive import *
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


class BasketApi:
    def submmit(self):
        body=RabbitMessages().usercheckout()
        with RabbitMQ() as mq:
                mq.publish(exchange=exchange, routing_key=usercheckout, body=json.dumps(body))



