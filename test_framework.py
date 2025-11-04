import pandas as pd
import numpy as np
from dsipts import TimeSeries, RNN,read_public_dataset, LinearTS, Persistent
import matplotlib.pyplot as plt
from datetime import timedelta
import logging
import sys
import os

# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logging.debug("info")

# get current folder
current_folder = os.getcwd()
data_path = os.path.join(current_folder, 'data')

#read a public dataset
data, columns = read_public_dataset(data_path, 'weather')

use_covariates = False  #use only y
use_future_covariate = True #suppose to have some future covariates

##load the timeseries to the datastructure, adding the hour column and use all the covariates
ts = TimeSeries('weather')
ts.load_signal( data,enrich_cat=['hour'],target_variables=['y'],past_variables=columns if use_covariates else [], future_variables=columns if use_future_covariate else [] )
