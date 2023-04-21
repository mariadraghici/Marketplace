"""
This module represents the Marketplace.

Computer Systems Architecture Course
Assignment 1
March 2021
"""
import time
import unittest
from threading import Lock
import logging
import logging.handlers as handlers

# create a formatter for the log messages
time_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

# create a rotating file handler for the log file
handler = handlers.RotatingFileHandler(filename='./marketplace.log', maxBytes=3000, backupCount=5)
handler.setFormatter(time_formatter)

# create a logger object and set the logging level
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# add the file handler to the logger
logger.addHandler(handler)

# set the converter to use GMT time
logging.Formatter.converter = time.gmtime


class Marketplace:
    """
    Class that represents the Marketplace. It's the central part of the implementation.
    The producers and consumers use its methods concurrently.
    """

    def __init__(self, queue_size_per_producer):
        """
        Constructor

        :type queue_size_per_producer: Int
        :param queue_size_per_producer: the maximum size of a queue associated with each producer
        """
        self.queue_size_per_producer = queue_size_per_producer
        self.producers = {}
        self.products = {}
        self.carts = {}
        self.lock_register = Lock()
        self.lock_carts = Lock()
        self.semaphore = Lock()
        self.consumer = Lock()

    def register_producer(self):
        """
        Returns an id for the producer that calls this.
        """
        with self.lock_register:
            producer_id = str(len(self.producers))
            self.producers[producer_id] = 0
            logging.info("producer %s was registered", producer_id)
            return producer_id

    def publish(self, producer_id, product):
        """
        Adds the product provided by the producer to the marketplace

        :type producer_id: String
        :param producer_id: producer id

        :type product: Product
        :param product: the Product that will be published in the Marketplace

        :returns True or False. If the caller receives False, it should wait and then try again.
        """
        logging.info("producer %s wants to publish product %s", producer_id, str(product))
        if self.producers[producer_id] == self.queue_size_per_producer:
            logging.info("producer could not publish")
            return False

        if producer_id not in self.producers:
            self.producers[producer_id] = 1
        else:
            self.producers[producer_id] = self.producers[producer_id] + 1
        self.semaphore.acquire()
        if product not in self.products:
            self.products[product] = {'quantity': 1, 'available': 1, 'producers': [producer_id]}
            self.semaphore.release()
        else:
            self.products[product]['quantity'] = self.products[product]['quantity'] + 1
            self.products[product]['available'] = self.products[product]['available'] + 1
            self.semaphore.release()
            self.products[product]['producers'].append(producer_id)
        logging.info("published done")
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        with self.lock_carts:
            cart_id = len(self.carts)
            self.carts[cart_id] = []
            logging.info("a new cart with id %d was created", cart_id)
            return cart_id

    def add_to_cart(self, cart_id, product):
        """
        Adds a product to the given cart. The method returns

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to add to cart

        :returns True or False. If the caller receives False, it should wait and then try again
        """
        logging.info("adding product %s to cart %d", str(product), cart_id)
        self.semaphore.acquire()
        if product in self.products:
            if self.products[product]['available'] >= 1:
                self.carts[cart_id].append([product, self.products[product]['producers'][0]])
                self.products[product]['available'] = self.products[product]['available'] - 1
                self.products[product]['producers'].pop(0)
                self.semaphore.release()
                logging.info("product was added to the cart")
                return True
        self.semaphore.release()
        logging.info("product could not be added to the cart")
        return False

    def remove_from_cart(self, cart_id, product):
        """
        Removes a product from cart.

        :type cart_id: Int
        :param cart_id: id cart

        :type product: Product
        :param product: the product to remove from cart
        """
        logging.info("removing product %s from cart %d", str(product), cart_id)
        self.semaphore.acquire()
        index = -1
        producer_id = 0
        for i in range(len(self.carts[cart_id])):
            if product == self.carts[cart_id][i][0]:
                producer_id = self.carts[cart_id][i][1]
                index = i
                break

        if index != -1:
            self.carts[cart_id].pop(index)
            self.products[product]['available'] = self.products[product]['available'] + 1
            self.products[product]['producers'].append(producer_id)
        self.semaphore.release()
        logging.info("product was removed from the cart")

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        logging.info("order from cart %d is being placed", cart_id)
        if len(self.carts[cart_id]) == 0:
            return []
        for i in range(len(self.carts[cart_id])):
            product = self.carts[cart_id][i][0]
            self.semaphore.acquire()
            self.products[product]['quantity'] = self.products[product]['quantity'] - 1
            producer_id = self.carts[cart_id][i][1]
            self.producers[producer_id] = self.producers[producer_id] - 1
            self.semaphore.release()
        logging.info("ordered placed successfully")
        return self.carts[cart_id]

    def lock_consumer(self):
        self.consumer.acquire()

    def unlock_consumer(self):
        self.consumer.release()


