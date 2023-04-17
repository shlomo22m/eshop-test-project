import os
import pytest
import json
import time
from dotenv import load_dotenv
from utils.db.db_utils import MSSQLConnector
from utils.rabbitmq.rabbit_messages import RabbitMessages
from utils.api.ordering_api import OrderingAPI
from utils.api.basketapi import BasketApi
from utils.api.paymentapi import PaymentApi
from utils.api.catalog_api import CatalogApi
from utils.rabbitmq.rabbitmq_receive import *
from time import sleep
from utils.docker.docker_utils import DockerManager


load_dotenv()
usercheckout=os.getenv('USERCHECKOUT')
exchange=os.getenv('EXCHANGE')
instock=os.getenv('STOCKCONFIRMERD')
stockreject=os.getenv('STOCKREJECT')
paymentfail=os.getenv('PAYMENTFAIL')
paymentsucceeded=os.getenv('PAYMENTSUCCEEDED')

orderstart=os.getenv('ORDERSTART')
statussubmitted=os.getenv('STATUSSUBMITTED')
statusawaiting=os.getenv('STATUSAWAITING')
statusstockconfirmed=os.getenv('STATUSSTOCKCONFIRMED')
statuspaid=os.getenv('STATUSPAID')

dockerflag=0

submitted=int(os.getenv('SUBMITTED'))
awaitingvalidation=int(os.getenv('AWAITINGVALIDATION'))
stockconfirmerd=int(os.getenv('STOCKCONFIRMED'))
paid=int(os.getenv('PAID'))
shipped=int(os.getenv('SHIPPED'))
cancelled=int(os.getenv('CANCELLED'))

currentstatus=os.getenv('CURRENTSTATUS')
orderidbystatus=os.getenv('ORDERIDBYSTATUS')
totalorderscount=os.getenv('TOTALORDERSCOUNT')
orderstatusbyid=os.getenv('ORDERSTATUSBYID')





rabbit_queues = {1: 'Basket', 2: 'Catalog', 3: 'Payment', 4: 'Ordering.signalrhub'}




@pytest.fixture()
def docker():
    return DockerManager()

@pytest.fixture()
def messages():
    return RabbitMessages()

@pytest.fixture()
def payment():
    return PaymentApi()

@pytest.fixture()
def basket():
    return BasketApi()

@pytest.fixture()
def order_api():
    return OrderingAPI()

@pytest.fixture()
def catalog():
    return CatalogApi()

@pytest.fixture()
def rabbitsend():
    return RabbitMQ()




@pytest.mark.test_ordering_api_load_performance
def test_ordering_api_load_performance(messages,docker):
    '''
      writer: shlomo mhadker
      date:14.3.2023
     test number 31: stop ordering api service send a 100 create a new order requests
     start ordering api service again we expect that the process will create a new 100 orders in
     less than 1 hour
    '''

    with MSSQLConnector() as conn:
                # stop ordering.api service
                docker.stop('eshop/ordering.api:linux-latest')
                # sql query that get the count of orders that was made
                orderstart=conn.select_query(totalorderscount)

                #a for loop that create a 100 messegas
                for i in range(100):
                    body=messages.usercheckout()
                    with RabbitMQ() as mq:
                        mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
                sleep(int(os.getenv('STOP_START')))
                # stop ordering.api service
                docker.start('eshop/ordering.api:linux-latest')
                sleep(int(os.getenv('STOP_START')))
                #save the time that the ordering service has start
                start_time = time.time()
                #save the last order status
                laststatus = conn.select_query(currentstatus)

                #while loop that run as long one hour hasant pass
                while time.time() - start_time < int(os.getenv('HOUR')):
                    # a sql query that take the current last  order status
                    laststatus = conn.select_query(currentstatus)
                    # if last order is 4(paid) brake the while loop
                    if laststatus[0]['OrderStatusId'] == paid:
                        break
                    sleep(int(os.getenv('WAIT5')))
                #a variable that save how much time has pass
                elapsed_time = time.time() - start_time
                #if one hour didnt pass enter if condition
                if elapsed_time<=int(os.getenv('HOUR')):
                    # sql query that get the order status of the last 100 orders
                    last100 = conn.select_query(
                        'SELECT TOP (100) [Id],[OrderStatusId] FROM [Microsoft.eShopOnContainers.Services.OrderingDb].[ordering].[orders] order by Id desc')
                    #for loop that check every last 100 orders are in status 4(paid)
                    for i in(last100):
                        assert i['OrderStatusId']==paid
                # sql query that get the count of orders that was made
                orderendsnum = conn.select_query(totalorderscount)
                #stop the other services
                docker.stop_services()
                sleep(int(os.getenv('STOP_START')))
    #check that one hour didnt pass
    assert elapsed_time<=int(os.getenv('HOUR'))
    #check that a new 100 orders has been created
    assert orderstart[0][''] + 100 == orderendsnum[0]['']

