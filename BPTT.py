"""Truncated back-propagation-through-time (BPTT).

Notes
-----
  This script is version v0. It provides the base for all subsequent
  iterations of the project.
  
Requirements
------------
  See "requirements.txt"
  
Comments
--------
  This version implements k1=k2.

"""

#%% import libraries and modules
import matplotlib.pyplot as plt
import numpy as np
import os

#%% build BPTT class
class BPTT:
    """BPTT class."""
    def __init__(self, dim_input, dim_hidden, dim_output, num_training_iterations, learning_rate, sequence_length):
        self.dim_input = dim_input # input layer dimension
        self.dim_hidden = dim_hidden # hidden layer dimension
        self.dim_output = dim_output # output layer dimension
        
        self.num_training_iterations = num_training_iterations # number of training iterations
        self.learning_rate = learning_rate # learning rate
        self.sequence_length = sequence_length # sequence length
        
        self.w_input_hidden  = np.random.randn(dim_hidden, dim_input)  * 0.01 # input-to-hidden weight matrix
        self.w_hidden_hidden = np.random.randn(dim_hidden, dim_hidden) * 0.01 # hidden-to-hidden weight matrix
        self.w_hidden_output = np.random.randn(dim_output, dim_hidden) * 0.01 # hidden-to-output weight matrix
        self.bias_hidden = np.zeros([dim_hidden, 1]) # hidden bias vector
        self.bias_output = np.zeros([dim_output, 1]) # output bias vector
        
    def softmax(self, y):
        """Apply softmax function."""
        f_y = np.exp(y) / np.sum(np.exp(y))
        return f_y
    
    def tanh(self, y):
        """Apply tanh function."""
        f_y = np.tanh(y)
        return f_y
        
    def compute_loss(self, input_indices, target_indices, hidden_prev):
        """Forward computation."""
        input_patterns, hidden_states, output_patterns, output_probabilities = {}, {}, {}, {} # empty dictionaries
        hidden_states[-1] = np.copy(hidden_prev) # initialize to previous hidden state
        loss = 0
        for timestep in range(self.sequence_length):
            input_patterns[timestep] = np.zeros([vocab_size, 1]) # input pattern of size 'vocab_size'
            input_patterns[timestep][input_indices[timestep]] = 1 # input pattern
            hidden_states[timestep] = self.tanh(np.dot(self.w_input_hidden, input_patterns[timestep]) + np.dot(self.w_hidden_hidden, hidden_states[timestep-1]) + self.bias_hidden) # compute hidden state
            output_patterns[timestep] = np.dot(self.w_hidden_output, hidden_states[timestep]) + self.bias_output # compute unnormalized log probabilities
            output_probabilities[timestep] = self.softmax(output_patterns[timestep]) # compute probabilities
            loss += -np.log(output_probabilities[timestep][target_indices[timestep]]).item() # apply cross-entropy loss
        """Backward computation."""
        dw_input_hidden, dw_hidden_hidden, dw_hidden_output = np.zeros_like(self.w_input_hidden), np.zeros_like(self.w_hidden_hidden), np.zeros_like(self.w_hidden_output) # initialize gradients for weight matrices
        dbias_hidden, dbias_output = np.zeros_like(self.bias_hidden), np.zeros_like(self.bias_output) # initialize gradients for bias vectors
        dhidden_next = np.zeros([self.dim_hidden, 1]) # initialize gradient of current hidden state w.r.t next hidden state
        for timestep in reversed(range(self.sequence_length)):
            doutput_pattern = np.copy(output_probabilities[timestep])
            doutput_pattern[target_indices[timestep]] -= 1 # backprop into output layer
            dw_hidden_output += np.dot(doutput_pattern, hidden_states[timestep].T) # accumulate gradient
            dbias_output += doutput_pattern # accumulate gradient
            dhidden = np.dot(self.w_hidden_output.T, doutput_pattern) + dhidden_next # backprop into hidden layer
            dhidden_raw = (1 - hidden_states[timestep] * hidden_states[timestep]) * dhidden # backprop through tanh nonlinearity
            dw_hidden_hidden += np.dot(dhidden_raw, hidden_states[timestep-1].T) # accumulate gradient
            dbias_hidden += dhidden_raw # accumulate gradient
            dw_input_hidden += np.dot(dhidden_raw, input_patterns[timestep].T) # accumulate gradient
            dhidden_next = np.dot(self.w_hidden_hidden.T, dhidden_raw) # gradient update of current hidden state w.r.t next hidden state
        """Clip gradients."""
        dw_input_hidden = np.clip(dw_input_hidden, -5, 5) # input-to-hidden
        dw_hidden_hidden = np.clip(dw_hidden_hidden, -5, 5) # hidden-to-hidden
        dw_hidden_output = np.clip(dw_hidden_output, -5, 5) # hidden-to-output
        dbias_hidden = np.clip(dbias_hidden, -5, 5) # hidden bias
        dbias_output = np.clip(dbias_output, -5, 5) # output bias
        return loss, dw_input_hidden, dw_hidden_hidden, dw_hidden_output, dbias_hidden, dbias_output, hidden_states, hidden_states[self.sequence_length-1]
        
    def fit(self):
        """Fit model to training data."""
        losses = []
        iteration_count = 0
        sequence_pointer = 0
        while iteration_count <= self.num_training_iterations:
            if iteration_count == 0 or sequence_pointer+self.sequence_length >= len(data):
                hidden_prev = np.zeros([self.dim_hidden, 1]) # initialize previous hidden state to zero
                sequence_pointer = 0
            input_indices = [character_to_index[character] for character in data[sequence_pointer: sequence_pointer+self.sequence_length]] # specify input indices
            target_indices = [character_to_index[character] for character in data[sequence_pointer+1: sequence_pointer+self.sequence_length+1]] # specify target indices
            """Compute loss."""
            loss, dw_input_hidden, dw_hidden_hidden, dw_hidden_output, dbias_hidden, dbias_output, hidden_states, hidden_prev = self.compute_loss(input_indices, target_indices, hidden_prev)
            losses.append(loss)
            """Update weights and biases."""
            self.w_input_hidden += -self.learning_rate * dw_input_hidden # input-to-hidden
            self.w_hidden_hidden += -self.learning_rate * dw_hidden_hidden # hidden-to-hidden
            self.w_hidden_output += -self.learning_rate * dw_hidden_output # hidden-to-output
            self.bias_hidden += -self.learning_rate * dbias_hidden # hidden bias
            self.bias_output += -self.learning_rate * dbias_output # output bias
            if iteration_count % 100 == 0:
                print(''.join(['=']*self.sequence_length) + '\niteration {}/{} - train loss: {:.4f}'.format(iteration_count, self.num_training_iterations, loss)) # print iteration_count every 100 iterations
                seed_index = 0
                input_character, actual_predictions = self.predict(seed_index=seed_index, input_indices=input_indices, hidden_state=hidden_states[seed_index-1], num_predictions=self.sequence_length-seed_index)
                print('input:            {}'.format(''.join(input_character)))
                print('next predictions: {}'.format(''.join(actual_predictions)))
            sequence_pointer += self.sequence_length
            iteration_count += 1
        return hidden_states, input_indices, target_indices, losses
    
    def predict(self, seed_index, input_indices, hidden_state, num_predictions):
        """Perform model predictions."""
        input_pattern = np.zeros([vocab_size, 1]) # input pattern of size 'vocab_size'
        input_pattern[input_indices[seed_index]] = 1 # input pattern
        input_character = [index_to_character[input_pattern.argmax()]] # specify input character
        actual_predictions = []
        for timestep in range(num_predictions):
            hidden_state = self.tanh(np.dot(self.w_input_hidden, input_pattern) + np.dot(self.w_hidden_hidden, hidden_state) + self.bias_hidden) # compute hidden state
            output_prob = self.softmax(np.dot(self.w_hidden_output, hidden_state) + self.bias_output) # compute probabilities
            # sampled_index = np.random.choice(range(vocab_size), p=output_prob.ravel()) # sample from the probability distribution
            sampled_index = output_prob.argmax() # choose argmax
            actual_predictions.append(index_to_character[sampled_index]) # store model prediction
            input_pattern = np.zeros([vocab_size, 1])
            input_pattern[sampled_index] = 1 # feedback model prediction as input in the next timestep
        return input_character, actual_predictions
    
