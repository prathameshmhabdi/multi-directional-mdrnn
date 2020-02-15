from unittest import TestCase
import numpy as np
from mdrnn import MDRNN, Direction
from tensorflow.keras import initializers
import tensorflow as tf


class Degenerate2DInputTests(TestCase):
    def setUp(self):
        seed = 1

        kwargs = dict(units=5, input_shape=(None, None, 2),
                      kernel_initializer=initializers.glorot_uniform(seed),
                      recurrent_initializer=initializers.he_normal(seed),
                      bias_initializer=initializers.Constant(2),
                      return_sequences=True,
                      activation='tanh'
                      )

        self.rnn2d = MDRNN(**kwargs)

        keras_kwargs = dict(kwargs)
        keras_kwargs.update(dict(input_shape=(None, 2)))
        self.keras_rnn = tf.keras.layers.SimpleRNN(**keras_kwargs)

    def assert_rnn_outputs_equal(self, x_1d, x_2d):
        actual = self.rnn2d(x_2d).numpy()

        desired_shape = x_2d.shape[:-1] + (5, )
        desired = self.keras_rnn(x_1d).numpy().reshape(desired_shape)
        np.testing.assert_almost_equal(actual, desired, 6)

    def test_on_1x1_input(self):
        x = np.array([5, 10], dtype=np.float)
        x_1d = x.reshape((1, 1, 2))
        x_2d = x.reshape((1, 1, 1, 2))

        self.assert_rnn_outputs_equal(x_1d, x_2d)

    def test_on_1xn_input(self):
        x_2d = np.random.rand(3, 1, 4, 2)
        x_1d = x_2d.reshape((3, 4, 2))
        self.assert_rnn_outputs_equal(x_1d, x_2d)

    def test_on_nx1_input(self):
        x_2d = np.random.rand(3, 4, 1, 2)
        x_1d = x_2d.reshape((3, 4, 2))
        self.assert_rnn_outputs_equal(x_1d, x_2d)


class GridInputTests(TestCase):
    def test_shape(self):
        rnn2d = MDRNN(units=5, input_shape=(None, None, 1),
                      kernel_initializer=initializers.Constant(1),
                      recurrent_initializer=initializers.Constant(1),
                      bias_initializer=initializers.Constant(-1),
                      return_sequences=True,
                      activation='tanh')

        x = np.arange(6).reshape((1, 2, 3, 1))

        res = rnn2d.call(x)

        self.assertEqual((1, 2, 3, 5), res.shape)

    def test_result(self):
        rnn2d = MDRNN(units=1, input_shape=(None, None, 1),
                      kernel_initializer=initializers.Identity(),
                      recurrent_initializer=initializers.Identity(1),
                      bias_initializer=initializers.Constant(-1),
                      return_sequences=True,
                      activation=None)

        x = np.arange(6).reshape((1, 2, 3, 1))

        actual = rnn2d.call(x)

        desired = np.array([
            [-1, -1, 0],
            [1, 3, 7]
        ]).reshape((1, 2, 3, 1))

        np.testing.assert_almost_equal(desired, actual.numpy(), 6)

    def test_2drnn_output_when_providing_initial_state(self):
        rnn2d = MDRNN(units=1, input_shape=(None, None, 1),
                      kernel_initializer=initializers.Identity(),
                      recurrent_initializer=initializers.Identity(1),
                      bias_initializer=initializers.Constant(-1),
                      return_sequences=True,
                      activation=None)

        x = np.arange(6).reshape((1, 2, 3, 1))

        initial_state = [tf.ones(shape=(1, 1)), tf.ones(shape=(1, 1))]

        actual = rnn2d.call(x, initial_state=initial_state)
        desired = np.array([
            [1, 1, 2],
            [3, 7, 13]
        ]).reshape((1, 2, 3, 1))
        np.testing.assert_almost_equal(desired, actual.numpy(), 6)

    def test_result_after_running_rnn_on_3d_input(self):
        rnn3d = MDRNN(units=1, input_shape=(None, None, None, 1),
                      kernel_initializer=initializers.Identity(),
                      recurrent_initializer=initializers.Identity(1),
                      bias_initializer=initializers.Constant(1),
                      return_sequences=True,
                      return_state=True,
                      activation=None)

        x = np.arange(2*2*2).reshape((1, 2, 2, 2, 1))

        outputs, state = rnn3d.call(x)

        desired = np.array([
            [[1, 3],
             [4, 11]],
            [[6, 15],
             [17, 51]]
        ]).reshape((1, 2, 2, 2, 1))

        np.testing.assert_almost_equal(desired, outputs.numpy(), 6)

        desired_state = desired[:, -1, -1, -1]
        np.testing.assert_almost_equal(desired_state, state.numpy(), 6)

    def test_shape_of_output_of_6d_rnn(self):
        units = 7
        last_dim_size = 12
        rnn = MDRNN(units=units, input_shape=(None, None, None, None, None, None, last_dim_size),
                    return_sequences=True,
                    activation='tanh')

        x = tf.zeros(shape=(2, 3, 1, 2, 2, 1, 5, last_dim_size))

        result = rnn.call(x)
        self.assertEqual((2, 3, 1, 2, 2, 1, 5, units), result.shape)