@pytest.mark.test_MSS
def test_MSS(messages,docker,basket,catalog,payment,crash=0,stockfail=0,paymentfailf=0):
    '''
    writer: shlomo mhadker
    date:14.3.2023
    test number 1: with default param create a new order flow MSS
    '''
    body = messages.usercheckout()
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
                #take the cout of orders that was made
                ordersnum = conn.select_query(totalorderscount)
                #create a new order
                basket.submmit()

                #basket simulator receive the message that order api send
                mq.consume('Basket', callback)
                #check that the message with the right routing key has arrived from ordering api
                assert returnglob() == orderstart

                #ordering.signalrhub simulator receive the message that order api send
                mq.consume('Ordering.signalrhub', callback)
                # check that the message with the right routing key has arrived from ordering api
                assert returnglob() == statussubmitted

                #an sql query that take the current  order status
                orderstatus = conn.select_query(currentstatus)
                #check that the order status is in status 1(submitted)
                assert orderstatus[0]['OrderStatusId'] == submitted


                # catalog simulator receive the message that order api send
                mq.consume('Catalog', callback)
                # check that the message with the right routing key has arrived from ordering api
                assert returnglob() == statusawaiting
                # a sql query that take the current  order status
                orderstatus = conn.select_query(currentstatus)
                # check that the order status is in status 2(awaitingvalidation)
                assert orderstatus[0]['OrderStatusId'] == awaitingvalidation

                #a flag that we use in test 29(test_ordering_api_crash statis 2)
                if crash==2:
                    #stop ordering.api service
                    docker.stop('eshop/ordering.api:linux-latest')
                    #wait 30 sec
                    sleep(int(os.getenv('CRASH')))
                    #start ordering.api service
                    docker.start('eshop/ordering.api:linux-latest')
                    sleep(int(os.getenv('CRASH')))


                #ordering.signalrhub simulator receive the message that order api send
                mq.consume('Ordering.signalrhub', callback)
                # check that the message with the right routing key has arrived from ordering api
                assert returnglob() == statusawaiting

                # a flag that we use in tests 2,5,11 when test need order in status 2(awaitingvalidation)
                if stockfail==1:
                    #return the current  status of the order
                    return orderstatus[0]['OrderStatusId']


                #send to ordering.api a message that we have available stock
                catalog.stock_stockconfirmed()



                # ordering.signalrhub simulator receive the message that order api send
                mq.consume('Ordering.signalrhub', callback)
                # ordering.signalrhub simulator receive the message that order api send
                assert returnglob() == statusstockconfirmed

                # payment simulator receive the message that order api send
                mq.consume('Payment', callback)
                # check that the message with the right routing key has arrived from ordering api
                assert returnglob() == statusstockconfirmed
                # a sql query that take the current  order status
                orderstatus = conn.select_query(currentstatus)
                # check that the order status is in status 3(stockconfirmerd)
                assert orderstatus[0]['OrderStatusId'] == stockconfirmerd

                # a flag that we use in test 30(test_ordering_api_crash statis 3)
                if crash==3:
                    #stop ordering.api service
                    docker.stop('eshop/ordering.api:linux-latest')
                    #wait 30 sec
                    sleep(int(os.getenv('CRASH')))
                    #start ordering.api service
                    docker.start('eshop/ordering.api:linux-latest')
                    sleep(int(os.getenv('CRASH')))

                # a flag that we use in tests 3,6,12 when test need order in status 3(stockconfirmerd)
                if paymentfailf==1:
                    # return the current  status of the order
                    return orderstatus[0]['OrderStatusId']

                # send to ordering.api a message that we have payment is valid
                payment.payment_succses()
                # ordering.signalrhub simulator receive the message that order api send
                mq.consume('Ordering.signalrhub', callback)
                # check that the message with the right routing key has arrived from ordering api
                assert returnglob() == statuspaid
                # catalog simulator receive the message that order api send
                mq.consume('Catalog', callback)
                # check that the message with the right routing key has arrived from ordering api
                assert returnglob() == statuspaid

                # a sql query that take the current amount of orders
                result = conn.select_query(totalorderscount)
                # a sql query that take the current status of the last order that has made
                orderstatus = conn.select_query(currentstatus)

    #check that the current orders amount has grown by 1
    assert result[0][''] == ordersnum[0]['']+1
    # check that the current status of the new order we made is status 4(paid)
    assert orderstatus[0]['OrderStatusId'] == paid


