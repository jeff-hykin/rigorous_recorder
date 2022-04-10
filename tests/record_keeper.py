#!/usr/bin/env python3
from rigorous_recorder import RecordKeeper
from random import random, sample, choices
keeper = RecordKeeper()

# parent data
experiment_keeper = RecordKeeper(experiment=1).set_parent(keeper)
episode_keeper    = RecordKeeper(episode=1).set_parent(experiment_keeper)

episode_keeper.push(x=1, y=1) # timestep1
episode_keeper.push(x=2, y=2) # timestep2
episode_keeper.push(x=3, y=3) # timestep3

episode_keeper.add(accuracy=random(), index=each_index)
episode_keeper.commit()