# -*- coding: utf-8 -*-

from __future__ import division, print_function

from functools import partial
import tensorflow as tf
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.animation as animation
from hamiltonians import hamiltonian_time_derivative
from solver import rk4_step


# hamiltonian function for string modeled by series of masses and springs
def catenary_hamiltonian(qval,p):
    with tf.variable_scope('hamiltonian'):
        with tf.variable_scope('kinetic_energy'):
            T = tf.reduce_sum(1/2 * p**2)
        with tf.variable_scope('potential_energy'):
            V = qval[:,0]**2/2 + qval[:,-1]**2/2
            V += tf.reduce_sum(tf.nn.conv1d(
                    tf.expand_dims(qval,2),
                    filters=tf.reshape([1.,-1.],(-1,1,1)),
                    stride=1,
                    padding='VALID'
                )**2/2)
            V += 1e-2 * tf.reduce_sum(qval)
        return T + V

tf.reset_default_graph()
sess = tf.InteractiveSession()

# setup simulation
string_length = 100;
h = tf.constant(.05, dtype=tf.float32, name='time_step');
x0 = np.zeros((1,2*string_length))

# Initial Condition
x0[:,-string_length:] += 2*np.exp(-np.linspace(-10,30,string_length)**2)
x0[:,-string_length:] += np.exp(-np.linspace(-20,10,string_length)**2)

with tf.variable_scope('state'):
    x = tf.Variable(x0, dtype=tf.float32)
    t = tf.Variable(0, dtype=tf.float32)

dxdt = partial(hamiltonian_time_derivative, catenary_hamiltonian)
update = rk4_step(dxdt, t, x, h)

sess.run(tf.global_variables_initializer())
summary_writer = tf.summary.FileWriter('logdir/', sess.graph)

N = 40000
state = np.array([x0]*N, dtype=np.float32)

# run simulation
for i in range(N):
    _, state[i] = sess.run([update,x])

summary_writer.close()

# plot
fig, ax = plt.subplots()

line, = ax.plot(np.full((string_length),np.nan))

axes = plt.gca()
axes.set_xlim([-1,string_length])
axes.set_ylim([-30,30])

plt.title('Vibrating String')
plt.ylabel('Vertical Displacement')
plt.xlabel('Position Along String')

skip = 15

def animate(i):
    line.set_ydata(state[skip*i,0,:string_length])# update the data
    return line,

ani = animation.FuncAnimation(fig, animate, range(N//skip),
                              interval=skip, blit=True)

#Set up formatting for the movie files
#Writer = animation.writers['ffmpeg']
#writer = Writer(fps=60, metadata=dict(artist='Me'), bitrate=1800)

#ani.save('im.mp4', writer=writer)

plt.show()