@pytest.mark.test_outofstock
def test_outofstock(messages,docker,basket,catalog,payment):
    '''
    writer: shlomo mhadker
    date:14.3.2023
    test number 2: try to create order with not enough product quantity (using test 1)
    '''

    with MSSQLConnector() as conn:
            #activate test_MSS with stockfail flag that stop test_MSS when the order status is 2(awaitingvalidation)
            orderstatus=test_MSS(messages,docker,basket,catalog,payment,stockfail=1)

            #a time out variable
            timeout=0
            #send to order.api a message with routing key stockreject
            catalog.stock_reject()

            #a while loop that wait until the order status will change from status 2(awaitingvalidation) or 10 sec has pass
            while timeout<=int(os.getenv('WAIT10')):
                ## a sql query that check the current status of the last order that has made every sec
                orderstatus = conn.select_query(currentstatus)
                #if the status order has been changed brake the while loop
                if orderstatus[0]['OrderStatusId']!=awaitingvalidation:
                    break
                sleep(1)
                #a 1 sec to our time out variable
                timeout+=1
    #check that the new status of the new order is 6(cancelled)
    assert orderstatus[0]['OrderStatusId'] == cancelled


@pytest.mark.test_paymentfail
def test_paymentfail(messages,docker,basket,catalog,payment,cancel=0):
    '''
    writer: shlomo mhadker
    date:14.3.2023
    test number 3: try to create order with a payment fail (using test 1)
    '''

    with RabbitMQ() as mq:
        with MSSQLConnector() as conn:
            # activate test_MSS with paymentfailf flag that stop test_MSS when the order status is 3(stockconfirmerd)
            test_MSS(messages,docker,basket,catalog,payment,paymentfailf=1)
            orderstatus = conn.select_query(currentstatus)

            # send to order.api a message with routing key paymentfail
            payment.payment_fail()
            # a time out variable
            timeout = 0

            # a while loop that wait until the order status will change from status 3(stockconfirmerd) or 10 sec has pass
            while timeout<=10:
                ## a sql query that check the current status of the last order that has made every sec
                orderstatus = conn.select_query(currentstatus)
                #if the status order has been changed brake the while loop
                if orderstatus[0]['OrderStatusId']!=stockconfirmerd:
                    break
                sleep(1)
                #a 1 sec to our time out variable
                timeout+=1

                mq.purge(rabbit_queues[4])
    # check that the new status of the new order is 6(cancelled)
    assert orderstatus[0]['OrderStatusId'] == cancelled



@pytest.mark.test_cancel_order_status_1
def test_cancel_order_status_1(order_api,messages,basket):
    '''
    writer: shlomo mhadker
    date:14.3.2023
    test number 4: cancel an order that with current status  submitted
    '''
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
                basket.submmit()
                sleep(3)
                # a sql query that take the current  order status
                orderstatus = conn.select_query(currentstatus)
                #check that the order status is in status 1(submitted)
                assert orderstatus[0]['OrderStatusId'] == submitted
                # a sql query that get the id of the new order that was added
                orderid = conn.select_query(f'{orderidbystatus}{submitted}')
                orderid = orderid[0]['']
                #send to ordering.api a cancel request to the new order
                order_api.cancel_order(orderid)
                ## purge the basket queue from messages
                mq.purge(rabbit_queues[1])
                # purge the ordering.signalrhub queue from messages
                mq.purge(rabbit_queues[4])
                # a sql query that take the current  order status
                newstatus=conn.select_query(f'{orderstatusbyid}{orderid}')

        # check that the new status of the new order is 6(cancelled)
        assert newstatus[0]['OrderStatusId'] == cancelled



