import datetime
from typing import Tuple

import typer

from src.cumulator import generate_cumulations
from src.grabber import download_latest_mrms, load_latest_mrms
from src.graphs import save_figs, generate_map, generate_gif
from src.model import nowcast
from src.system_functions import keep_latest_mrms
from src.tools import timed_nowcast
import time


class Caster:
    def __init__(self, save_path: str, nb_observations: int = 30, nb_forecasts: int = 12, window_size=4, modified_shape = None):
        # Get saving path containing both img and data folder
        self.save_path = save_path
        # Get time
        self.minute = '{:02d}'.format(datetime.datetime.now().minute)
        self.hour = '{:02d}'.format(datetime.datetime.now().hour)
        self.day = '{:02d}'.format(datetime.datetime.now().day)
        self.month = '{:02d}'.format(datetime.datetime.now().month)
        self.year = datetime.datetime.now().year
        # Target url to load mrms from
        self.url = f'https://mtarchive.geol.iastate.edu/{self.year}/{self.month}/{self.day}/mrms/ncep/PrecipRate/'
        # Get the number of observations to download
        self.nb_observations = nb_observations
        # Get the window size
        self.window_size = window_size
        # Get the number of window times ahead
        self.nb_forecasts = nb_forecasts
        # Retrieve shape
        self.modified_shape = modified_shape

    def __call__(self, *args, **kwargs):
        # Download latest mrms data with a number of opservations equal to nb_observations
        download_latest_mrms(self.url, self.save_path, self.nb_observations)
        # Delete the old mrms file and keep only the ones we need
        keep_latest_mrms(self.save_path, self.nb_observations)
        # Load the mrms files
        precip, last_timestep = load_latest_mrms(self.save_path, self.window_size, self.modified_shape)
        # Compute the nowcasting
        excedance, nowcast_linda = nowcast(precip, nb_forecasts=self.nb_forecasts, threshold=1)
        # Build teh graphs
        nowcast_linda = timed_nowcast(nowcast_linda, last_timestep)
        # Generate_cumulation layers
        likelihoods = generate_cumulations(nowcast_linda, self.save_path)
        # Save the fig
        save_figs(likelihoods, self.save_path, self.window_size)
        # Generate the map
        generate_gif(self.save_path)
        generate_map(self.save_path)
        # To github
        save_to_github(
            save_path=self.save_path,
            hour=self.hour,
            minute=self.minute,
            month=self.month,
            day=self.day,
            year=self.year
        )