#%% load data and extract vocabulary info
data = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h', 'i', 'j', 'k', 'l', 'm',
        'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z'] # alphabet characters

vocab = sorted(set(data)) # unique characters
vocab_size = len(vocab) # number of unique characters

#%% specify indices and characters of inputs and corresponding targets
character_to_index = {character:index for index, character in enumerate(vocab)} # convert character to index
index_to_character = {index:character for index, character in enumerate(vocab)} # convert index to character

#%% instantiate BPTT class
model = BPTT(
    dim_input=vocab_size,
    dim_hidden=10,
    dim_output=vocab_size,
    num_training_iterations=10_000,
    learning_rate=0.01,
    sequence_length=25)

#%% fit model to training data
hidden_states, input_indices, target_indices, losses = model.fit()

#%% specify filepath
cwd = os.getcwd() # get current working directory
fileName = 'images' # specify filename

if os.path.exists(os.path.join(cwd, fileName)) == False: # if path does not exist
    os.makedirs(fileName) # create directory with specified filename

#%% plot loss
fig, ax = plt.subplots()
plt.plot(losses, label='training')
plt.xlabel('Iteration #')
plt.ylabel('Loss')
plt.legend()
plt.tight_layout()
fig.savefig(os.path.join(cwd + '/' + fileName, 'figure_1'))

#%% perform model predictions
# seed_index = 0 # choose any value between 0 and sequence_length-1
# prev_hidden_state = hidden_states[seed_index-1] # select previous hidden state (seed_index-1)
# num_predictions = model.sequence_length-seed_index # could be of any arbitrary size

# input_character, actual_predictions = model.predict(seed_index=seed_index, input_indices=input_indices, hidden_state=prev_hidden_state, num_predictions=num_predictions)
# print('input:            {}'.format(''.join(input_character)))
# print('next predictions: {}'.format(''.join(actual_predictions)))