@pytest.mark.test_cancel_order_status_2
def test_cancel_order_status_2(order_api,messages,basket,catalog,payment,docker,update=0):
    '''
    writer: shlomo mhadker
    date:14.3.2023
    test number 5: cancel an order that her current status is awaitingvalidation (using test 2)
    '''

    # activate test_MSS with stockfail flag that stop test_MSS when the order status is 2(awaitingvalidation)
    orderstatus = test_MSS(messages,docker,basket,catalog,payment,stockfail=1)
    #sleep(10)
    # check that the order status is in status 2(awaitingvalidation)
    assert orderstatus== awaitingvalidation

    with RabbitMQ() as mq:
        with MSSQLConnector() as conn:
            # a sql query that get the id of the new order that was added
            orderid = conn.select_query(f'{orderidbystatus}{awaitingvalidation}')
            orderid = orderid[0]['']
            # send to ordering.api a cancel request to the new order
            order_api.cancel_order(orderid)
            # a sql query that take the current  order status
            newstatus=conn.select_query(f'{orderstatusbyid} {orderid}')
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])
            # purge the catalog queue from messages
            mq.purge(rabbit_queues[2])

    # check that the new status of the new order is 6(cancelled)
    assert newstatus[0]['OrderStatusId'] == cancelled



@pytest.mark.test_cancel_order_status_3
def test_cancel_order_status_3(order_api,messages,docker,basket,catalog,payment,update=0):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 6: cancel an order that her current status is stock confirmerd (using tes 3)
     '''
    # activate test_MSS with paymentfailf flag that stop test_MSS when the order status is 3(stockconfirmerd)
    orderstatus=test_MSS(messages,docker,basket,catalog,payment,paymentfailf=1)
    assert orderstatus == stockconfirmerd

    with RabbitMQ() as mq:
        with MSSQLConnector() as conn:
            # a sql query that get the id of the new order that was added
            orderid = conn.select_query(f'{orderidbystatus}{stockconfirmerd}')
            orderid = orderid[0]['']
            # send to ordering.api a cancel request to the new order using order id
            order_api.cancel_order(orderid)
            # a sql query that take the current  order status
            newstatus=conn.select_query(f'{orderstatusbyid} {orderid}')
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])
            # purge the payment queue from messages
            mq.purge(rabbit_queues[3])

    #check that the new status of the new order is 6(cancelled)
    assert newstatus[0]['OrderStatusId'] == cancelled



@pytest.mark.test_cancel_order_status_4_fail
def test_cancel_order_status_4_fail(order_api,messages,basket,catalog,payment,docker):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 7:try to cancel an order that her current status is paid (using test 1)
     '''

    with MSSQLConnector() as conn:
        #run full test_MSS to create a new order with status 4
        test_MSS(messages,docker,basket,catalog,payment)
        # a sql query that get the id of the new order that was added
        orderid = conn.select_query(f'{orderidbystatus} {paid}')
        orderid = orderid[0]['']
        # send to ordering.api a cancel request to the new order using order id
        order_api.cancel_order(orderid)
        # a sql query that take the current  order status
        newstatus=conn.select_query(f'{orderstatusbyid}{orderid}')

    # check that the  status of the new order is 4(paid)
    assert newstatus[0]['OrderStatusId'] == paid


@pytest.mark.test_update_order_to_shiped
def test_update_order_to_shiped(order_api,messages,docker,basket,catalog,payment):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 8:create order and then update the order status from paid to shipped
     '''
    # run full test_MSS to create a new order with status 4
    test_MSS(messages,docker,basket,catalog,payment)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the id of the new order that was added
            orderid=conn.select_query(f'{orderidbystatus} {paid}')
            orderid=orderid[0]['']
            # send to ordering.api an update request to the new order using order id
            order_api.update_to_shiped(orderid)
            # a sql query that take the current  order status
            newstatus=conn.select_query(f'{orderstatusbyid} {orderid}')
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])

        # check that the new status of the new order is 5(shipped)
        assert newstatus[0]['OrderStatusId']==shipped


@pytest.mark.test_cancel_order_status_5_fail
def test_cancel_order_status_5_fail(order_api,messages,docker,basket,catalog,payment):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 9:try to cancel an order that her current status is shipped (using test 8)
     '''

    with MSSQLConnector() as conn:
        # run full test_update_order_to_shiped to create a new order with status 5(shipped)
        test_update_order_to_shiped(order_api,messages,docker,basket,catalog,payment)
        # a sql query that get the id of the new order that has created
        orderid = conn.select_query(f'{orderidbystatus} {shipped}')
        orderid = orderid[0]['']
        # send to ordering.api a cancel request to the new order using order i
        order_api.cancel_order(orderid)
        # a sql query that take the current  order status
        newstatus=conn.select_query(f'{orderstatusbyid} {orderid}')

    # check that the status of the new order is 5(shipped)
    assert newstatus[0]['OrderStatusId'] == shipped




