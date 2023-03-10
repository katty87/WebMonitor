import argparse
import json
import logging
import sys
import time

import yaml
from kafka import KafkaConsumer
from retry import retry

from data_handler.data_saver import init_data_saver


def _run_endless_loop(consumer, data_saver, config):
    sleep_interval = config['kafka_consumer']['sleep_interval']
    while True:
        for msg in consumer:
            data_saver.save_data_item(msg.value)

        time.sleep(sleep_interval)


def run_handler(args, config: dict):
    consumer = init_kafka_consumer(config)
    data_saver = init_data_saver(args.data_saver_type, config)
    try:
        data_saver.init()
        _run_endless_loop(consumer, data_saver, config)
    finally:
        data_saver.finalize()


def get_config(args):
    with open(args.config) as config_f:
        return yaml.full_load(config_f)


@retry(tries=5, delay=1, backoff=2)
def init_kafka_consumer(config: dict) -> KafkaConsumer:
    return KafkaConsumer(config['kafka_consumer']['topic'],
                         value_deserializer=lambda m: json.loads(m),
                         **config['kafka_consumer']['connection']
                         )


def parse_args():
    parser = argparse.ArgumentParser(description='Process some integers.')
    parser.add_argument('-c', '--config', required=True, help='configuration file name')
    parser.add_argument('--data_saver_type', type=str, default='postgre_sql', choices=('postgre_sql'),
                        help='the name of a file with url list')
    return parser.parse_args()


def config_logging(args):
    logging.basicConfig(format='%(asctime)s] %(levelname).1s %(message)s',
                        datefmt='%Y.%m.%d %H:%M:%S', level=logging.INFO)
    logging.info("Data handler started with options: {}".format(args))


def main():
    try:
        args = parse_args()
        config_logging(args)

        run_handler(args, get_config(args))
    except KeyboardInterrupt:
        sys.exit('Data handler stopped.')


if __name__ == "__main__":
    main()