class RnnMovingSouthEast(TestCase):
    def setUp(self):
        kwargs = dict(units=1, input_shape=(None, None, 1),
                      kernel_initializer=initializers.Identity(),
                      recurrent_initializer=initializers.Identity(1),
                      bias_initializer=initializers.Constant(-1),
                      return_sequences=True,
                      return_state=True,
                      direction=self.get_direction(),
                      activation=None)

        self.rnn = MDRNN(**kwargs)

        self.x = np.arange(6).reshape((1, 2, 3, 1))

    def get_direction(self):
        return Direction(1, 1)

    def get_expected_result(self):
        return np.array([
            [-1, -1, 0],
            [1, 3, 7]
        ]).reshape((1, 2, 3, 1))

    def get_expected_last_state(self):
        return self.get_expected_result()[:, -1, -1]

    def assert_rnn_outputs_are_correct(self, output, state):
        expected_result = self.get_expected_result()
        np.testing.assert_almost_equal(expected_result, output.numpy(), 6)

        expected_state = self.get_expected_last_state()
        np.testing.assert_almost_equal(expected_state, state.numpy(), 6)

    def test_2d_rnn_scanning_in_given_direction(self):
        output, state = self.rnn.call(self.x)
        self.assert_rnn_outputs_are_correct(output, state)

    def test_2d_rnn_scanning_in_given_direction_using_functor(self):
        output, state = self.rnn(self.x)
        self.assert_rnn_outputs_are_correct(output, state)


class RnnMovingSouthWest(RnnMovingSouthEast):
    def get_direction(self):
        return Direction(1, -1)

    def get_expected_result(self):
        return np.array([
            [0, 1, 1],
            [11, 9, 5]
        ]).reshape((1, 2, 3, 1))

    def get_expected_last_state(self):
        return np.array([11]).reshape((1, 1))


class RnnMovingNorthEast(RnnMovingSouthEast):
    def get_direction(self):
        return Direction(-1, 1)

    def get_expected_result(self):
        return np.array([
            [1, 6, 16],
            [2, 5, 9]
        ]).reshape((1, 2, 3, 1))

    def get_expected_last_state(self):
        return np.array([16]).reshape((1, 1))


class RnnMovingNorthWest(RnnMovingSouthEast):
    def get_direction(self):
        return Direction(-1, -1)

    def get_expected_result(self):
        return np.array([
            [20, 12, 5],
            [9, 7, 4]
        ]).reshape((1, 2, 3, 1))

    def get_expected_last_state(self):
        return np.array([20]).reshape((1, 1))
