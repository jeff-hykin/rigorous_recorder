#!/usr/bin/env python3
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
        model_2_losses.add_record({
            "index": each_index,
            "loss": random(),
        })
        
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
    for each_index in range(50):
        # one method
        model_2_evaluation.add_record({
            "index": each_index,
            "accuracy": random(),
        })
        
        # alternative way (same outcome)
        model_1_evaluation.pending_record["index"] = each_index
        model_1_evaluation.pending_record["accuracy"] = random()
        model_1_evaluation.commit_record()


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
model_2_first_half_loss = average(tuple(each["loss"] for each in records_first_half_of_time if each["model"] == "model2"))