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
from logging import handlers

# Create a formatter for the log messages
time_formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s')

# Create a rotating file handler for the log file
handler = handlers.RotatingFileHandler(filename='./marketplace.log', maxBytes=3000, backupCount=5)
handler.setFormatter(time_formatter)

# Create a logger object and set the logging level
logger = logging.getLogger()
logger.setLevel(logging.INFO)

# Add the file handler to the logger
logger.addHandler(handler)

# Set the converter to use GMT time
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
            # Create producer_id
            producer_id = str(len(self.producers))
            # Initialize number of products published with 0
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
        # Verify if the producer reached limit of products
        if self.producers[producer_id] == self.queue_size_per_producer:
            logging.info("producer could not publish")
            return False

        # Increment number of products published for the producer
        if producer_id not in self.producers:
            self.producers[producer_id] = 1
        else:
            self.producers[producer_id] = self.producers[producer_id] + 1
        # Add the product to products
        with self.semaphore:
            if product not in self.products:
                self.products[product] = {'quantity': 1, 'available': 1, 'producers': [producer_id]}
            else:
                self.products[product]['quantity'] = self.products[product]['quantity'] + 1
                self.products[product]['available'] = self.products[product]['available'] + 1
                self.products[product]['producers'].append(producer_id)
        logging.info("published done")
        return True

    def new_cart(self):
        """
        Creates a new cart for the consumer

        :returns an int representing the cart_id
        """
        # Generate cart_id
        with self.lock_carts:
            cart_id = len(self.carts)
            # Initialize list for cart
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
        with self.semaphore:
            if product in self.products:
                # If there is still at least one product
                if self.products[product]['available'] >= 1:
                    # Add product to cart
                    self.carts[cart_id].append([product, self.products[product]['producers'][0]])
                    # Decrease by 1 the number of available products of this type
                    self.products[product]['available'] = self.products[product]['available'] - 1
                    # Update the list of producers for this product type
                    self.products[product]['producers'].pop(0)
                    logging.info("product was added to the cart")
                    return True
            logging.info("product could not be added to the cart")
            # If the product has not been produced or is not available return False
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
        with self.semaphore:
            index = -1
            i = 0
            producer_id = 0
            # Search for the list with that type of product
            for elem in self.carts[cart_id]:
                if product == elem[0]:
                    # Save producer
                    producer_id = elem[1]
                    # Save index
                    index = i
                    break
                i = i + 1

            if index != -1:
                # Remove product from cart
                self.carts[cart_id].pop(index)
                # Update available quantity and producers list for that type of product
                self.products[product]['available'] = self.products[product]['available'] + 1
                self.products[product]['producers'].append(producer_id)
        logging.info("product was removed from the cart")

    def place_order(self, cart_id):
        """
        Return a list with all the products in the cart.

        :type cart_id: Int
        :param cart_id: id cart
        """
        logging.info("order from cart %d is being placed", cart_id)
        # If cart is empty return empty list
        if len(self.carts[cart_id]) == 0:
            return []
        # Iterate through products in cart
        for elem in self.carts[cart_id]:
            product = elem[0]
            with self.semaphore:
                # Decrease with 1 total quantity for this type of product
                self.products[product]['quantity'] = self.products[product]['quantity'] - 1
                producer_id = elem[1]
                # Decrease number of products the producer published
                self.producers[producer_id] = self.producers[producer_id] - 1
        logging.info("ordered placed successfully")
        # Return cart
        return self.carts[cart_id]

    def get_lock_consumer(self):
        """
        Return consumer lock
        """
        return self.consumer


