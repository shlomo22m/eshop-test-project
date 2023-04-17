import uuid
import json
import pika
import datetime
from utils.db.db_utils import MSSQLConnector
class RabbitMessages:
    def usercheckout(self,productid=1,quantity=1,cardtype=1,username="alice",cardsecuritynumber='123',cardnumber='4012888888881881',
                     year='2024',month='12',day='31'):
     if username!='alice':
         userid=str(uuid.uuid4())
         cardnameholder="john wick"
     else:
         userid='b9e5dcdd-dae2-4b1c-a991-f74aae042814'
         cardnameholder = "Alice Smith"
     body={
            "UserId": f'{userid}',
            "UserName": username,
            "OrderNumber": 0,
            "City": "Redmond",
            "Street": "15703 NE 61st Ct",
            "State": "WA",
            "Country": "U.S.",
            "ZipCode": "98052",
            "CardNumber": cardnumber,
            "CardHolderName": cardnameholder,
            "CardExpiration": f"{year}-{month}-{day}T22:00:00Z",
            "CardSecurityNumber": cardsecuritynumber,
            "CardTypeId": cardtype,
            "Buyer": 'null',
            "RequestId": str(uuid.uuid4()),
            "Basket": {
                        "BuyerId": "b9e5dcdd-dae2-4b1c-a991-f74aae042814",
                        "Items": [
                           {
                                "Id": "c1f98125-a109-4840-a751-c12a77f58dff",
                                "ProductId": 1,
                                "ProductName": ".NET Bot Black Hoodie",
                                "UnitPrice": 19.5,
                                "OldUnitPrice": 0,
                                "Quantity": 1,
                                 "PictureUrl": "http://host.docker.internal:5202/c/api/v1/catalog/items/1/pic/"
                           }
                                 ]
  },
            "Id": "16c5ddbc-229e-4c19-a4bd-d4148417529c",
            "CreationDate": "2023-03-04T14:20:24.4730559Z"
         }
     return body

    def stockconfirmed(self):
        with MSSQLConnector() as conn:
            id=conn.select_query('SELECT MAX(Id) FROM ordering.orders')
        body={
                "OrderId": id[0][''] ,
                "Id": "e9b80940-c861-4e5b-9d7e-388fd256acef",
                "CreationDate": "2023-03-07T09:52:56.6412897Z"
             }
        return body


    def paymentsuccses(self):
        with MSSQLConnector() as conn:
            id = conn.select_query('SELECT MAX(Id) FROM ordering.orders')
        body={
                "OrderId": id[0][''],
                "Id": "b84dc7a5-1d0e-429e-a800-d3024d9c724f",
                "CreationDate": "2023-03-05T15:33:18.1376971Z"
             }
        return body

    def stockreject(self):
        with MSSQLConnector() as conn:
            id = conn.select_query('SELECT MAX(Id) FROM ordering.orders')
        body={
                "OrderId": id[0][''],
                "OrderStockItems": [
                 {
                     "ProductId": 1,
                     "HasStock": False
                 }
                                   ],
                 "Id": "99c3f974-c6ed-41a4-8e01-5cb00f9e6335",
                 "CreationDate": "2023-03-05T15:51:11.5458796Z"
             }
        return body

    def paymentfail(self):
        with MSSQLConnector() as conn:
            id = conn.select_query('SELECT MAX(Id) FROM ordering.orders')
        body={
                "OrderId": id[0][''],
                "OrderStatus": "stockconfirmed",
                "BuyerName": "alice",
                "Id": "cca155c0-4480-4c93-a763-910e54218040",
                "CreationDate": "2023-03-05T17:07:35.6306122Z"
             }

        return body

    def respone_of_get_order_by_id(self,id):
        body={
                "ordernumber": 68,
                "date": "2023-03-13T10:47:52.5204089",
                 "status": "shipped",
                "description": None,
                "street": "15703 NE 61st Ct",
                "city": "Redmond",
                "zipcode": "98052",
                "country": "U.S.",
                "orderitems": [
                {
                    "productname": ".NET Black & White Mug",
                    "units": 1,
                    "unitprice": 8.5,
                    "pictureurl": "http://host.docker.internal:5202/c/api/v1/catalog/items/2/pic/"
                },
                {
                     "productname": ".NET Blue Hoodie",
                     "units": 1,
                        "unitprice": 12,
                    "pictureurl": "http://host.docker.internal:5202/c/api/v1/catalog/items/6/pic/"
                }
                            ],
                "total": 20.50
            }
        return body



