import os
import sys
import argparse
import time
from datetime import datetime

import numpy as np
import pandas as pd
import tensorflow as tf

from common import load_model
from dataset import DataSet
from decode import decode_batch
from neuralnetworks import create_model
from preprocess import SpeechSample


def train_model(dataTrain, model_dir):
    print('Batch Dimensions: ', dataTrain.get_feature_shape())
    print('Label Dimensions: ', dataTrain.get_label_shape())

    tf.set_random_seed(1)
    X = tf.placeholder(tf.float32, dataTrain.get_feature_shape())
    Y = tf.sparse_placeholder(tf.int32)
    T = tf.placeholder(tf.int32, [None])
    is_training = tf.placeholder(tf.bool)

    model, loss = create_model(dataTrain, X, Y, T, is_training)
    optimizer = tf.train.MomentumOptimizer(
        learning_rate=0.005, momentum=0.9).minimize(loss)

    init = tf.global_variables_initializer()
    saver = tf.train.Saver()
    sess = tf.Session()
    sess.run(init)

    start_epoch=10
    load_model(start_epoch, sess, saver, model_dir)

    train_time_sec = 0
    for epoch in range(start_epoch, dataTrain.epochs):
        avg_loss = 0
        total_batch = 0
        dataTrain.reset()
        while dataTrain.has_more_batches():
            X_batch, Y_batch, seq_len, _ = dataTrain.get_next_batch()
            t0 = time.time()
            _, loss_val = sess.run([optimizer, loss], feed_dict={
                                   X: X_batch, Y: Y_batch, T: seq_len, is_training: True})
            train_time_sec = train_time_sec + (time.time() - t0)
            avg_loss += loss_val
            total_batch += 1

        if total_batch > 0:
            saver.save(sess, os.path.join(model_dir, 'model'), global_step=epoch)
            print('Epoch: ', '%04d' % (epoch + 1), 'cost = %.4f' %
                  (avg_loss / total_batch))
            dataTrain.reset()
            X_batch, Y_batch, seq_len, original = dataTrain.peek_batch()
            feed_dict = {X: X_batch, T: seq_len, is_training: False}
            str_decoded = decode_batch(sess, model, feed_dict)
            print('Decoded: ', str_decoded)
            print('Original: ', original)

    print("Finished training!!!")


if __name__ == '__main__':
    parser = argparse.ArgumentParser(
        description="Read data from featurized mfcc files.")
    parser.add_argument("-i", "--input", required=True,
                        help="List of pickle files containing mfcc")
    parser.add_argument("-m", "--model_dir", required=False, default='.model',
                        help="Directory to save model files.")
    args = parser.parse_args()

    dataTrain = DataSet(args.input, epochs=100)
    train_model(dataTrain, args.model_dir)
