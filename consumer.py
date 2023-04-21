"""
This module represents the Consumer.

Computer Systems Architecture Course
Assignment 1
March 2021
"""

from threading import Thread
from time import sleep


class Consumer(Thread):
    """
    Class that represents a consumer.
    """

    def __init__(self, carts, marketplace, retry_wait_time, **kwargs):
        """
        Constructor.

        :type carts: List
        :param carts: a list of add and remove operations

        :type marketplace: Marketplace
        :param marketplace: a reference to the marketplace

        :type retry_wait_time: Time
        :param retry_wait_time: the number of seconds that a producer must wait
        until the Marketplace becomes available

        :type kwargs:
        :param kwargs: other arguments that are passed to the Thread's __init__()
        """
        Thread.__init__(self, **kwargs)
        self.carts = carts
        self.marketplace = marketplace
        self.retry_wait_time = retry_wait_time
        self.kwargs = kwargs
        self.cart_id = self.marketplace.new_cart()

    def run(self):
        # Iterate through carts
        for cart in self.carts:
            # Iterate through commands
            for elem in cart:
                command = elem['type']
                product = elem['product']
                quantity = elem['quantity']
                if command == 'add':
                    while quantity > 0:
                        verify = self.marketplace.add_to_cart(self.cart_id, product)
                        # If the product can not be added sleep and try again
                        if not verify:
                            sleep(self.retry_wait_time)
                        else:
                            # If product was added, decrease quantity
                            quantity = quantity - 1
                if command == 'remove':
                    while quantity > 0:
                        self.marketplace.remove_from_cart(self.cart_id, product)
                        quantity = quantity - 1
            # Save returned list of products
            cart_list = self.marketplace.place_order(self.cart_id)
            # Assign a new cart
            self.cart_id = self.marketplace.new_cart()
            # Print products
            if len(cart_list) > 0:
                for k in cart_list:
                    self.marketplace.lock_consumer()
                    print(self.kwargs['name'], 'bought', k[0])
                    self.marketplace.unlock_consumer()
