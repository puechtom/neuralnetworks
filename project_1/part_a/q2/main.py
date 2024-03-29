import numpy as np
import theano
import theano.tensor as T
import matplotlib.pyplot as plt
import time

def init_bias(n = 1):
    return(np.zeros(n))

def create_bias(n = 1):
    return(theano.shared(init_bias(n), theano.config.floatX))

def init_weights(n_in=1, n_out=1, logistic=True):
    W_values = np.asarray(
        np.random.uniform(
        low=-np.sqrt(6. / (n_in + n_out)),
        high=np.sqrt(6. / (n_in + n_out)),
        size=(n_in, n_out)),
        dtype=theano.config.floatX
        )
    if logistic == True:
        W_values *= 4
    return W_values

def create_weights(n_in=1, n_out=1, logistic=True):
    W_values = init_weights(n_in, n_out, logistic)
    return (theano.shared(value=W_values, name='W', borrow=True))

# scale data
def scale(X, X_min, X_max):
    return (X - X_min)/(X_max-np.min(X, axis=0))

#do scale 2, with standard dev and mean value
def scaleN(X):
    return (X - np.mean(X)) / np.std(X)
# update parameters
def sgd(cost, params, lr=0.01):
    grads = T.grad(cost=cost, wrt=params)
    updates = []
    for p, g in zip(params, grads):
        updates.append([p, p - g * lr])
    return updates

def shuffle_data (samples, labels):
    idx = np.arange(samples.shape[0])
    np.random.shuffle(idx)
    #print  (samples.shape, labels.shape)
    samples, labels = samples[idx], labels[idx]
    return samples, labels

decay = 1e-6
learning_rate = 0.01
epochs = 1000

# theano expressions
X = T.matrix() #features
Y = T.matrix() #output

w1, b1 = create_weights(36, 10), create_bias(10) #weights and biases from input to hidden layer
w2, b2 = create_weights(10, 6, logistic=False), create_bias(6) #weights and biases from hidden to output layer

h1 = T.nnet.sigmoid(T.dot(X, w1) + b1)
py = T.nnet.softmax(T.dot(h1, w2) + b2)

y_x = T.argmax(py, axis=1)

cost = T.mean(T.nnet.categorical_crossentropy(py, Y)) + decay*(T.sum(T.sqr(w1)+T.sum(T.sqr(w2))))
params = [w1, b1, w2, b2]
updates = sgd(cost, params, learning_rate)

# compile
train = theano.function(inputs=[X, Y], outputs=cost, updates=updates, allow_input_downcast=True)
predict = theano.function(inputs=[X], outputs=y_x, allow_input_downcast=True)


#read train data
train_input = np.loadtxt('../../data/sat_train.txt',delimiter=' ')
trainX, train_Y = train_input[:,:36], train_input[:,-1].astype(int)
trainX_min, trainX_max = np.min(trainX, axis=0), np.max(trainX, axis=0)
trainX = scaleN(trainX)
#train X is the data matrix
#this is the desired output
train_Y[train_Y == 7] = 6
trainY = np.zeros((train_Y.shape[0], 6))
#this is the K matrix
trainY[np.arange(train_Y.shape[0]), train_Y-1] = 1


#read test data
test_input = np.loadtxt('../../data/sat_test.txt',delimiter=' ')
testX, test_Y = test_input[:,:36], test_input[:,-1].astype(int)

testX_min, testX_max = np.min(testX, axis=0), np.max(testX, axis=0)
testX = scaleN(testX)

test_Y[test_Y == 7] = 6
testY = np.zeros((test_Y.shape[0], 6))
testY[np.arange(test_Y.shape[0]), test_Y-1] = 1

print(trainX.shape, trainY.shape)
print(testX.shape, testY.shape)


# train and test
n = len(trainX)
result = dict()
result["test_accuracy"] = []
result["train_cost"] = []


time_for_update = np.zeros(n)

batch_size_list = [4, 8, 16, 32, 64]


for batch_size in batch_size_list:
    print(batch_size)
    test_accuracy = []
    train_cost = []
    t = time.time()
    result["times"] = []
    for i in range(epochs):
        trainX, trainY = shuffle_data(trainX, trainY)
        cost = 0.0

        for start, end in zip(range(0, n, batch_size), range(batch_size, n, batch_size)):
            t0 = time.time()
            cost += train(trainX[start:end], trainY[start:end])
            result["times"].append(1000*(time.time()-t0))

        train_cost.append(cost/(n // batch_size))

        test_accuracy.append(np.mean(np.argmax(testY, axis=1) == predict(testX)))
        # print(test_accuracy)


    w1.set_value(init_weights(36, 10))
    b1.set_value(init_bias(10)) #weights and biases from input to hidden layer

    w2.set_value(init_weights(10, 6, logistic=False))
    b2.set_value(init_bias(6)) #weights and biases from hidden to output layer

    result["test_accuracy"].append(test_accuracy)
    result["train_cost"].append(train_cost)



    time_for_update[batch_size] = (1000*(time.time()-t)) / (epochs * (n // batch_size))

#Plots
plt.figure()
for label, curve in zip(batch_size_list, result["train_cost"]):
    plt.plot(range(epochs), curve, label="batch size = " + str(label))
plt.legend(loc = 'upper right')
plt.xlabel('iterations')
plt.ylabel('cross-entropy')
plt.title('training cost')
plt.savefig('p2a_sample_cost.png')

plt.figure()
for label, curve in zip(batch_size_list, result["test_accuracy"]):
    plt.plot(range(epochs), curve, label="batch size = " + str(label))
plt.legend(loc = 'lower right')
plt.xlabel('iterations')
plt.ylabel('accuracy')
plt.title('test accuracy')
plt.savefig('p2a_sample_accuracy.png')


plt.figure()
plt.plot(batch_size_list, time_for_update[batch_size_list])
plt.xlabel('batch-size')
plt.ylabel('time in ms')
plt.title('time to update parameters')
plt.xticks(batch_size_list)
plt.savefig('p2b3_time_update.png')

plt.show()
