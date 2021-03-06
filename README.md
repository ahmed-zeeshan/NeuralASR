[Description is obselete need to update.]
# NeuralASR: A nerual network based configurable End-to-End speech recognition engine

This speech recognition engine has been created for quickly benchmarking different deep neural architectures. There are bunch of speech recognition systems available on the web that are based on tensorflow or other deep learning platforms. However, `TFSpeechRecEngine` is highly configurable in a sense that audio features, network definition, training and evaluation parameters can be defined at run-time. `TFSpeechRecEngine` supports training in parallel using multiple GPUs. The user can bring in any tensorflow implementations such as [DeepSpeech](https://github.com/mozilla/DeepSpeech), [WaveNet](https://github.com/buriburisuri/speech-to-text-wavenet)
 etc. to benchmark against their own implementation.

## Configuration
Most of the system configurations are defined in a .config file which is a text file that comply with [python configparser](https://docs.python.org/2/library/configparser.html) standards. Some of the sample configuration files can be found in ./config folder. Here is how a sample configuration look like.

```
[Parameters]
#### Audio sample rate
samplerate=16000

#### Number of MFCC to compute
numcep=26

#### Number of MFCCs to take into account in context. The feature vector size will be "(2 * numcontext + 1) * numcep"
numcontext=10

#### randomly shift feature vector to avoid over-fitting
#rand_shift=2

#### Batch size for training neural network
batch_size=16

#### Number of iterations over complete training data.
epochs=1

#### Learning rate of for optimizer
learningrate=0.0001

#### Path where trained models are saved.
model_dir=.model

#### if greater than zero model will be loaded from mode_dir
start_step=0

#### status will be  printed after 'report_step'
report_step=100

#### Number of GPUs to use
num_gpus=2

#### Remove punctuations from the labels
punc_regex=[^a-z0-9 ]

#### File where Output symbols are stored e.g. [a,b,c...] with their numeric ids
sym_file=${MFCC Featurizer:output}/symbols

#### Network to use for the ASR
network=bilstm_ctc_net

[Train]
#### File containing list of .pkl file generated from preprocess_mfcc.py
input=${MFCC Featurizer:output}/train.scp

[Test]
#### File containing list of .pkl file generated from preprocess_mfcc.py
input=${MFCC Featurizer:output}/test.scp

[MFCC Featurizer]
#### CSV File containing audio file path, transcription, audio size in each row
input=sample_train.scp

#### Directory to save .pkl file
output=sample_featurized
```

## Preprocessing
Conversion of speech wave form into MFCCs or other features takes a bit of time. To speech up the training, `TFSpeechRecEngine` provides an option to pre-featurized the audio data so that training process can be sped up. The featurized MFCCs together with other meta-data are stored in a python [pickle](https://pythontips.com/2013/08/02/what-is-pickle-in-python/) file. During training, data is read from these pickle file. Following is a simple command to generate featurized files from a list of audio files

```
$ python preprocess_mfcc.py config
```

This command also cleans the transcription text based on the regular expression defined in the config file e.g. `unc_regex=[^a-z0-9 ]` in above configuration. In addition to generating the .pkl file for each training example, the script also partitions data into training and test sets and places the list of train and test files in the `output` directory. The files are named according to `input` parameters in `[Train]` and `[Test]` sections of configuration file.

## Network Definition
Networks are defined in a tensorflow python code file. Some example networks are available in networks directory in this repository. For example, following is a naive example of LSTM based network from networks/lstm_ctc_net.py file.

```python
import tensorflow as tf

from .common import (label_error_rate, loss, model, setup_training_network,
                     variable_on_worker_level)


def create_network(features, seq_len, num_classes):

    num_hidden = 500
    num_layers = 3

    cells = [tf.contrib.rnn.LSTMCell(num_hidden, state_is_tuple=True)
             for i in range(num_layers)]
    stack = tf.contrib.rnn.MultiRNNCell(cells,
                                        state_is_tuple=True)

    outputs, _ = tf.nn.dynamic_rnn(stack, features, seq_len, dtype=tf.float32)

    shape = tf.shape(features)
    batch_s, max_time_steps = shape[0], shape[1]

    outputs = tf.reshape(outputs, [-1, num_hidden])

    W = variable_on_worker_level(
        'W', [num_hidden, num_classes], tf.contrib.layers.xavier_initializer(uniform=False))

    b = variable_on_worker_level('b', [num_classes], tf.constant_initializer(0.))

    # Doing the affine projection
    logits = tf.matmul(outputs, W) + b

    # Reshaping back to the original shape
    logits = tf.reshape(logits, [batch_s, -1, num_classes])

    # Time major
    logits = tf.transpose(logits, (1, 0, 2))
    return logits
```

To use this network for training, please set `network` parameter in config file as follows

```
...
#### Network to use for the ASR
network=lstm_ctc_net
...
```
The `create_network' method defines the networks. This network is automatically parallelize by the system during training. 'ctc_loss', 'decoding' and other generic operations are defined in networks/common.py. User can override these implementations by defining their own implementations in the network file. If you create a new network, place it in the network folder. The training script loads any network defined in the configuration from network directory.

## Training
Once the network is defined, the system can be trained using following command

```
$ python train.py config
```
Training script saves the intermediate model, its parameters and necessary data files into a directory defined by `mode_dir` parameter in config file. The frequency of save operation is defined by the `report_step` parameter in config file.

### Parallel Training on GPUs
Training is automatically done in parallel on GPUs if `num_gpus > 1` in the config file. The system employs data parallel technique. 'N' number of batches are processed in parallel where 'N' is the number of GPUs ('num_gpus') in config. 

## Decoding
The following command can be used to decode evaluation/test data and compute the metrics such as ctc_loss and label error rate etc.

```
$ python decode.py config
```
The test section in the config defines the list of file for evaluation.

## Converting Audio to Text 
A raw audio file can also be converted in to text using following command

```
$ python decode_wav.py config input.wav
```
The `input.wav` will be downsampled based on the settings in the configuration file.

## To-Do

- Add other audio featurization techniques in addition to MFCCs.
- Run the benchmarks and highlight results on this page.
- Make it deep learning platform independent i.e. include Caffe, CNTK, torch etc.
- Add language model decoding.

## Contribution(s)
Contributions are welcome on any area of the system. Please see to-do list above for any idea.
The following is a list of major contributor(s).

- Zeeshan Ahmed (zeeshan.ahmed.za at gmail dot com)
