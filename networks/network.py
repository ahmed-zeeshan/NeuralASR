from abc import ABC, abstractmethod
from logger import get_logger

class Network:
    def __init__(self):
        self.logger = get_logger()

    @abstractmethod
    def create_loss(self, logits, labels, seq_len):
        pass

    @abstractmethod
    def create_model(self, logits, seq_len):
        pass

    @abstractmethod
    def create_metric(self, model, labels):
        pass

    @abstractmethod
    def create_network(self, features, seq_len, num_classes, is_training):
        pass

    @abstractmethod
    def setup_training_network(self, X, Y, T, num_classes, num_gpus, learningrate, is_training):
        pass