@pytest.mark.test_update_order_to_shiped_fail_status_1
def test_update_order_to_shiped_fail_status_1(order_api,messages,basket):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 10:create order and then try to update the order status from submitted to shipped
     '''

    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            ordersnum = conn.select_query(totalorderscount)
            # create a new order
            basket.submmit()
            sleep(5)
            # a sql query that take the current  order status
            orderstatus = conn.select_query(currentstatus)
            # check that the order status is in status 1(submitted)
            assert orderstatus[0]['OrderStatusId'] == submitted
            # a sql query that get the id of the new order that was added
            orderid = conn.select_query(f'{orderidbystatus}{submitted}')
            orderid = orderid[0]['']
            # send to ordering.api an update request to the new order using order id
            order_api.update_to_shiped(orderid)
            # a sql query that take the current  order status
            newstatus = conn.select_query(f'{orderstatusbyid} {orderid}')
            # check that the status of the new order has remains 1(submitted)
            assert newstatus[0]['OrderStatusId'] == submitted
            sleep(int(os.getenv('TEST10PURGE')))
            mq.purge(rabbit_queues[1])
            mq.purge(rabbit_queues[2])
            mq.purge(rabbit_queues[4])


@pytest.mark.test_update_order_to_shiped_fail_status_2
def test_update_order_to_shiped_fail_status_2(messages,order_api,docker,basket,catalog,payment):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 11: create order and then try to update the order status from awaitingvalidation to shipped
     (using test No.5)
     '''
    with RabbitMQ() as mq:
        with MSSQLConnector() as conn:

            # activate test_MSS with stockfail flag that stop test_MSS when the order status is 2(awaitingvalidation)
            orderstatus = test_MSS(messages,docker,basket,catalog,payment, stockfail=1)
            # check that the order status is in status 2(awaitingvalidation)
            assert orderstatus == awaitingvalidation
            # a sql query that get the id of the new order that was added
            orderid = conn.select_query(f'{orderidbystatus} {orderstatus}')
            orderid = orderid[0]['']
            # send to ordering.api an update request to the new order using order id
            order_api.update_to_shiped(orderid)
            # a sql query that take the current  order status
            newstatus = conn.select_query(f'{orderstatusbyid} {orderid}')
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])
        # check that the status of the new order has remains 2(awaitingvalidation)
        assert newstatus[0]['OrderStatusId'] == awaitingvalidation
        #assert respones==400



@pytest.mark.test_update_order_to_shiped_fail_status_3
def test_update_order_to_shiped_fail_status_3(order_api,messages,docker,basket,catalog,payment):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 12: create order and then try to update the order status from stockconfirmerd to shipped
     (using test No.6)
     '''

    # activate test_MSS with paymentfailf flag that stop test_MSS when the order status is 3(stockconfirmerd)
    orderstatus = test_MSS(messages,docker,basket,catalog,payment, paymentfailf=1)
    #check that the new order status is 3(stockconfirmerd)
    assert orderstatus == stockconfirmerd

    with RabbitMQ() as mq:
        with MSSQLConnector() as conn:
            # a sql query that get the id of the new order that was added
            orderid = conn.select_query(f'{orderidbystatus}{orderstatus}')
            orderid = orderid[0]['']

            # send to ordering.api an update request to the new order using order id
            respone=order_api.update_to_shiped(orderid)

            # a sql query that take the current  order status
            newstatus = conn.select_query(f'{orderstatusbyid}{orderid}')

            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])
            # purge the payment queue from messages
            mq.purge(rabbit_queues[3])

            # check that the status of the new order has remains 3(stockconfirmerd)
            assert newstatus[0]['OrderStatusId'] == stockconfirmerd
            # check that the respone status code is 400(Bad Request)
            assert respone==400


@pytest.mark.test_update_order_to_shiped_fail_status_6
def test_update_order_to_shiped_fail_status_6(order_api,messages,basket):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 13: create order and then try to update the order status from cancelled to shipped
     (using test No.4)
     '''
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # activate test_cancel_order_status_1 to create a new order that her final status will be 6(cancelled)
            test_cancel_order_status_1(order_api,messages,basket)

            # a sql query that get the id of the new order that was added
            orderid = conn.select_query(f'{orderidbystatus}{cancelled}')
            orderid = orderid[0]['']

            timeout = 0
            while True and timeout<=5:
                ## a sql query that check the current status of the last order that has made every sec
                orderstatus = conn.select_query(currentstatus)
                #if the status order has been changed brake the while loop
                if orderstatus[0]['OrderStatusId']==cancelled:
                    break
                sleep(1)
                timeout+=1


            # send to ordering.api an update request to the new order using order id
            order_api.update_to_shiped(orderid)

            # purge the catalog queue from messages
            mq.purge(rabbit_queues[2])
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])

        # check that the status of the new order has remains 6(cancelled)
        assert orderstatus[0]['OrderStatusId'] == cancelled



