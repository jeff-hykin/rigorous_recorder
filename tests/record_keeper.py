from rigorous_recorder import RecordKeeper
keeper = RecordKeeper()

# parent data
experiment_keeper = keeper.sub_record_keeper(experiment=1)
episode_keeper    = experiment_keeper.sub_record_keeper(episode=1)

episode_keeper.add_record({ "x":1, "y":1, }) # timestep1
episode_keeper.add_record({ "x":2, "y":2, }) # timestep2
episode_keeper.add_record({ "x":3, "y":3, }) # timestep3