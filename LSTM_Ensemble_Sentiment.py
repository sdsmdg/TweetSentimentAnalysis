# -*- coding: utf-8 -*-
"""
Spyder Editor

This is a temporary script file.
"""

import pandas as pd
import re

from nltk.corpus import stopwords
from nltk import FreqDist

from sklearn.model_selection import train_test_split

import numpy as np

import gensim.models as genmod

from keras.preprocessing import sequence

import keras
from keras.layers import LSTM
from keras.layers import Dense
from keras.layers import Input
from keras.layers import Dropout
from keras.layers import Embedding
from keras.models import Model
from keras.layers import Flatten
from keras import optimizers
#%%
def polishData(df):
    
    data = []

    for i in xrange(0, df.shape[0]):
        no_links = re.sub("https?:\/\/.*[\r\n]*", " ", df.iloc[:,0][i], flags=re.MULTILINE)

        letters_only = re.sub("[^a-zA-Z]", " ", no_links)

        lower_case = letters_only.lower()
        words = lower_case.split()
    
        words = [w for w in words if not w in stopwords.words("english")]
    
        data.append(words)
        
    return data
#%%
def labelsOneHot(df):
    sentiOneHot = pd.get_dummies(df.iloc[:,1])

    labels = np.empty((sentiOneHot.shape), dtype = int)

    for i in xrange(0,sentiOneHot.shape[1]):
        numbers = np.array(sentiOneHot.iloc[:,i])
        labels[:,i] = numbers

    return labels
#%%
def polishDataSet(df):
    data = polishData(df)
    labels = labelsOneHot(df)
    
    return data, labels
#%%
def vocabBuilder (data, unknown = True, min_no_of_words = 1):
    tokens = []
    
    for i in xrange(0, len(data)):
        for j in xrange(0,len(data[i])):
            tokens.append(data[i][j])
            
    freqdist = FreqDist(tokens)
    
    vocab = []
    
    for key in freqdist:
        if freqdist[key] >= min_no_of_words:
            vocab.append(key)
    
    if unknown:
        vocab.append('UNKNOWN')
    
    return vocab
#%%
def fit_unknown_token(data, vocab):
    
    data_unknown = data
    
    for i in xrange(0, len(data)):
        for j in xrange(0, len(data[i])):
            if data[i][j] not in vocab:
                data_unknown[i][j] = 'UNKNOWN'
                
    return data_unknown
#%%
def word2vec(data, window, min_count, size, iterations):
    model = genmod.Word2Vec(train_data, window = window, min_count = min_count, 
                            size = size, iter = iterations)
    return model.wv
#%%
def word_embedding_matrix_builder(word_vectors_model, size, vocab):
        
    embeddingsMatrix = np.zeros((len(vocab), size))

    for i in xrange(0, len(vocab)):
        if vocab[i] in word_vectors_model.vocab:
            embeddingsMatrix[i] = word_vectors_model[vocab[i]]

    return embeddingsMatrix
#%%
def word_to_index(data, vocab):
    
    data_word_to_index = []
    
    for i in xrange(0, len(data)):
        wordToIndex = []

        for j in xrange(0, len(data[i])):            
            l = vocab.index(data[i][j])
            wordToIndex.append(l)
        
        data_word_to_index.append(wordToIndex)

    return data_word_to_index