class TestMarketplace(unittest.TestCase):
    def setUp(self):
        self.marketplace = Marketplace(10)

    def test_register_producer(self):
        for producer_id in range(10):
            self.assertEqual(self.marketplace.register_producer(), str(producer_id),
                             'test_register_producer: producer_id incorrect')

    def test_publish(self):
        products = ['tea', 'chocolate', 'strawberry', 'milk']
        for producer_id in range(3):
            self.assertEqual(self.marketplace.register_producer(), str(producer_id))

        for producer_id in range(3):
            for i in range(10):
                self.assertEqual(self.marketplace.publish(str(producer_id), products[producer_id]), True,
                                 'test_publish incorrect: product should have been added to marketplace')
            self.assertEqual(self.marketplace.publish(str(producer_id), products[producer_id]), False,
                             'test_publish incorrect: product should NOT have been added to marketplace')

    def test_new_cart(self):
        for cart_id in range(10):
            self.assertEqual(self.marketplace.new_cart(), cart_id, 'test_new_cart: cart_id incorrect')

    def test_add_to_cart(self):
        products = ['tea', 'chocolate', 'strawberry', 'milk']
        for producer_id in range(3):
            self.assertEqual(self.marketplace.register_producer(), str(producer_id))

        for producer_id in range(3):
            for i in range(5):
                self.assertEqual(self.marketplace.publish(str(producer_id), products[producer_id]), True)

        self.assertEqual(self.marketplace.publish(str(0), products[3]), True)
        for cart_id in range(2):
            self.assertEqual(self.marketplace.new_cart(), cart_id)

        self.assertEqual(self.marketplace.add_to_cart(0, 'milk'), True,
                         'test_add_to_cart: product should have been added to cart')
        self.assertEqual(self.marketplace.add_to_cart(1, 'milk'), False,
                         'test_add_to_cart: product should NOT have been added to cart')

        for i in range(3):
            self.assertEqual(self.marketplace.add_to_cart(0, products[0]), True,
                             'test_add_to_cart: product should have been added to cart')
        for i in range(2):
            self.assertEqual(self.marketplace.add_to_cart(1, products[0]), True,
                             'test_add_to_cart: product should have been added to cart')
        self.assertEqual(self.marketplace.add_to_cart(1, products[0]), False,
                         'test_add_to_cart: product should NOT have been added to cart')

    def test_remove_from_cart(self):
        products = ['tea', 'chocolate', 'strawberry', 'milk']
        for producer_id in range(3):
            self.assertEqual(self.marketplace.register_producer(), str(producer_id))

        for producer_id in range(3):
            for i in range(5):
                self.assertEqual(self.marketplace.publish(str(producer_id), products[producer_id]), True)

        self.assertEqual(self.marketplace.publish(str(0), products[3]), True)
        for cart_id in range(2):
            self.assertEqual(self.marketplace.new_cart(), cart_id)

        for i in range(3):
            self.assertEqual(self.marketplace.add_to_cart(0, products[0]), True)
        for i in range(5):
            self.assertEqual(self.marketplace.add_to_cart(1, products[1]), True)
            self.assertEqual(self.marketplace.add_to_cart(1, products[2]), True)

        self.marketplace.remove_from_cart(1, products[1])
        self.assertEqual(self.marketplace.add_to_cart(0, products[1]), True,
                         'test_remove_from_cart: product should have been available')

    def test_place_order(self):
        products = ['tea', 'chocolate', 'strawberry', 'milk']
        for producer_id in range(3):
            self.assertEqual(self.marketplace.register_producer(), str(producer_id))

        for producer_id in range(3):
            for i in range(5):
                self.assertEqual(self.marketplace.publish(str(producer_id), products[producer_id]), True)

        self.assertEqual(self.marketplace.publish(str(0), products[3]), True)
        for cart_id in range(2):
            self.assertEqual(self.marketplace.new_cart(), cart_id)

        for i in range(3):
            # cart 0: 'tea' * 3
            self.assertEqual(self.marketplace.add_to_cart(0, products[0]), True)
        for i in range(5):
            # cart 1: 'chocolate' * 5, 'strawberry' * 5
            self.assertEqual(self.marketplace.add_to_cart(1, products[1]), True)
            self.assertEqual(self.marketplace.add_to_cart(1, products[2]), True)

        self.assertEqual(self.marketplace.add_to_cart(0, products[1]), False)
        self.marketplace.remove_from_cart(1, products[1])
        self.marketplace.remove_from_cart(1, products[1])
        self.marketplace.place_order(1)
        self.assertEqual(self.marketplace.add_to_cart(0, products[1]), True)
        self.assertEqual(self.marketplace.add_to_cart(0, products[1]), True)
        self.assertEqual(self.marketplace.add_to_cart(0, products[2]), False)
        self.assertEqual(self.marketplace.new_cart(), 2)
        self.marketplace.place_order(1)
        self.assertEqual(self.marketplace.add_to_cart(2, products[1]), False)
