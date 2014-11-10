# Compares the predictive accuracy of using
# standard fingerprints versus custom convolutional nets.
#
# Dougal Maclaurin
# David Duvenaud
# Ryan P. Adams
#
# Sept 2014

import sys
import numpy as np
import numpy.random as npr

from deepmolecule import tictoc, normalize_array, sgd_with_momentum, get_data_file, load_data
from deepmolecule import build_morgan_deep_net, build_morgan_flat_net
from deepmolecule import build_universal_net, output_dir

def train_nn(net_builder_fun, smiles, raw_targets, arch_params, train_params,
             validation_smiles=None, validation_targets=None):
    npr.seed(1)
    targets, undo_norm = normalize_array(raw_targets)
    loss_fun, grad_fun, pred_fun, _, N_weights = net_builder_fun(**arch_params)
    def callback(epoch, weights):
        if epoch % 10 == 0:
            train_preds = undo_norm(pred_fun(weights, smiles))
            print "\nTraining RMSE after epoch", epoch, ":",\
                np.sqrt(np.mean((train_preds - raw_targets)**2)),
            if validation_smiles and validation_targets:
                validation_preds = undo_norm(pred_fun(weights, validation_smiles))
                print "Validation RMSE", epoch, ":",\
                    np.sqrt(np.mean((validation_preds - validation_targets)**2)),
        else:
            print ".",
    grad_fun_with_data = lambda idxs, w : grad_fun(w, smiles[idxs], targets[idxs])
    trained_weights = sgd_with_momentum(grad_fun_with_data, len(targets), N_weights,
                                        callback, **train_params)
    return lambda new_smiles : undo_norm(pred_fun(trained_weights, new_smiles))


def random_net_linear_output(net_builder_fun, smiles, raw_targets, arch_params, train_params):
    """Creates a network with random weights, and trains a ridge regression model on top."""
    npr.seed(1)
    targets, undo_norm = normalize_array(raw_targets)
    _, _, _, output_layer_fun, N_weights = net_builder_fun(**arch_params)
    net_weights = npr.randn(N_weights) * train_params['param_scale']
    train_outputs = output_layer_fun(net_weights, smiles)
    linear_weights = np.linalg.solve(np.dot(train_outputs.T, train_outputs)
                                     + np.eye(train_outputs.shape[1]) * train_params['l2_reg'],
                                     np.dot(train_outputs.T, targets))
    return lambda new_smiles : undo_norm(np.dot(output_layer_fun(net_weights, new_smiles),
                                                linear_weights))


def main():
    # Parameters for convolutional net.
    conv_train_params = {'num_epochs'  : 5,
                         'batch_size'  : 200,
                         'learn_rate'  : 1e-3,
                         'momentum'    : 0.9,
                         'param_scale' : 0.1,
                         'gamma'       : 0.9}
    conv_arch_params = {'num_hidden_features' : [10, 10, 500],
                        'permutations' : False}

    # Parameters for standard net build on Morgan fingerprints.
    morgan_train_params = {'num_epochs'  : 5,
                           'batch_size'  : 200,
                           'learn_rate'  : 1e-3,
                           'momentum'    : 0.98,
                           'param_scale' : 0.1,
                           'gamma'       : 0.9}
    morgan_deep_arch_params = {'h1_size'    : 500,
                               'h1_dropout' : 0.01,
                               'fp_length'  : 512,
                               'fp_radius'  : 4}
    morgan_flat_arch_params = {'fp_length'  : 512,
                               'fp_radius'  : 4}

    linear_train_params = {'param_scale' : 0.1,
                           'l2_reg'      : 0.1}

    task_params = {'N_train'     : 10000,
                   'N_valid'     : 10,
                   'N_test'      : 10,
                   'target_name' : 'Molecular Weight',
                   'data_file'   : get_data_file('2014-11-03-all-tddft/processed.csv')}
    #target_name = 'Log Rate'
    #'Polar Surface Area'
    #'Number of Rings'
    #'Number of H-Bond Donors'
    #'Number of Rotatable Bonds'
    #'Minimum Degree'

    print "Linear net training params: ", linear_train_params
    print "Morgan net training params: ", morgan_train_params
    print "Morgan flat net architecture params: ", morgan_flat_arch_params
    print "Morgan deep net architecture params: ", morgan_deep_arch_params
    print "Conv net training params: ", conv_train_params
    print "Conv net architecture params: ", conv_arch_params
    print "Task params", task_params
    print "Output directory:", output_dir()

    print "\nLoading data..."
    traindata, valdata, testdata = load_data(task_params['data_file'],
                        (task_params['N_train'], task_params['N_valid'], task_params['N_test']))
    train_inputs, train_targets = traindata['smiles'], traindata[task_params['target_name']]
    val_inputs, val_targets = valdata['smiles'], valdata[task_params['target_name']]
    test_inputs, test_targets = testdata['smiles'], testdata[task_params['target_name']]

    def print_performance(pred_func):
        train_preds = pred_func(train_inputs)
        test_preds = pred_func(test_inputs)
        print "\nPerformance (RMSE):"
        print "Train:", np.sqrt(np.mean((train_preds - train_targets)**2))
        print "Test: ", np.sqrt(np.mean((test_preds - test_targets)**2))
        print "-" * 80

    #def save_predictions(pred_func, filename):
    #    train_preds = pred_func(train_inputs)
    #    test_preds = pred_func(test_inputs)
    #    train_preds - train_targets)**2))
    #    print "Test: ", np.sqrt(np.mean((test_preds - test_targets)**2))
    #    print "-" * 80

    print "-" * 80
    print "Mean predictor"
    y_train_mean = np.mean(train_targets)
    print_performance(lambda x : y_train_mean)

    print "Fingerprints with linear weights"
    predictor = random_net_linear_output(build_morgan_flat_net, train_inputs, train_targets,
                                         morgan_flat_arch_params, linear_train_params)
    print_performance(predictor)

    print "Fingerprints with random net on top and linear weights"
    predictor = random_net_linear_output(build_morgan_deep_net, train_inputs, train_targets,
                                         morgan_deep_arch_params, linear_train_params)
    print_performance(predictor)

    print "Random net with linear weights"
    predictor = random_net_linear_output(build_universal_net, train_inputs, train_targets,
                                         conv_arch_params, linear_train_params)
    print_performance(predictor)

    #print "Training vanilla neural net"
    #with tictoc():
    #    predictor = train_nn(build_morgan_deep_net, train_inputs, train_targets,
    #                         morgan_deep_arch_params, morgan_train_params, val_inputs, val_targets)
    #    print "\n"
    #print_performance(predictor)

    #print "Training custom neural net : array representation"
    #with tictoc():
    #    predictor = train_nn(build_universal_net, train_inputs, train_targets,
    #                         conv_arch_params, conv_train_params, val_inputs, val_targets)
    #    print "\n"
    #print_performance(predictor)


if __name__ == '__main__':
    sys.exit(main())