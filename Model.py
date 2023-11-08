import tensorflow as tf
from keras import layers


def create_dqn_model(input_shape, number_of_actions):
    """
    Creates a DQN model.

    :param input_shape: The shape of the input state space
    :param number_of_actions: The number of possible actions
    :return: A compiled Keras model
    """
    model = tf.keras.Sequential([
        layers.InputLayer(input_shape=input_shape),
        layers.Dense(128, activation='relu'),
        layers.Dense(64, activation='relu'),
        layers.Dense(32, activation='relu'),
        layers.Dense(number_of_actions, activation='linear')  # Q-value for each action
    ])

    model.compile(optimizer=tf.keras.optimizers.Adam(learning_rate=0.001),
                  loss='mse')  # Mean Squared Error loss is commonly used in DQN

    return model


def train_dqn_model(model, states, actions, rewards, next_states, done_flags):
    """
    Train the DQN model.

    :param model: The DQN model
    :param states: Batch of states
    :param actions: Batch of actions taken
    :param rewards: Batch of rewards received
    :param next_states: Batch of states following the actions
    :param done_flags: Batch of boolean values indicating if the episode ended after the action
    """
    # Predict Q-values for the starting states
    current_q_values = model.predict(states)

    # Predict the Q-values for the next states
    next_q_values = model.predict(next_states)

    # The target Q-value is the reward plus the discounted max future Q-value
    # Note: This is a simplified version and does not handle done flags or use a separate target network
    max_future_q_values = np.max(next_q_values, axis=1)
    target_q_values = rewards + (1 - done_flags) * 0.99 * max_future_q_values  # discount factor gamma = 0.99

    # Update the Q-values for the actions taken
    for i, action in enumerate(actions):
        current_q_values[i, action] = target_q_values[i]

    # Train the model
    model.fit(states, current_q_values, epochs=1, verbose=0)
