from utils.rabbitmq.rabbitmq_send import RabbitMQ

rk=''

routigkey=[]
def callback(ch, method, properties, body):
    global rk
    rk=''
    rk=method.routing_key
    if rk!='':
        ch.stop_consuming()


def returnglob():
    r_key=rk
    return r_key

def consume_message(queue):
    with RabbitMQ() as mq:
        mq.consume(queue,callback)

if __name__ == '__main__':
    #with RabbitMQ() as mq:
        #mq.consume('Ordering', callback)
    with RabbitMQ() as mq:
        respones=mq.consume('Catalog', callback)
        print('23')
        #print(str2)
        #mq.close()
    print(rk)
    #for message in routigkey:
       # print(message)
