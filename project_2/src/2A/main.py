from load import mnist
import numpy as np
import pylab

import theano
from theano import tensor as T
from theano.tensor.nnet import conv2d
from theano.tensor.signal import pool

# 1 convolution layer, 1 max pooling layer and a softmax layer

np.random.seed(10)
batch_size = 128
noIters = 25
learningrate = 0.5
decayparameter = 1e-6
print('fuck off')
def init_weights_bias4(filter_shape, d_type):
    fan_in = np.prod(filter_shape[1:])
    fan_out = filter_shape[0] * np.prod(filter_shape[2:])

    bound = np.sqrt(6. / (fan_in + fan_out))
    w_values =  np.asarray(
            np.random.uniform(low=-bound, high=bound, size=filter_shape),
            dtype=d_type)
    b_values = np.zeros((filter_shape[0],), dtype=d_type)
    return theano.shared(w_values,borrow=True), theano.shared(b_values, borrow=True)

def init_weights_bias2(filter_shape, d_type):
    fan_in = filter_shape[1]
    fan_out = filter_shape[0]

    bound = np.sqrt(6. / (fan_in + fan_out))
    w_values =  np.asarray(
            np.random.uniform(low=-bound, high=bound, size=filter_shape),
            dtype=d_type)
    b_values = np.zeros((filter_shape[1],), dtype=d_type)
    return theano.shared(w_values,borrow=True), theano.shared(b_values, borrow=True)

def model(X, w1, b1, w2, b2, w3, b3):
    y1 = T.nnet.relu(conv2d(X, w1) + b1.dimshuffle('x', 0, 'x', 'x'))
    pool_dim = (2, 2)
    o1 = pool.pool_2d(y1, pool_dim)
    o2 = T.flatten(o1, outdim=2)

    y2 = T.nnet.relu(conv2d(y1, w2)) + b1.dimshuffle('x', 0, 'x', 'x'))
    o3 = pool.pool(y2, pool_dim)
    o4 = T.flatten(o3, outdim=2)

    pyx = T.nnet.softmax(T.dot(o4, w3) + b3)
    return y1, y2, o1, o3, pyx

def sgd(cost, params, lr=0.05, decay=0.0001):
    grads = T.grad(cost=cost, wrt=params)
    updates = []
    for p, g in zip(params, grads):
        updates.append([p, p - (g + decay*p) * lr])
    return updates

def shuffle_data (samples, labels):
    idx = np.arange(samples.shape[0])
    np.random.shuffle(idx)
    samples, labels = samples[idx], labels[idx]
    return samples, labels

trX, teX, trY, teY = mnist(onehot=True)

trX = trX.reshape(-1, 1, 28, 28)
teX = teX.reshape(-1, 1, 28, 28)

trX, trY = trX[:12000], trY[:12000]
teX, teY = teX[:2000], teY[:2000]


X = T.tensor4('X')
Y = T.matrix('Y')

num_filters1 = 15
w1, b1 = init_weights_bias4((num_filters1, 1, 9, 9), X.dtype)
num_filters2 = 20
w2, b2 = init_weights_bias4((num_filters1 * num_filters2, 1, 5, 5), X.dtype)
w3, b3 = init_weights_bias2((num_filters1 * num_filters2*3*3, 10), X.dtype)

y1, y2 o1, o2, py_x  = model(X, w1, b1, w2, b2, w3, b3)

y_x = T.argmax(py_x, axis=1)

cost = T.mean(T.nnet.categorical_crossentropy(py_x, Y))
params = [w1, b1, w2, b2, w3, b3]

updates = sgd(cost, params, learningrate, decayparameter)

train = theano.function(inputs=[X, Y], outputs=cost, updates=updates, allow_input_downcast=True)
predict = theano.function(inputs=[X], outputs=y_x, allow_input_downcast=True)
test = theano.function(inputs = [X], outputs=[y1, o1, y2, o2], allow_input_downcast=True)

a = []
for i in range(noIters):
    trX, trY = shuffle_data (trX, trY)
    teX, teY = shuffle_data (teX, teY)
    for start, end in zip(range(0, len(trX), batch_size), range(batch_size, len(trX), batch_size)):
        cost = train(trX[start:end], trY[start:end])
    a.append(np.mean(np.argmax(teY, axis=1) == predict(teX)))
    print(a[i])

pylab.figure()
pylab.plot(range(noIters), a)
pylab.xlabel('epochs')
pylab.ylabel('test accuracy')
pylab.savefig('figure_2a_1.png')

w = w1.get_value()
pylab.figure()
pylab.gray()
for i in range(25):
    pylab.subplot(5, 5, i+1); pylab.axis('off'); pylab.imshow(w[i,:,:,:].reshape(9,9))
#pylab.title('filters learned')
pylab.savefig('figure_2a_2.png')

ind = np.random.randint(low=0, high=2000)
convolved, pooled, convolved2, pooled2 = test(teX[ind:ind+1,:])

pylab.figure()
pylab.gray()
pylab.axis('off'); pylab.imshow(teX[ind,:].reshape(28,28))
#pylab.title('input image')
pylab.savefig('figure_2a_3.png')

pylab.figure()
pylab.gray()
for i in range(25):
    pylab.subplot(5, 5, i+1); pylab.axis('off'); pylab.imshow(convolved[0,i,:].reshape(20,20))
#pylab.title('convolved feature maps')
pylab.savefig('FirstConvLayer.png')

pylab.figure()
pylab.gray()
for i in range(5):
    pylab.subplot(5, 5, i+1); pylab.axis('off'); pylab.imshow(pooled[0,i,:].reshape(5,5))
#pylab.title('pooled feature maps')
pylab.savefig('FirstPoolLayer.png')

pylab.figure()
pylab.gray()
for i in range(25):
    pylab.subplot(5, 5, i+1); pylab.axis('off'); pylab.imshow(convolved2[0,i,:].reshape(6,6))
#pylab.title('second convolved feature maps')
pylab.savefig('SecondConvLayer.png')

pylab.figure()
pylab.gray()
for i in range(5):
    pylab.subplot(5, 5, i+1); pylab.axis('off'); pylab.imshow(pooled2[0,i,:].reshape(3,3))
#pylab.title('second pooled feature maps')
pylab.savefig('SecondPoolLayer.png')

pylab.show()
