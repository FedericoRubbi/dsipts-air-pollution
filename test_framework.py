import pandas as pd
import numpy as np
from dsipts import TimeSeries, RNN, read_public_dataset, LinearTS, Persistent
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
data_path = os.path.join(current_folder, "data")
models_dir = os.path.join(current_folder, "models")


def process_data(df):
    # Columns such as Veneto_MA_18_max_lon raise a mixed type DTypeWarning. They are not needed, so we drop them.
    keep_col = df.columns[
        (df.columns.str.endswith("min_lon") == False)
        & (df.columns.str.endswith("max_lon") == False)
        & (df.columns.str.endswith("min_lat") == False)
        & (df.columns.str.endswith("max_lat") == False)
        & (df.columns.str.endswith("misura") == False)
    ]
    df = df[keep_col]
    df.drop(
        [
            "Nazione",
            "Comune",
            "StazioneMeteo",
            "Latitudine",
            "Longitudine",
            "Inquinante",
        ],
        axis=1,
        inplace=True,
    )
    df.rename(columns=({"Data": "time"}), inplace=True)
    df.time = pd.to_datetime(df.time, format="%Y-%m-%d")

    # Aggregate data grouping by Stazione column
    df = df.groupby(["time", "Stazione"], as_index=False).mean()

    return df


def load_ts(data):
    use_covariates = False  # use only y
    use_future_covariate = True  # suppose to have some future covariates

    ##load the timeseries to the datastructure, adding the hour column and use all the covariates
    # Fix: Exclude categorical columns from numerical variables to avoid StandardScaler error
    ts = TimeSeries("PM10")

    # Exclude categorical columns from numerical variables
    numerical_cols = data.columns.drop("Stazione") if use_covariates else []

    ts.load_signal(
        data,
        target_variables=["Valore"],  # PM10 value
        past_variables=numerical_cols,
        future_variables=numerical_cols if use_future_covariate else [],
        cat_past_var=["Stazione"],
        cat_fut_var=["Stazione"],
        group="Stazione",
    )

    # ts.plot()
    return ts


def fit_rnn(ts):
    # RNN
    past_steps = 4
    future_steps = 8
    config = dict(
        model_configs=dict(
            past_steps=past_steps,  # TASK DEPENDENT
            future_steps=future_steps,  # TASK DEPENDENT
            emb_dim=8,  # categorical stuff
            use_classical_positional_encoder=True,  # categorical stuff
            reduction_mode="mean",  # categorical stuff
            kind="gru",  # model dependent
            hidden_RNN=12,  # model dependent
            num_layers_RNN=2,  # model dependent
            kernel_size=15,  # model dependent
            dropout_rate=0.5,  # model dependent
            remove_last=True,  # model dependent
            use_bn=False,  # model dependent
            activation="torch.nn.PReLU",  # model dependent
            quantiles=[0.1, 0.5, 0.9],  # LOSS
            persistence_weight=0.010,  # LOSS
            loss_type="l1",  # LOSS
            optim="torch.optim.Adam",  # OPTIMIZER
            past_channels=len(
                ts.past_variables
            ),  # parameter that depends on the ts dataset
            future_channels=len(
                ts.future_variables
            ),  # parameter that depends on the ts dataset
            embs_past=[
                ts.dataset[c].nunique() for c in ts.cat_past_var
            ],  # parameter that depends on the ts dataset
            embs_fut=[
                ts.dataset[c].nunique() for c in ts.cat_fut_var
            ],  # parameter that depends on the ts dataset
            out_channels=len(ts.target_variables),
        ),  # parameter that depends on the ts dataset
        scheduler_config=dict(gamma=0.1, step_size=100),
        optim_config=dict(lr=0.0005, weight_decay=0.01),
    )

    model_rnn = RNN(
        **config["model_configs"],
        optim_config=config["optim_config"],
        scheduler_config=config["scheduler_config"],
        verbose=True,
    )

    ts.set_model(model_rnn, config=config)

    ##splitting parameters
    split_params = {
        "perc_train": 0.7,
        "perc_valid": 0.1,  ##if not None it will split 70% 10% 20%
        "range_train": None,
        "range_validation": None,
        "range_test": None,  ## or we can split using ranges for example range_train=['2021-02-03','2022-04-08']
        "past_steps": past_steps,
        "future_steps": future_steps,
        "starting_point": None,  ## do not skip samples
        "skip_step": 1,  ## distance between two consecutive samples
    }

    # train the model for 50 epochs with auto_lr_find
    if True:
        ts.train_model(
            dirpath=f"{models_dir}/RNN",
            split_params=split_params,
            batch_size=128,
            num_workers=4,
            max_epochs=5,
            gradient_clip_val=0.0,
            gradient_clip_algorithm="value",
            precision="bf16",
            auto_lr_find=True,
        )
        # Print the losses, check overfitting
        ts.save(f"PM10_RNN")


def load_rnn(ts):
    ts.load(RNN,f"PM10_RNN",load_last=True)
    return ts

def test_rnn(ts):
    res = ts.inference_on_set(200,4,set='test',rescaling=True)
    return res


def main():
    # read a public dataset
    data = pd.read_csv(os.path.join(data_path, "merged_appa_eea.csv"))
    data = process_data(data)
    ts = load_ts(data)
    # fit_rnn(ts)
    load_rnn(ts)

    res = test_rnn(ts)
    print(res)
    breakpoint()

if __name__ == "__main__":
    main()