@pytest.mark.test_order_fail_with_card_type_4
def test_order_fail_with_card_type_4(messages,basket):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 14: try to create an order with wrong card type
     '''

    #set credit card type to number not set in the DB
    cardtype=4
    # create a message with the wrong card type
    body = messages.usercheckout(cardtype)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the count of orders that been made
            startcount = conn.select_query(totalorderscount)
            # create a new order
            mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
            # a sql query that get the count of orders after the new order create request
            endingcount= conn.select_query(totalorderscount)
        #check that no new order created
        assert startcount==endingcount


@pytest.mark.test_order_fail_with_card_type_0
def test_order_fail_with_card_type_0(messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 15: try to create an order with wrong card type
     '''
    # set credit card type to number not set in the DB

    cardtype=0
    # create a message with the wrong card type
    body = messages.usercheckout(cardtype)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the count of orders that been made
            startcount = conn.select_query(totalorderscount)
            # create a new order
            mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
            # a sql query that get the count of orders after the new order create request
            endingcount= conn.select_query(totalorderscount)
        # check that no new order created
        assert startcount==endingcount

@pytest.mark.test_order_fail_with_card_type_negative
def test_order_fail_with_card_type_negative(messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 16: try to create an order with negtive card type
     '''

    # set credit card type to number not set in the DB
    cardtype=-1
    # create a message with the wrong card type
    body = messages.usercheckout(cardtype)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the count of orders that been made
            startcount = conn.select_query(totalorderscount)
            # create a new order
            mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
            # a sql query that get the count of orders after the new order create request
            endingcount= conn.select_query(totalorderscount)
        # check that no new order created
        assert startcount==endingcount



@pytest.mark.test_create_order_with_wrong_security_number
def test_create_order_with_wrong_security_number(messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 17: try to create an order with wrong security number
     '''

    # set wrong credit card security number
    cardsecuritynumber = '1234'
    # create a message with the wrong security number
    body = messages.usercheckout(cardsecuritynumber=cardsecuritynumber)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the count of orders that been made
            startcount = conn.select_query(totalorderscount)
            # create a new order
            mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
            # a sql query that get the count of orders after the new order create request
            endingcount = conn.select_query(totalorderscount)
        # check that no new order created
        assert startcount == endingcount



@pytest.mark.test_create_order_with_wrong_credit_card_number
def test_create_order_with_wrong_credit_card_number(messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 18: try to create an order with wrong credit card number
     '''
    # set wrong credit card  number high count of numbers
    cardnumber='4012888888881881145'
    # create a message with the wrong security number
    body = messages.usercheckout(cardnumber=cardnumber)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the count of orders that been made
            startcount = conn.select_query(totalorderscount)
            # a sql query that get the count of orders after the new order create request
            mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
            sleep(int(os.getenv('TEST10PURGE')))
            # a sql query that get the count of orders after the new order create request
            endingcount = conn.select_query(totalorderscount)
            # purge the basket queue from messages
            mq.purge(rabbit_queues[1])
            # purge the catalog queue from messages
            mq.purge(rabbit_queues[2])
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])

        # check that no new order created
        assert startcount[0][''] == endingcount[0]['']

@pytest.mark.test_create_order_with_wrong_credit_card_number_low
def test_create_order_with_wrong_credit_card_number_low(messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 19: try to create an order with low number amount in credit card number
     '''

    # set wrong credit card  number low count of numbers
    cardnumber='123456789012'
    # create a message with the wrong security number
    body = messages.usercheckout(cardnumber=cardnumber)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the count of orders that been made
            startcount = conn.select_query(totalorderscount)
            # a sql query that get the count of orders after the new order create request
            mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
            sleep(int(os.getenv('TEST10PURGE')))
            # a sql query that get the count of orders after the new order create request
            endingcount = conn.select_query(totalorderscount)
            # purge the basket queue from messages
            mq.purge(rabbit_queues[1])
            # purge the catalog queue from messages
            mq.purge(rabbit_queues[2])
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])

        # check that no new order created
        assert startcount[0][''] == endingcount[0]['']


