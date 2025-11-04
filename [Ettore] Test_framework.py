import os
import sys
import torch
import logging
import numpy as np
import pandas as pd
from datetime import timedelta
import matplotlib.pyplot as plt
from dsipts import TimeSeries, RNN, read_public_dataset, LinearTS, Persistent


# Global parameters
past_steps = 4
future_steps = 8
use_covariates = False  #use only y
use_future_covariate = True # suppose to have some future covariates

# Enable TF32 for matmul and cudnn
torch.backends.cuda.matmul.allow_tf32 = True
torch.backends.cudnn.allow_tf32 = True

# Splitting parameters
split_params = {
    'perc_train': 0.7,
    'perc_valid': 0.1,
    'range_train': None,
    'range_validation': None,
    'range_test': None,
    'past_steps': past_steps,
    'future_steps': future_steps,
    'starting_point': None,
    'skip_step': 1
}

DIR_PATH = "/home/ettore1012/Projects/PublicAI_Ettore/DSIPTS/data/merged_appa_eea.csv"

# logger = logging.getLogger()
# logger.setLevel(logging.DEBUG)
# logging.debug("info")

def process_data(df):
    keep_col = df.columns[
        (df.columns.str.endswith('min_lon')==False) & 
        (df.columns.str.endswith('max_lon')==False) & 
        (df.columns.str.endswith('min_lat')==False) & 
        (df.columns.str.endswith('max_lat')==False) &
        (df.columns.str.endswith('misura')==False)
    ]
    df = df[keep_col]
    df.drop([
        'Nazione', 
        'Comune', 
        'StazioneMeteo', 
        'Latitudine', 
        'Longitudine',
        'Inquinante'
    ], axis=1, inplace=True)
    df.rename(columns = ({'Data':'time'}), inplace=True)
    df.time = pd.to_datetime(df.time, format='%Y-%m-%d')
    variables = df.columns.drop(['Stazione'])
    return df


def train_RNN(ts):
    #train the model for 50 epochs with auto_lr_find 
    ts.train_model(
        dirpath="./models/RNN",
        split_params=split_params,
        batch_size=128,
        num_workers=4,
        max_epochs=5,
        gradient_clip_val=0.0,
        gradient_clip_algorithm='value',
        precision='bf16-mixed',
        auto_lr_find=True
    )
    # Print the losses, check overfitting
    ts.save("PM10_RNN")


def test_RNN(ts):
    """Make inferences on the test set."""
    res = ts.inference_on_set(200, 4, set='test', rescaling=True)
    return res


def plot_results(res, station=None, lag=7):
    """Plot prediction results with confidence bands."""
    plt.figure(figsize=(15, 7))
    
    # Filter data for better visualization
    to_plot = res[res.time > pd.to_datetime('2020-12-28')]
    
    if station:
        to_plot = to_plot[to_plot.Stazione == station]
    lag_data = to_plot[to_plot.lag == lag]
    
    # Plot actual vs predicted values
    plt.plot(lag_data.time, lag_data.Valore, label='real', alpha=0.5)
    plt.plot(lag_data.time, lag_data.Valore_median, label='median', alpha=0.5)
    plt.fill_between(lag_data.time, lag_data.Valore_low, lag_data.Valore_high, 
                     alpha=0.2, label='error band')
    plt.title(f'Prediction on test for lag={lag}')
    plt.legend()
    plt.show()


def get_rnn_config(ts):
    config = dict(
        model_configs=dict(
            # Task dependent
            past_steps=past_steps,
            future_steps=future_steps,
            
            # Categorical embeddings
            emb_dim=8,
            use_classical_positional_encoder=True,
            reduction_mode='mean',
            
            # Model architecture
            kind='gru',
            hidden_RNN=12,
            num_layers_RNN=2,
            kernel_size=15,
            dropout_rate=0.5,
            remove_last=True,
            use_bn=False,
            activation='torch.nn.PReLU',
            
            # Loss configuration
            quantiles=[0.1, 0.5, 0.9],
            persistence_weight=0.010,
            loss_type='l1',
            
            # Optimizer
            optim='torch.optim.Adam',
            
            # Dataset dependent parameters
            past_channels=len(ts.past_variables),
            future_channels=len(ts.future_variables),
            embs_past=[ts.dataset[c].nunique() for c in ts.cat_past_var],
            embs_fut=[ts.dataset[c].nunique() for c in ts.cat_fut_var],
            out_channels=len(ts.target_variables)
        ),
        scheduler_config=dict(gamma=0.1, step_size=100),
        optim_config=dict(lr=0.0005, weight_decay=0.01)
    )
    return config


def fit_RNN(ts):
    # Config dictionary
    config = get_rnn_config(ts)
    model_rnn = RNN(
        **config['model_configs'],
        optim_config=config['optim_config'],
        scheduler_config=config['scheduler_config'],
        verbose=True
    )
    #set the desirere model
    ts.set_model(model_rnn,config=config)
    #train the model
    train_RNN(ts) 
    #test the model
    res= test_RNN(ts)
    # result diagnostic
    plot_results(res, station='Monte Gaza')


def check_cuda():
    if torch.cuda.is_available():
        print("CUDA is available. Device count:", torch.cuda.device_count())
        for device in range(torch.cuda.device_count()):
            print(f"Device {device}: {torch.cuda.get_device_name(device)}")
    else:
        print("CUDA is not available. Please check your installation.")


def load_to_ts(df, ts_name):
    ts = TimeSeries('PM10')
    # Exclude categorical columns from numerical variables
    numerical_cols = df.columns.drop('Stazione') if use_covariates else []
    ts.load_signal(
        df,
        target_variables=['Valore'],  # PM10 value
        past_variables=numerical_cols,
        future_variables=numerical_cols if use_future_covariate else [],
        cat_past_var=['Stazione'],
        cat_fut_var=['Stazione'], 
        group='Stazione'
    )
    return ts


def main():
    # get current folder
    current_folder = os.getcwd()
    data_path = os.path.join(current_folder, 'data')
    # read a dataframe
    df = pd.read_csv(DIR_PATH, low_memory=False)
    # process the dataframe
    df = process_data(df)
    # load the timeseries to the datastructure, adding the hour column and use all the covariates
    ts = load_to_ts(df, ts_name='PM10')
    # check cuda availability
    check_cuda()
    # fit and test RNN model
    fit_RNN(ts)


if __name__ == "__main__":
    main()   
    
