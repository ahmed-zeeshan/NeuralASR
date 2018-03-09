import argparse
import os
import sys
import time
from datetime import datetime

import numpy as np
import pandas as pd
import tensorflow as tf

from logger import get_logger
from common import load_model
from config import Config
from dataset import DataSet
from networks.deepspeech import create_model, create_optimizer


logger = get_logger()

def train_model(dataTrain, datavalid, config):
    logger.info('Batch Dimensions: ' + str(dataTrain.get_feature_shape()))
    logger.info('Label Dimensions: ' + str(dataTrain.get_label_shape()))

    tf.set_random_seed(1)
    is_training = tf.placeholder(tf.bool)

    if datavalid:
        X, T, Y, _ = tf.cond(is_training, lambda: dataTrain.get_batch_op(),
                             lambda: datavalid.get_batch_op())
    else:
        X, T, Y, _ = dataTrain.get_batch_op()

    model, loss, mean_ler, log_prob = create_model(
        X, Y, T, dataTrain.symbols.counter, is_training)

    optimizer = create_optimizer(loss, config.learningrate)

    init = tf.global_variables_initializer()
    saver = tf.train.Saver()
    sess = tf.Session()
    sess.run(init)

    global_step = 0
    load_model(global_step, sess, saver, config.model_dir)
    config.write(os.path.join(config.model_dir, os.path.basename(config.configfile)))
    dataTrain.symbols.write(os.path.join(
        config.model_dir, os.path.basename(config.sym_file)))

    metrics = {'train_time_sec': 0, 'avg_loss': 0, 'avg_ler': 0}
    report_step = config.report_step #dataTrain.get_num_of_sample() // dataTrain.batch_size
    while True:
        global_step += 1
        try:
            t0 = time.time()
            _, loss_val, mean_ler_value = sess.run(
                [optimizer, loss, mean_ler], feed_dict={is_training: True})
            metrics['train_time_sec'] = metrics['train_time_sec'] + \
                (time.time() - t0)
            metrics['avg_loss'] += loss_val
            metrics['avg_ler'] += mean_ler_value
        except tf.errors.OutOfRangeError:
            logger.info("Done Training...")
            break

        if global_step % report_step == 0:
            saver.save(sess, os.path.join(config.model_dir, 'model'),
                       global_step=global_step)
            logger.info('Step: %04d' % (global_step) + ', cost = %.4f' %
                  (metrics['avg_loss'] / report_step) + ', ler = %.4f' % (metrics['avg_ler'] / report_step))
            metrics['avg_loss'] = 0
            metrics['avg_ler'] = 0
            if datavalid:
                valid_loss_val,  valid_mean_ler_value = sess.run(
                    [loss, mean_ler], feed_dict={is_training: False})
                logger.info('Valid: cost = %.4f' % (valid_loss_val) +
                      ', ler = %.4f' % (valid_mean_ler_value))

    logger.info("Finished training!!!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Train speech recognizer on featurized mfcc files.")
    parser.add_argument("-c", "--config", required=True,
                        help="Configuration file.")
    args = parser.parse_args()

    config = Config(args.config)
    dataTrain = DataSet(config.train_input, config.sym_file, config.feature_size,
                        batch_size=config.batch_size, epochs=config.epochs)
    dataValid = None
    if config.test_input:
        dataValid = DataSet(config.test_input, config.sym_file, config.feature_size,
                            batch_size=1, epochs=None)

    train_model(dataTrain, dataValid, config)
