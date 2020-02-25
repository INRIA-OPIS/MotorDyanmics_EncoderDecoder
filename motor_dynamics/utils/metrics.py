import math

import numpy as np
import scipy.io as sio

import torch
import torch.nn as nn
import torch.nn.functional as F

from sklearn.metrics import r2_score, mean_absolute_error
from sklearn.metrics import mean_squared_log_error

def flatten_extra_dims(quant):
    return quant.flatten()

def r2(y_true, y_pred):
    y_true = flatten_extra_dims(y_true)
    y_pred = flatten_extra_dims(y_pred)
    return r2_score(y_true, y_pred)


def rmsle(y_true, y_pred):
    assert len(y_true) == len(y_pred)
    y_true = flatten_extra_dims(y_true)
    y_pred = flatten_extra_dims(y_pred)
    terms_to_sum = (np.log(y_pred + abs(y_pred) + 0.0001) - np.log(y_true + 1)) ** 2.0
    return (sum(terms_to_sum) * (1.0/len(y_true))) ** 0.5


def rmse(y_true, y_pred):
    y_true = flatten_extra_dims(y_true)
    y_pred = flatten_extra_dims(y_pred)
    return np.sqrt(((y_pred - y_true) ** 2).mean())


def mae(y_true, y_pred):
    y_true = flatten_extra_dims(y_true)
    y_pred = flatten_extra_dims(y_pred)
    return mean_absolute_error(y_true, y_pred)


def smape(y_true, y_pred):
    y_true = flatten_extra_dims(y_true)
    y_pred = flatten_extra_dims(y_pred)
    return 100.0/ len(y_true) * np.sum(2.0 * np.abs(y_pred - y_true) / \
           (np.abs(y_true) + np.abs(y_pred) + 0.00001))


def sc(signal):
    signal = flatten_extra_dims(signal)
    return np.sum(abs(signal[1:] - signal[:-1]))


def smape_vs_sc(y_true, y_pred, window):
    y_true = flatten_extra_dims(y_true)
    y_pred = flatten_extra_dims(y_pred)
    smape_vs_sc_all_windows = []

    for i in range(0, y_true.shape[0]):
        if i + window + 1 < y_true.shape[0]:
            smape_val = smape(y_true[i: i + window], y_pred[i: i + window])
            sc_val = sc(y_true[i : i + window])
            smape_vs_sc_all_windows.append([smape_val, sc_val])

    return np.asarray(smape_vs_sc_all_windows)


def sc_mse(y_pred, y_true):
    sc_y_true = torch.sum(torch.abs(y_true[:,:,1:] - y_true[:,:,:-1]), dim=2)
    mse = torch.mean((y_pred - y_true) ** 2.0, dim=2)
    loss = sc_y_true * mse
    loss = torch.mean(loss)
    return loss

def mirror(reference, simulated):
    if simulated.min() < 0:
        return abs(reference), abs(simulated)
    return reference, simualted

def get_ramp(reference):
    ramp_start = np.argmin(reference == reference.min())
    ramp_end = np.argmax(reference)
    return ramp_start, ramp_end

def response_time_2perc(reference, simulated, time):
    #when is the simulated quantity 2% of the nominal reference quantity.
    start, end = get_ramp(reference)
    perc2_time = time[start + np.argmax(simulated[start:] >=\
                        0.02 * reference.max())] - time[start]
    return perc2_time

def response_time_95perc(reference, simulated, time):
    #when is the simulated quantity 95% between 105% of the nominal reference
    # quantity and remains with 95% and 105% for test 2 it is 1.025
    start, end = get_ramp(reference)
    perc2_time = time[start + np.argmax(simulated[start:] >= \
                    0.995 * reference.max())] - time[start]
    return perc2_time

def following_error(reference, simulated):
    #error between refernece and simulated when reference is 0.5 of of the nominal
    start, end = get_ramp(reference)
    following_indx = start + np.argmax(reference[start:end] >= \
                        0.5 * (reference.max()-reference.min()))
    return reference[following_indx] - simulated[following_indx]

def stead_state_error(reference, simulated):
    #error between reference and simulated when simulated has stablised after overshoot
    pass

def overshoot(reference, simulated):
    #value of simulated at ramp overshoot
    start, end = get_ramp(reference)
    overshoot_idx = end + np.argmax(abs(reference[end:-1] - simulated[end:-1]))
    return 100 * (simulated[overshoot_idx] - reference[overshoot_idx]) / \
                (reference.max() - reference.min())

def max_torque_acceleration(simulated):
    #maximum value of torque when speed ramp occurs
    return np.max(simulated)

def speed_drop(reference, simulated):
    #minimum value of speed when torque ramp occurs
    pass

def setting_time(reference, simulated):
    #When simulated speed value is back to 0.005 of reference speed value
    pass

def speed_drop_area(reference, simulated):
    #area of speed when drop occurs
    pass


test = sio.loadmat('../mat_sim/test2.mat')
print (test.keys())
sim_speed = test['Speed']
ref_speed = test['RefSpeed']
sim_torque = test['Torque']
ref_torque = test['RefLoad']
time = test['t']

#mirror is not the correct solution
ref_speed, sim_speed = mirror(ref_speed, sim_speed)
ref_torque, sim_torque = mirror(ref_torque, sim_torque)

print (response_time_2perc(ref_speed, sim_speed, time))
print (response_time_95perc(ref_speed, sim_speed, time))
print (following_error(ref_speed, sim_speed))
print (overshoot(ref_speed, sim_speed))
print (max_torque_acceleration(sim_torque))
