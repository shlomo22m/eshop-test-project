import json
import uuid
import requests
from utils.api.bearer_tokenizer import BearerTokenizer
from utils.db.db_utils import *
import datetime


class OrderingAPI:
    def __init__(self, username='bob', password='Pass123%24'):
        self.base_url = 'http://localhost:5102'
        #self.bearer_token = BearerTokenizer().bearer_token
        self.bearer_token = BearerTokenizer(username, password).bearer_token
        self.headers = {"Authorization": f"Bearer {self.bearer_token}"}
        self.username=username
        self.body = None

    def get_order_by_id(self, order_id):

        order = requests.get(f'{self.base_url}/api/v1/orders/{order_id}', headers=self.headers)
        return order

    def update_to_shiped(self,order_id):
        headers = {
                    'Authorization':f'Bearer {self.bearer_token}',
                    'Content-Type': 'application/json',
                    'x-requestid': str(uuid.uuid4())
                  }
        endpoint = f'{self.base_url}/ordering-api/api/v1/Orders/ship'
        self.body = {"orderNumber": order_id}
        respone=requests.put(url=endpoint, data=json.dumps(self.body),headers=headers)
        return respone.status_code


    def cancel_order(self,order_id):
        headers = {
                    'Authorization': f'Bearer {self.bearer_token}',
                    'Content-Type': 'application/json',
                    'x-requestid': str(uuid.uuid4())
                  }
        endpoint = f'{self.base_url}/ordering-api/api/v1/Orders/cancel'
        self.body = {"orderNumber": order_id}
        requests.put(url=endpoint, data=json.dumps(self.body), headers=headers)

    def status(self):
        response = requests.get(self.base_url, headers=self.headers)
        return response.status_code


    def get_orders(self):
        #print(self.headers)
        order = requests.get(url='http://host.docker.internal:5102/ordering-api/api/v1/Orders', headers=self.headers)
        return order


if __name__ == '__main__':
    import pprint
    api = OrderingAPI()

    #pprint.pprint(api.get_order_by_id(21).json())
    # with MSSQLConnector() as conn:
    #     orderid = conn.select_query('SELECT Name from ordering.buyers where Id=21')
    #     print(orderid[0]['Name'])
        #orderids = conn.select_query('SELECT MAX(Id) from ordering.orders where orders.OrderStatusId = 2')
        #print(orderid[0][''])
        #orderid=orderid[0]['']
    print(str(uuid.uuid4()))
    #orders=(api.get_order_by_id(68))
    # order=api.get_orders().json()
    # for i in order:
    #     pprint.pprint(i['ordernumber'])
    # pprint.pprint(api.username)
    #print(api.get_order_by_id(53).json())
    #api.update_to_shiped(41)
    #print(api.status())
    #api.cancel_order(44)