@pytest.mark.test_create_order_with_wrong_characters_credit_card_number
def test_create_order_with_wrong_characters_credit_card_number(messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 20: try to create an order with characters insted of numbers in credit card number
     '''
    # set a letters insted of numbers
    cardnumber='fkjdhsgks'
    # create a message with the wrong security number
    body = messages.usercheckout(cardnumber=cardnumber)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the count of orders that been made
            startcount = conn.select_query(totalorderscount)
            # a sql query that get the count of orders after the new order create request
            mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
            sleep(int(os.getenv('WAIT5')))
            # a sql query that get the count of orders after the new order create request
            endingcount = conn.select_query(totalorderscount)
            # purge the basket queue from messages
            mq.purge(rabbit_queues[1])
            # purge the catalog queue from messages
            mq.purge(rabbit_queues[2])
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])

        # check that no new order created
        assert startcount[0][''] == endingcount[0]['']


@pytest.mark.test_create_order_with_wrong_expiration_date_year
def test_create_order_with_wrong_expiration_date_year(messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 21: try to create an order with invalid year in card expiration date
     '''

    # set expiration date year to wrong year
    year='2015'
    # create a message with the wrong year
    body = messages.usercheckout(year=year)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the count of orders that been made
            startcount = conn.select_query(totalorderscount)
            # a sql query that get the count of orders after the new order create request
            mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
            sleep(int(os.getenv('WAIT5')))
            # a sql query that get the count of orders after the new order create request
            endingcount = conn.select_query(totalorderscount)
            # purge the basket queue from messages
            mq.purge(rabbit_queues[1])
            # purge the catalog queue from messages
            mq.purge(rabbit_queues[2])
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])

        # check that no new order created
        assert startcount[0][''] == endingcount[0]['']


@pytest.mark.test_create_order_with_wrong_expiration_date_month
def test_create_order_with_wrong_expiration_date_month(messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 22: try to create an order with invalid month in card expiration date
     '''

    # set expiration date moth to wrong moth
    month='13'
    # create a message with the wrong month
    body = messages.usercheckout(month=month)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the count of orders that been made
            startcount = conn.select_query(totalorderscount)
            # a sql query that get the count of orders after the new order create request
            mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
            sleep(int(os.getenv('WAIT5')))
            # a sql query that get the count of orders after the new order create request
            endingcount = conn.select_query(totalorderscount)
            # purge the basket queue from messages
            mq.purge(rabbit_queues[1])
            # purge the catalog queue from messages
            mq.purge(rabbit_queues[2])
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])

        # check that no new order created
        assert startcount[0][''] == endingcount[0]['']

@pytest.mark.test_create_order_with_wrong_expiration_date_day
def test_create_order_with_wrong_expiration_date_day(messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 23: try to create an order with invalid day in card expiration date
     '''

    # set expiration date day to wrong day
    day='35'
    # create a message with the wrong day
    body = messages.usercheckout(day=day)
    with MSSQLConnector() as conn:
        with RabbitMQ() as mq:
            # a sql query that get the count of orders that been made
            startcount = conn.select_query(totalorderscount)
            # a sql query that get the count of orders after the new order create request
            mq.publish(exchange=exchange, routing_key=usercheckout,body=json.dumps(body))
            sleep(int(os.getenv('WAIT5')))
            # a sql query that get the count of orders after the new order create request
            endingcount = conn.select_query(totalorderscount)
            # purge the basket queue from messages
            mq.purge(rabbit_queues[1])
            # purge the catalog queue from messages
            mq.purge(rabbit_queues[2])
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])

        # check that no new order created
        assert startcount[0][''] == endingcount[0]['']


