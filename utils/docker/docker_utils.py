import docker
import time


class DockerManager:
    def __init__(self):
        self.cli = docker.from_env()
        self.containers = self.cli.containers.list()
        self.containers_dict = {c.image.tags[0]: c for c in self.containers}

    def start(self, container_name):
        self.containers_dict[container_name].start()

    def stop(self, container_name):
        self.containers_dict[container_name].stop()

    def restart(self, container_name):
        self.containers_dict[container_name].restart()

    def pause(self, container_name):
        self.containers_dict[container_name].pause()

    def unpause(self, container_name):
        self.containers_dict[container_name].unpause()

    def stop_services(self):
        self.stop('eshop/basket.api:linux-latest')
        self.stop('eshop/catalog.api:linux-latest')
        self.stop('eshop/payment.api:linux-latest')
        self.stop('eshop/ordering.signalrhub:linux-latest')

    def start_services(self):
        #self.start('eshop/basket.api:linux-latest')
        self.start('eshop/catalog.api:linux-latest')
        self.start('eshop/payment.api:linux-latest')
        self.start('eshop/ordering.signalrhub:linux-latest')


if __name__ == '__main__':
    dm = DockerManager()
    # dm.stop('eshop/ordering.api:linux-latest')
    # time.sleep(1)
    # dm.start('eshop/ordering.api:linux-latest')
    #
    # dm.pause('eshop/ordering.api:linux-latest')
    # time.sleep(1)
    # dm.unpause('eshop/ordering.api:linux-latest')
    #
    # dm.restart('eshop/ordering.api:linux-latest')
    dm.stop_services()
    # dm.start('eshop/basket.api:linux-latest')
    # dm.stop('eshop/basket.api:linux-latest')
    # dm.stop('eshop/catalog.api:linux-latest')
    # dm.stop('eshop/payment.api:linux-latest')
    # dm.stop('eshop/ordering.signalrhub:linux-latest')
