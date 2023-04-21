"""
This module represents the Producer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread
from time import sleep


class Producer(Thread):
    """
    Class that represents a producer.
    """

    def __init__(self, products, marketplace, republish_wait_time, **kwargs):
        """
        Constructor.

        @type products: List()
        @param products: a list of products that the producer will produce

        @type marketplace: Marketplace
        @param marketplace: a reference to the marketplace

        @type republish_wait_time: Time
        @param republish_wait_time: the number of seconds that a producer must
        wait until the marketplace becomes available

        @type kwargs:
        @param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.products = products
        self.marketplace = marketplace
        self.republish_wait_time = republish_wait_time
        self.kwargs = kwargs
        self.id = marketplace.register_producer()

    def run(self):
        # print('sunt aici')
        i = 0
        curr_time = 0
        wait_time = self.products[i][2]
        quantity = self.products[i][1]
        while 1:
            # print(curr_time, wait_time, i)
            verify = self.marketplace.publish(self.id, self.products[i][0])
            if not verify:
                # print('ma culc republish')
                sleep(self.republish_wait_time)
                # curr_time = curr_time + self.republish_wait_time
                # print('n am putut adauga')
                # print(curr_time)
            else:
                sleep(wait_time)
                # print("am putut")
                # print('cantitate', quantity)
                # if curr_time < wait_time:
                #     # print('trebuie sa ma culc', wait_time - curr_time)
                #     sleep(wait_time - curr_time)
                wait_time = self.products[i][2]
                # curr_time = 0
                if quantity == 0:
                    i = i + 1
                    if i == len(self.products):
                        i = 0
                    quantity = self.products[i][1]
                else:
                    quantity = quantity - 1

