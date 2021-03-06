#! /usr/bin/python3

from google.protobuf.timestamp_pb2 import Timestamp
from concurrent import futures
import sys
import time
import logging
import argparse

import grpc
import order_pb2
import order_pb2_grpc

from grpc_interceptor import ServerInterceptor

logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(name)s | %(lineno)d | %(levelname)s | %(message)s')

# A common Logger
logger = logging.getLogger('gRPC_playground')


class ErrorLoggerInterceptor(ServerInterceptor):
    
    def intercept(self, method, request, context, method_name):
        try:
            return method(request, context)
        except Exception as e:
            self.log_error(e)
            raise

    def log_error(self, e: Exception) -> None:
        print("log error")


"""
Order Receiver class
"""

class Greeter(order_pb2_grpc.OrderService):

    def AddOrder(self, order_requests, context):
        
        for order_request in order_requests:
            logger.debug("Order received with {}".format(order_request))
       
        #return order_pb2.OrderReply(result=True)
        #yield order_pb2.OrderReply(result=True)
       
        timestamp = Timestamp()
        timestamp.GetCurrentTime()
        
        yield order_pb2.OrderReply(result=True, responseTime=timestamp)
       

def serve(server_address=None, port=None, use_tsl=None, max_workers=None):

    """
    :brief Serve method for the gRPC server
    :param server_address local host or a remote server
    :param port a SSL port such as 443 ? 
    :param use_tsl whether an encryption is used
    """

    logger.info("gRCP Server is started to serve ...")

    interceptors = [ErrorLoggerInterceptor()]
    server = grpc.server(futures.ThreadPoolExecutor(max_workers=max_workers), interceptors=interceptors)

    order_pb2_grpc.add_OrderServiceServicer_to_server(Greeter(), server)

    # Certificate Authority (CA) certificate handling on server
    
    port = 50051
    #server_host = 'localhost'
    keyfile = 'server.key'
    certfile = 'server.crt'
    private_key = open(keyfile, 'rb').read()
    certificate_chain = open(certfile, 'rb').read()
    credentials = grpc.ssl_server_credentials([(private_key, certificate_chain)])

    if server_address:
        server.add_secure_port(server_address + ':' + str(port), credentials)
    else:
        server.add_secure_port('[::]:' + str(port), credentials)

    logger.info("Start listening {}:{}".format(server_address, port))
    
    #server.add_secure_port('[::]:' + str(port), credentials)
    #server.add_insecure_port('[::]:50051')
    
    server.start()

    server.wait_for_termination()


"""
Main
"""
if __name__ == '__main__':

    p = argparse.ArgumentParser('A python implementation of gRPC server')

    p.add_argument('-w', '--max-workers', dest='max_workers', default=10,
        help='mayimum number of workers for the threadpool used by.')
    p.add_argument('-l', '--localhost', metavar='localhost',
        help='whether the localhost is used for the gRPC connection test.')
    p.add_argument('-s', '--server-address', metavar='server_address', dest='server_address',
        help='server host is used for the gRPC connection test.')
    p.add_argument('-p', '--port', metavar='port', dest='port',
        help='port is used for the gRPC connection test.')    
    p.add_argument('-t', '--use-tsl', metavar='tsl', dest='use_tsl',
        help='whether a remote host uses a TSL gRPC connection.')
    p.add_argument('-v', '--verbose', action='store_true',
        help='Verbose mode for logging')               

    # parse to get the arguments
    args = p.parse_args()

    if args.verbose:
        logger.setLevel(logging.DEBUG)

    logger.info("gRCP Server is started to run ...")
    logger.debug("Arguments {} ".format(args))

    if args.server_address:
         logger.info("Remote host {}".format(args.server_address))

    if args.port:
        logger.info("Port {}".format(args.port))    

    if args.use_tsl:
         logger.info("Use TSL host {}".format(args.use_tsl))

    if args.max_workers:
         logger.info("Used max workers for thread pool {}".format(args.max_workers))

    while True:
        try:

            # take start time timestamp
            start_time = time.perf_counter()

            logger.debug("Serve with server address {}".format(args.server_address))
            serve(args.server_address, args.use_tsl, args.max_workers)

        except KeyboardInterrupt:

            # elapsed time calculation
            print('Elapsed time {:0.4f} in seconds'.format(time.perf_counter() - start_time))
            exit()

        finally:
            print('Finally')
            exit()