#%%
def makeModel(train_data, train_labels, vocab_length, pretrained = False, wordEmbeddingsLocal = None, 
              wordEmbeddingsGlove = None, wordEmbeddingsGoogle = None, trainable = False, size = 300,
              hidden_layer = 128, activation = 'relu', optimizer = 'adam', loss = 'categorical_crossentropy'):
    
    main_input = Input(shape = (train_data.shape[1],), dtype = 'float64', name = 'main_input')
    word_embeddings_random = Embedding(len(vocab), size, input_length = train_data.shape[1])(main_input)
    word_embeddings_pretrained_word2vec_local = Embedding(len(vocab), wordEmbeddingsLocal.shape[1], 
                                                          input_length = train_data.shape[1],
                                                          weights = [wordEmbeddingsLocal], 
                                                          trainable = trainable) (main_input)
    word_embeddings_pretrained_glove = Embedding(len(vocab), wordEmbeddingsGlove.shape[1], 
                                                 input_length = train_data.shape[1],
                                                 weights = [wordEmbeddingsGlove], 
                                                 trainable = trainable) (main_input)
    word_embeddings_pretrained_word2vec_google = Embedding(len(vocab), wordEmbeddingsGoogle.shape[1], 
                                                           input_length = train_data.shape[1],
                                                           weights = [wordEmbeddingsGoogle], 
                                                           trainable = trainable) (main_input)
    
    lstm_random_1 = LSTM(256)(word_embeddings_random)
    lstm_pretrained_word2vec_local_1 = LSTM(256)(word_embeddings_pretrained_word2vec_local)
    lstm_pretrained_glove_1 = LSTM(256)(word_embeddings_pretrained_glove)
    lstm_pretrained_word2vec_google_1 = LSTM(256)(word_embeddings_pretrained_word2vec_google)

    
    lstm_features = keras.layers.concatenate([lstm_random_1, lstm_pretrained_word2vec_local_1, 
                                              lstm_pretrained_glove_1, lstm_pretrained_word2vec_google_1])
    
    dense_output_1 = Dense(hidden_layer, activation = activation) (lstm_features)
    dropout_dense_1 = Dropout(0.5)(dense_output_1)
    dense_output_2 = Dense(hidden_layer, activation = activation) (dropout_dense_1)
    dropout_dense_2 = Dropout(0.5)(dense_output_2)
    main_output = Dense(train_labels.shape[1], activation = 'softmax')(dropout_dense_2)
    
    model = Model(inputs = [main_input], outputs = [main_output])
 
    model.compile(optimizer = optimizer, loss = loss, metrics = ['accuracy'])
    
    return model
#%%
def evaluateModel(test_data, test_labels):   
    scores = model.evaluate(test_data, test_labels)
    print("\n%s: %.2f%%" % (model.metrics_names[1], scores[1]*100))             
#%%
path = "./train_data.csv"
df = pd.read_csv(path)
df
#%%
data, labels = polishDataSet(df)
#%%
test_split = 0.20
train_data, test_data, train_labels, test_labels = train_test_split(data, labels, 
                                                                    test_size = test_split, 
                                                                    random_state = 42)
#%%
vocab = vocabBuilder(train_data, unknown = True, min_no_of_words = 2)
#%%
train_data_fit = fit_unknown_token(train_data, vocab)
test_data_fit = fit_unknown_token(test_data, vocab)
#%%
#wordModelGoogleWord2Vec = models.KeyedVectors.load_word2vec_format('../../GoogleNews-vectors-negative300.bin', binary=True)
#wordModelGlove = models.KeyedVectors.load_word2vec_format('',binary = True)
wordModelLocal = word2vec(train_data, 5, 2, 128, 20)  
#%%
wordEmbeddingsMatrixLocal = word_embedding_matrix_builder(wordModelLocal, 128, vocab)
#%%
train_data_sequence = word_to_index(train_data_fit, vocab)
test_data_sequence = word_to_index(test_data_fit, vocab)
#%%
train_size = 20
train_data_padded = sequence.pad_sequences(train_data_sequence, maxlen = train_size)
test_data_padded = sequence.pad_sequences(test_data_sequence, maxlen = train_size)
#%%
model = makeModel(train_data_padded, train_labels, len(vocab), pretrained = False,
                  wordEmbeddingsGlove = wordEmbeddingsMatrixLocal, wordEmbeddingsGoogle = wordEmbeddingsMatrixLocal,
                  wordEmbeddingsLocal = wordEmbeddingsMatrixLocal, trainable = False, size = 300)
#%%
epochs = 3
batch_size = 128
model.fit(train_data_padded, train_labels, epochs = epochs, batch_size = batch_size)
#%%
model.evaluateModel(test_data_padded, test_labels)