class TestMarketplace(unittest.TestCase):
    """
    Unittest for marketplace
    """
    def setUp(self):
        """
        Set up function
        """
        self.marketplace = Marketplace(10)

    def test_register_producer(self):
        """
        Test register_producer() function
        """
        for producer_id in range(10):
            self.assertEqual(self.marketplace.register_producer(), str(producer_id),
                             'test_register_producer: producer_id incorrect')

    def test_publish(self):
        """
        Test publish() function
        """
        products = ['tea', 'chocolate', 'strawberry', 'milk']
        for producer_id in range(3):
            self.assertEqual(self.marketplace.register_producer(), str(producer_id))

        for producer_id in range(3):
            for _ in range(10):
                self.assertEqual(self.marketplace.publish(str(producer_id), products[producer_id]),
                                 True,
                                 'test_publish incorrect: product should have been added')
            self.assertEqual(self.marketplace.publish(str(producer_id), products[producer_id]),
                             False,
                             'test_publish incorrect: product should NOT have been added')

    def test_new_cart(self):
        """
        Test new_cart() function
        """
        for cart_id in range(10):
            self.assertEqual(self.marketplace.new_cart(), cart_id,
                             'test_new_cart: cart_id incorrect')

    def test_add_to_cart(self):
        """
        Test add_to_cart(cart_id, product) function
        """
        products = ['tea', 'chocolate', 'strawberry', 'milk']
        for producer_id in range(3):
            self.assertEqual(self.marketplace.register_producer(), str(producer_id))

        for producer_id in range(3):
            for _ in range(5):
                self.assertEqual(self.marketplace.publish(str(producer_id),
                                                          products[producer_id]), True)

        self.assertEqual(self.marketplace.publish(str(0), products[3]), True)
        for cart_id in range(2):
            self.assertEqual(self.marketplace.new_cart(), cart_id)

        self.assertEqual(self.marketplace.add_to_cart(0, 'milk'), True,
                         'test_add_to_cart: product should have been added to cart')
        self.assertEqual(self.marketplace.add_to_cart(1, 'milk'), False,
                         'test_add_to_cart: product should NOT have been added to cart')

        for _ in range(3):
            self.assertEqual(self.marketplace.add_to_cart(0, products[0]), True,
                             'test_add_to_cart: product should have been added to cart')
        for _ in range(2):
            self.assertEqual(self.marketplace.add_to_cart(1, products[0]), True,
                             'test_add_to_cart: product should have been added to cart')
        self.assertEqual(self.marketplace.add_to_cart(1, products[0]), False,
                         'test_add_to_cart: product should NOT have been added to cart')

    def test_remove_from_cart(self):
        """
        Test remove_from_cart(cart_id, product) function
        """
        products = ['tea', 'chocolate', 'strawberry', 'milk']
        for producer_id in range(3):
            self.assertEqual(self.marketplace.register_producer(), str(producer_id))

        for producer_id in range(3):
            for _ in range(5):
                self.assertEqual(self.marketplace.publish(str(producer_id),
                                                          products[producer_id]), True)

        self.assertEqual(self.marketplace.publish(str(0), products[3]), True)
        for cart_id in range(2):
            self.assertEqual(self.marketplace.new_cart(), cart_id)

        for _ in range(3):
            self.assertEqual(self.marketplace.add_to_cart(0, products[0]), True)
        for _ in range(5):
            self.assertEqual(self.marketplace.add_to_cart(1, products[1]), True)
            self.assertEqual(self.marketplace.add_to_cart(1, products[2]), True)

        self.marketplace.remove_from_cart(1, products[1])
        self.assertEqual(self.marketplace.add_to_cart(0, products[1]), True,
                         'test_remove_from_cart: product should have been available')

    def test_place_order(self):
        """
        Test place_ordrer() function
        """
        products = ['tea', 'chocolate', 'strawberry', 'milk']
        for producer_id in range(3):
            self.assertEqual(self.marketplace.register_producer(), str(producer_id))

        for producer_id in range(3):
            for _ in range(5):
                self.assertEqual(self.marketplace.publish(str(producer_id),
                                                          products[producer_id]), True)

        self.assertEqual(self.marketplace.publish(str(0), products[3]), True)
        for cart_id in range(2):
            self.assertEqual(self.marketplace.new_cart(), cart_id)

        for _ in range(3):
            # cart 0: 'tea' * 3
            self.assertEqual(self.marketplace.add_to_cart(0, products[0]), True)
        for _ in range(5):
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