@pytest.mark.test_get_user_order_by_id
def test_get_user_order_by_id(order_api,messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 24: getting order details using the order id
     '''

    #set the order id we want to get detail
    orderid=68
    #set a get request with the order id
    respone=order_api.get_order_by_id(68)
    #check that the respone status code is 200
    assert respone.status_code==int(os.getenv('SUCCESS'))


@pytest.mark.test_get_user_orders
def test_get_user_orders(order_api):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 25: getting all orders details that a user has made
     '''

    #authenticate as bob
    order_api=OrderingAPI('bob','Pass123%24')
    #get bob orders list from ordering.api
    orders=order_api.get_orders()

    #in for loop check every order
    for id in orders.json():
        #get the order number
        orderid=id['ordernumber']
        with MSSQLConnector() as conn:
            # a sql query that get buyer id using the order id
            buyerid=conn.select_query(f'SELECT BuyerId from ordering.orders where id = {orderid}')[0]['BuyerId']
            # a sql query that get buyer name using the buyer id
            name=conn.select_query(f'SELECT Name from ordering.buyers where Id={buyerid}')
            #check that the buyer name is the same name that authenticated
            assert order_api.username==name[0]['Name']

    # check that the respone status code is 200
    assert orders.status_code==int(os.getenv('SUCCESS'))

    #assert orders==2

def test_get_user_order_by_id_of_diffrent_user(order_api,messages):
    '''
     writer: shlomo mhadker
     date:14.3.2023
     test number 26: try to get a different user order details
     '''
    #enter a diffrent user order id
    orderid=42
    #check that the respone status code is 401(Unauthorized)
    assert order_api.get_order_by_id(orderid).status_code==int(os.getenv('UNAUTHOTIZED'))


@pytest.mark.test_update_order_to_shiped
def test_update_order_to_shiped_to_diffrent_user(order_api,messages):
   '''
     writer: shlomo mhadker
     date:14.3.2023
    test number 27: try to update a different user order status
   '''

   with RabbitMQ() as mq:
        with MSSQLConnector() as conn:
            #orderid=conn.select_query('SELECT MAX(Id) from ordering.orders where orders.OrderStatusId = 4')
            # a sql query that get a different user order id that order status is paid
            orderid=conn.select_query(f'{orderidbystatus}{paid} and Id != 11')
            orderid=orderid[0]['']
            #try to update order status
            order_api.update_to_shiped(orderid)
            sleep(int(os.getenv('WAIT5')))
            # a sql query that take the order status
            newstatus=conn.select_query(f'{orderstatusbyid} {orderid}')
            # purge the ordering.signalrhub queue from messages
            mq.purge(rabbit_queues[4])
        #check that the order status remains paid
        assert newstatus[0]['OrderStatusId']==paid

@pytest.mark.test_cancel_order_to_diffrent_user
def test_cancel_order_to_diffrent_user(order_api, messages):
   '''
     writer: shlomo mhadker
     date:14.3.2023
    test number 28: try to cancel a different user order
   '''

   with RabbitMQ() as mq:
       with MSSQLConnector() as conn:
           orderid = conn.select_query('SELECT MAX(Id) from ordering.orders where orders.OrderStatusId in(1,2,3) and Id != 11')
           orderid = orderid[0]['']
           # try to cancel the order order
           order_api.cancel_order(orderid)
           sleep(int(os.getenv('WAIT5')))
           # a sql query that take the order status
           newstatus = conn.select_query(f'{orderstatusbyid} {orderid}')
           # purge the ordering.signalrhub queue from messages
           mq.purge(rabbit_queues[4])
           mq.purge(rabbit_queues[1])
           mq.purge(rabbit_queues[2])
       # check that the order status remains submitted orawaitingvalidation or stockconfirmerd
       assert newstatus[0]['OrderStatusId'] in (submitted,awaitingvalidation,stockconfirmerd)



@pytest.mark.test_ordering_api_crash_status2
def test_ordering_api_crash_status2(order_api,messages,docker,basket,catalog,payment):
    '''
      writer: shlomo mhadker
      date:14.3.2023
     test number 29: while  order create process is running stop ordering api service in status 2 wait some timme
     and start ordering api service again,we expect that the process will continue from where it stops
     (using test No.1)
    '''
    with MSSQLConnector() as conn:
        orderstartsnum = conn.select_query(totalorderscount)
        global dockerflag
        test_MSS(messages,docker,basket,catalog,payment,crash=2)
        orderendsnum = conn.select_query(totalorderscount)
        assert orderstartsnum[0]['']+1==orderendsnum[0]['']
        status = conn.select_query(f'{currentstatus}')
    assert status[0]['OrderStatusId']==paid



@pytest.mark.test_ordering_api_crash_status3
def test_ordering_api_crash_status3(order_api,messages,docker,basket,catalog,payment):
    '''
      writer: shlomo mhadker
      date:14.3.2023
     test number 30: while  order create process is running stop ordering api service in status 3 wait some timme
     and start ordering api service again,we expect that the process will continue from where it stops
     (using test No.1)
    '''
    with MSSQLConnector() as conn:
        orderstartsnum = conn.select_query(totalorderscount)
        global dockerflag
        test_MSS(messages,docker,basket,catalog,payment,crash=3)
        orderendsnum = conn.select_query(totalorderscount)
        assert orderstartsnum[0]['']+1==orderendsnum[0]['']
        status = conn.select_query(f'{currentstatus}')
    assert status[0]['OrderStatusId']==paid






