# What is this?

I needed an efficient data logger for my machine learning experiments that I could easily query. Specifically, I needed to do cross-experiment comparisions
- in a modular hierarchical way (not one big global logging variable)
- but still having a flat table-like structure for performing queries/summaries
- without having tons of duplicated data

This library would work well with PySpark

# What is a usecase example?

Lets say you're going to perform
- 3 experiments
- each experiment has 10 episodes
- each episode has 100,000 timesteps
- there is an an `x` and `y` value at each timestep <br>

#### Example goal:
- We want to get the average `x` value across all timesteps in episode 2 (I don't care what experiment they're from)


Our timestamp data could look like:
```python
record1 = { "x":1, "y":1 } # first timestep
record2 = { "x":2, "y":2 } # second timestep
record3 = { "x":3, "y":3 } # third timestep
```

#### Problem
Those records don't contain the experiment number or the episode number (which we need for our goal)

#### Bad Solution

Duplicating the data would provide a flat structure, but (for 100,000 timesteps) thats a huge memory cost
```python
record1 = { "x":1, "y":1, "episode":1, "experiment": 1, } # first timestep
record2 = { "x":2, "y":2, "episode":1, "experiment": 1, } # second timestep
record3 = { "x":3, "y":3, "episode":1, "experiment": 1, } # third timestep
```

#### Good-ish Solution

We can use references to both be more efficient, and allow editing data after the fact

```python
# parent data
experiment_data = { "experiment": 1 }
episode_data    = { "episode":1, }

record1 = { "x":1, "y":1, "parents": [experiment_data, episode_data] } # first timestep
record2 = { "x":2, "y":2, "parents": [experiment_data, episode_data] } # second timestep
record3 = { "x":3, "y":3, "parents": [experiment_data, episode_data] } # third timestep
```

#### How does Rigorous Recorder help?

The "Good-ish Solution" above is still very crude
1. The `RecordKeeper` class in this library provides a much cleaner implmentation.
2. The `ExperimentCollection` class helps a lot saving, handling errors, managing experiments etc 

```python
from rigorous_recorder import RecordKeeper
keeper = RecordKeeper()

# parent data
experiment_keeper = keeper.sub_record_keeper(experiment=1)
episode_keeper    = experiment_keeper.sub_record_keeper(episode=1)

episode_data.add_record({ "x":1, "y":1, }) # timestep1
episode_data.add_record({ "x":2, "y":2, }) # timestep2
episode_data.add_record({ "x":3, "y":3, }) # timestep3
```

# How do I use this?

`pip install rigorous-recorder`

```python
from rigorous_recorder import RecordKeeper, ExperimentCollection

from statistics import mean as average
from random import random, sample, choices

collection = ExperimentCollection("records/my_study") # <- this string is a filepath 

# automatically increments from the previous experiment number
# data is saved to disk automatically, even when an error is thrown
# running again (after error) won't double-increment the experiment number (same number until non-error run is achieved)
with collection.new_experiment() as record_keeper:
    model1 = record_keeper.sub_record_keeper(model="model1")
    model2 = record_keeper.sub_record_keeper(model="model2")
    # splits^ in two different ways (like siblings in a family tree)
    
    # 
    # training
    # 
    model_1_losses = model1.sub_record_keeper(training=True)
    model_2_losses = model2.sub_record_keeper(training=True)
    for each_index in range(1000):
        # one approach
        model_2_losses.add_record(
            index=each_index,
            loss=random(),
        )
        
        # alternative approach (same outcome)
        # - this way is very handy for adding data in one class method (loss func)
        #   while calling commit_record in a different class method (update weights)
        model_1_losses.pending_record["index"] = each_index
        model_1_losses.pending_record["loss"] = random()
        model_1_losses.commit_record()
    # 
    # testing
    # 
    model_1_evaluation = model1.sub_record_keeper(testing=True)
    model_2_evaluation = model2.sub_record_keeper(testing=True)
    for each_index in range(1000):
        # one method
        model_2_losses.add_record(
            index=each_index,
            loss=random(),
        )
        
        # alternative way (same outcome)
        # - very handy for adding data in a class method
        #   while calling commit_record in a different class method
        model_1_losses.pending_record["index"] = each_index
        model_1_losses.pending_record["loss_1"] = random()
        model_1_losses.commit_record()


# 
# 
# Analysis
# 
# 

all_records = collection.records
print(all_records[0]) # prints first record, which behaves just like a regular dictionary

# first 500 training records (from both models)
records_first_half_of_time = tuple(each for each in all_records if each["training"] and each["index"] < 500)
# not a great example, but this wouldn't care if the loss was from model1 or model 2
first_half_average_loss = average(tuple(each["loss"] for each in records_first_half_of_time))
# only for model 1
model_1_first_half_loss = average(tuple(each["loss"] for each in records_first_half_of_time if each["model"] == "model1"))
# only for model 2
model_1_first_half_loss = average(tuple(each["loss"] for each in records_first_half_of_time if each["model"] == "model2"))
```

# What are some other details?

The `ExperimentCollection` adds 6 keys as a parent to every record:
```
experiment_number     # int
error_number          # int, is only incremented for back-to-back error runs
had_error             # boolean for easy filtering
experiment_start_time # the output of time.time() from python's time module
experiment_end_time   # the output of time.time() from python's time module
experiment_duration   # the difference between start and end (for easy graphing/filtering)
```