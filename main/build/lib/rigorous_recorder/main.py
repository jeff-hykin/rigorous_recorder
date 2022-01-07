from time import time as now

from super_hash import super_hash

# 
# helpers
# 
def large_pickle_load(file_path):
    """
    This is for loading really big python objects from pickle files
    ~4Gb max value
    """
    import pickle
    import os
    max_bytes = 2**31 - 1
    bytes_in = bytearray(0)
    input_size = os.path.getsize(file_path)
    with open(file_path, 'rb') as f_in:
        for _ in range(0, input_size, max_bytes):
            bytes_in += f_in.read(max_bytes)
    output = pickle.loads(bytes_in)
    return output

def large_pickle_save(variable, file_path):
    """
    This is for saving really big python objects into a file
    so that they can be loaded in later
    ~4Gb max value
    """
    import pickle
    bytes_out = pickle.dumps(variable, protocol=4)
    max_bytes = 2**31 - 1
    with open(file_path, 'wb') as f_out:
        for idx in range(0, len(bytes_out), max_bytes):
            f_out.write(bytes_out[idx:idx+max_bytes])

# save loading times without brittle code
def attempt(a_lambda, default=None, expected_errors=(Exception,)):
    try:
        return a_lambda()
    except expected_errors:
        return default

def indent(string):
    return string.replace("\n", "\n    ")

# 
# 
# Main code
# 
# 
class AncestorDict(dict):
    def __init__(self, *, ancestors, itself=None):
        self.ancestors = ancestors
        if not isinstance(self.ancestors, (list, tuple)):
            raise Exception('for self_custom_inherit(), ancestors needs to be a dict')
        if itself != None and type(self.itself) != dict:
            raise Exception('for self_custom_inherit(), itself needs to be a pure dict')
        self.itself = itself or {}
    
    @property
    def lineage(self):
        yield self.itself
        for each in self.ancestors:
            yield each
    
    def keys(self):
        self_keys = self.itself.keys()
        for each_key in self_keys:
            yield each_key
        self_keys = set(self_keys)
        for each_parent in self.ancestors:
            for each_key in each_parent.keys():
                if each_key not in self_keys:
                    self_keys.add(each_key)
                    yield each_key
    
    def values(self):
        self_keys = self.itself.keys()
        for each_key, each_value in self.itself.items():
            yield each_value
        self_keys = set(self_keys)
        for each_parent in self.ancestors:
            for each_key, each_value in each_parent.items():
                if each_key not in self_keys:
                    self_keys.add(each_key)
                    yield each_value
    
    def items(self):
        self_keys = self.itself.keys()
        for each_key, each_value in self.itself.items():
            yield (each_key, each_value)
        self_keys = set(self_keys)
        for each_parent in self.ancestors:
            for each_key, each_value in each_parent.items():
                if each_key not in self_keys:
                    self_keys.add(each_key)
                    yield (each_key, each_value)
    
    def __len__(self):
        return len(tuple(self.keys()))
    
    def __iter__(self):
        return (each for each in self.keys())
    
    def __contains__(self, key):
        return any((key in each_person.keys() for each_person in self.lineage))
        
    def __getitem__(self, key):
        for each_person in self.lineage:
            if key in each_person.keys():
                return each_person[key]
        return None
    
    def __setitem__(self, key, value):
        # this happens because of pickling
        if not hasattr(self, "itself"):
            self.itself = {}
        self.itself[key] = value

    def update(self, other):
        self.itself.update(other)
    
    @property
    def compressed(self):
        copy = {}
        for each in reversed(tuple(self.lineage)):
            copy.update(each)
        return copy
    
    def __repr__(self,):
        copy = self.compressed
        import json
        representer = attempt(lambda: json.dumps(self, indent=4), default=copy.__repr__())
        return representer
    
    def get(self,*args,**kwargs):
        return self.compressed.get(*args,**kwargs)
    
    def copy(self,*args,**kwargs):
        return self.compressed.copy(*args,**kwargs)

    def clone(self):
        return AncestorDict(
            ancestors=self.ancestors,
            itself=dict(self.itself),
        )
    
    def __getstate__(self):
        return self.itself, self.ancestors
    
    def __setstate__(self, state):
        self.itself, self.ancestors = state
    
    def __json__(self):
        return self.compressed
    

#%%
class CustomInherit(dict):
    def __init__(self, *, parent, data=None):
        self.parent = parent
        if not isinstance(self.parent, dict):
            raise Exception('for CustomInherit(), parent needs to be a dict')
        if data != None and type(self.data) != dict:
            raise Exception('for CustomInherit(), data needs to be a pure dict')
        self._self = data or {}
    
    @property
    def self(self):
        if not hasattr(self, "_self"):
            self._self = {}
        return self._self
    
    def keys(self):
        self_keys = self.self.keys()
        for each_key in self_keys:
            yield each_key
        self_keys = set(self_keys)
        for each_key in self.parent.keys():
            if each_key not in self_keys:
                yield each_key
    
    def values(self):
        self_keys = self.self.keys()
        for each_key, each_value in self.self.items():
            yield each_value
        self_keys = set(self_keys)
        for each_key, each_value in self.parent.items():
            if each_key not in self_keys:
                yield each_value
    
    def items(self):
        self_keys = self.self.keys()
        for each_key, each_value in self.self.items():
            yield (each_key, each_value)
        self_keys = set(self_keys)
        for each_key, each_value in self.parent.items():
            if each_key not in self_keys:
                yield (each_key, each_value)
    
    @property
    def ancestors(self):
        current = self
        ancestors = []
        while hasattr(current, "parent") and current != current.parent:
            ancestors.append(current.parent)
            current = current.parent
        return ancestors
    
    def __len__(self):
        return len(tuple(self.keys()))
    
    def __iter__(self):
        return (each for each in self.keys())
    
    def __contains__(self, key):
        return key in self.parent or key in self.self
        
    def __getitem__(self, key):
        if key in self.self:
            return self.self[key]
        else:
            return self.parent.get(key, None)
    
    def __setitem__(self, key, value):
        self.self[key] = value

    def update(self, other):
        self.self.update(other)
    
    def __repr__(self,):
        copy = self.parent.copy()
        copy.update(self.self)
        import json
        representer = attempt(lambda: json.dumps(self, indent=4), default=copy.__repr__())
        return representer
    
    def get(self,*args,**kwargs):
        copy = self.parent.copy()
        copy.update(self.self)
        return copy.get(*args,**kwargs)
    
    def copy(self,*args,**kwargs):
        copy = self.parent.copy()
        copy.update(self.self)
        return copy.copy(*args,**kwargs)

    def clone(self):
        new_data = dict(self.self)
        return CustomInherit(
            parent=self.parent,
            data=new_data
        )
    
    def __getstate__(self):
        return {
            "_self": self.self,
            "parent": self.parent,
        }
    
    def __setstate__(self, state):
        self._self = state["_self"]
        self.parent = state["parent"]
    
    def __json__(self):
        copy = self.parent.copy()
        copy.update(self.self)
        return copy
    

class RecordKeeper():
    def __init__(self, parent_record_keeper=None, local_data=None, collection=None, records=None, file_path=None):
        self.parent_record_keeper = parent_record_keeper
        self.local_data           = local_data or {}
        self.file_path            = file_path
        self.sub_record_keepers   = []
        self.pending_record       = AncestorDict(ancestors=self.local_data_lineage,)
        self.collection           = collection
        self.local_records        = records or []
        if not isinstance(self.local_data, dict):
            raise Exception('Parent needs to be a dict')
    
    def local_data_lineage_generator(self):
        yield self.local_data
        next_keeper = self
        while isinstance(next_keeper.parent_record_keeper, RecordKeeper):
            yield next_keeper.parent_record_keeper.local_data
            next_keeper = next_keeper.parent_record_keeper
    
    @property
    def local_data_lineage(self):
        return tuple(self.local_data_lineage_generator())
    
    @property
    def records(self):
        if self.collection is not None:
            return self.collection.records
        else:
            return self.local_records
    
    def add_record(self, record):
        return self.commit_record(additional_info=record)
    
    def swap_out(self, old_record_keeper, new_record_keeper):
        next_keeper = self
        while isinstance(next_keeper.parent_record_keeper, RecordKeeper):
            if id(next_keeper.parent_record_keeper) == id(old_record_keeper):
                next_keeper.parent_record_keeper = new_record_keeper
                return True
            # TODO: add infinte loop check (like if next_keeper.parent_record_keeper == next_keeper) 
            next_keeper = next_keeper.parent_record_keeper
    
    def commit_record(self,*, additional_info=None):
        # finalize the record
        (additional_info is not None) and self.pending_record.update(additional_info)
        # make sure the ancestors are the most up-to-date (swap_out can cause them to change since init)
        local_lineage = self.local_data_lineage
        self.pending_record.ancestors = local_lineage
        # save different depending on if part of a collection or not
        output = self.pending_record
        if self.collection is not None:
            self.collection.add_record(self.pending_record)
        else:
            self.local_records.append(self.pending_record)
        # start a new clean record
        self.pending_record = AncestorDict(ancestors=local_lineage)
        # return the record (AncestorDict) that was just committed
        return output
        
    @property
    def number_of_records(self):
        return len(self)
    
    def sub_record_keeper(self, **kwargs):
        sub_record_keeper = RecordKeeper(
            parent_record_keeper=self,
            local_data=kwargs,
            collection=self.collection,
            records=self.local_records,
            file_path=self.file_path,
        )
        self.sub_record_keepers.append(sub_record_keeper)
        return sub_record_keeper
    
    def __iter__(self):
        return (each for each in self.records if self.local_data in each.ancestors)
    
    def __len__(self):
        # apparently this is the fastest way (no idea why converting to tuple is faster than using reduce)
        return len(tuple((each for each in self)))
    
    def __hash__(self):
        return super_hash({ "CustomInherit": self.local_data })
        
    def __repr__(self):
        size = len(self)
        import json
        # fallback case first
        representer = attempt(lambda: indent(representer.__repr__()), default=self.local_data)
        # ideal case
        representer = attempt(lambda: indent(json.dumps(self.local_data, indent=4)), default=representer)
        # parent data
        all_parents = []
        parent_data = "    {"
        for each_key, each_value in self.parent_record_keeper.items():
            parent_data += f'\n        "{each_key}":' + indent(
                attempt(lambda: json.dumps(each_value, indent=4), default=f"{each_value}")
            )
        parent_data += "\n    }"
        
        return f"""{'{'}\n    number_of_records: {size},\n    records: [ ... ],\n    local_data: {representer},\n    parent_data:{parent_data}\n{'}'}"""
    
    def __getitem__(self, key):
        return self.pending_record[key]
    
    def __setitem__(self, key, value):
        self.local_data[key] = value
    
    def __getattr__(self, key):
        return self[key]
    
    def copy(self,*args,**kwargs):
        return self.pending_record.copy(*args,**kwargs)
    
    def items(self, *args, **kwargs):
        return self.pending_record.items(*args, **kwargs)
    
    def keys(self, *args, **kwargs):
        return self.pending_record.keys(*args, **kwargs)
    
    def values(self, *args, **kwargs):
        return self.pending_record.values(*args, **kwargs)
    
    def __getstate__(self):
        return (self.parent_record_keeper, self.local_data, self.file_path, self.kids, self.pending_record, self.local_records)
    
    def __setstate__(self, state):
        self.parent_record_keeper, self.local_data, self.file_path, self.kids, self.pending_record, self.local_records = state
        self.collection = None
        if self.file_path is not None:
            self.collection = globals().get("_ExperimentCollection_register",{}).get(self.file_path, None)
        if not isinstance(self.local_data, dict):
            raise Exception('local_data needs to be a dict')

class Experiment(object):
    def __init__(self, experiment_info_keeper, save_experiment):
        self.experiment_info_keeper = experiment_info_keeper
        self.save_experiment        = save_experiment
    
    def __enter__(self):
        return self.experiment_info_keeper
    
    def __exit__(self, _, error, traceback):
        self.save_experiment(_, error, traceback)

class ExperimentCollection:
    """
    Example:
        collection = ExperimentCollection("test1") # filepath 
        with collection.new_experiment() as record_keeper:
            model1 = record_keeper.sub_record_keeper(model="model1")
            model2 = record_keeper.sub_record_keeper(model="model2")
            model_1_losses = model1.sub_record_keeper(training=True)
            from random import random, sample, choices
            for each in range(1000):
                model_1_losses.pending_record["index"] = each
                model_1_losses.pending_record["loss_1"] = random()
                model_1_losses.commit_record()
    Note:
        the top most record keeper will be automatically be given these values:
        - experiment_number
        - error_number
        - had_error
        - experiment_start_time
        - experiment_end_time
        - experiment_duration
    """
    
    # TODO: make it so that Experiments uses database with detached/reattached pickled objects instead of a single pickle file
    
    def __init__(self, file_path, records=None, extension=".pickle"):
        self.file_path              = file_path+extension
        self.experiment_info_keeper = None
        self.collection_name        = ""
        self.experiment_keeper      = None
        self._records               = records or []
        self.record_keepers         = {}
        self.prev_experiment_local_data = None
        self.collection_keeper      = RecordKeeper(
            parent_record_keeper=None,
            local_data={},
            collection=self,
            records=self._records,
            file_path=self.file_path,
        )
        
        import os
        self.file_path = os.path.abspath(self.file_path)
        self.collection_name = os.path.basename(self.file_path)[0:-len(extension)]
    
    def load(self):
        # 
        # load from file
        # 
        import os
        
        # when a record_keeper is seralized, it shouldn't contain a copy of the experiment collection and every single record
        # it really just needs its parents/children
        # however, it still needs a refernce to the experiment_collection to get access to all the records
        # so this register is used as a way for it to reconnect, based on the file_path of the collection
        register = globals()["_ExperimentCollection_register"] = globals().get("_ExperimentCollection_register", {})
        register[self.file_path] = self
        
        self.prev_experiment_local_data = self.prev_experiment_local_data or dict(experiment_number=0, error_number=0, had_error=False)
        if not self._records and self.file_path:
            if os.path.isfile(self.file_path):
                self.collection_keeper.local_data, self.prev_experiment_local_data, self.record_keepers, self._records = large_pickle_load(self.file_path)
            else:
                print(f'Will create new experiment collection: {self.collection_name}')
    
    def ensure_loaded(self):
        if self.prev_experiment_local_data == None:
            self.load()
    
    @property
    def experiment_numbers(self):
        experiment_numbers = set()
        for each in self.records:
            experiment_numbers.add(each.get("experiment_number", None))
        return tuple(experiment_numbers)
        
    def __getitem__(self, key):
        self.ensure_loaded()
        experiment_numbers = self.experiment_numbers
        if key < 0:
            key = experiment_numbers[key]
        if key not in experiment_numbers:
            return []
        return tuple(each for each in self._records if each.get("experiment_number",None) == key)
    
    def add_record(self, record):
        self.ensure_loaded()
        self._records.append(record)
    
    def new_experiment(self, **experiment_info):
        # 
        # load from file
        # 
        self.ensure_loaded()
        
        # add basic data to the experiment
        # there are 3 levels:
        # - self.collection_keeper.local_data (root)
        # - self.experiment_keeper
        # - self.experiment_info_keeper
        self.experiment_keeper = self.collection_keeper.sub_record_keeper(
            experiment_number=self.prev_experiment_local_data["experiment_number"] + 1 if not self.prev_experiment_local_data["had_error"] else self.prev_experiment_local_data["experiment_number"],
            error_number=self.prev_experiment_local_data["error_number"]+1,
            had_error=True,
            experiment_start_time=now(),
        )
        # create experiment record keeper
        if len(experiment_info) == 0:
            self.experiment_info_keeper = self.experiment_keeper
        else:
            self.experiment_info_keeper = self.experiment_keeper.sub_record_keeper(**experiment_info)
        
        def save_experiment(_, error, traceback):
            # mutate the root one based on having an error or not
            no_error = error is None
            experiment_info = self.experiment_keeper.local_data
            experiment_info["experiment_end_time"] = now()
            experiment_info["experiment_duration"] = experiment_info["experiment_end_time"] - experiment_info["experiment_start_time"]
            if no_error:
                experiment_info["had_error"] = False
                experiment_info["error_number"] = 0
            
            # refresh the all_record_keepers dict
            # especially after mutating the self.experiment_keeper.local_data
            # (this ends up acting like a set, but keys are based on mutable values)
            self.record_keepers = { super_hash(each_value) : each_value for each_value in self.record_keepers.values() }
            
            # 
            # save to file
            # 
            # ensure folder exists
            import os;os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            self.prev_experiment_local_data = self.experiment_keeper.local_data
            data = (self.collection_keeper.local_data, self.experiment_keeper.local_data, self.record_keepers, self._records)
            # update self encase multiple experiments are run without re-reading the file
            print("Saving "+str(len(self._records))+" records")
            large_pickle_save(data, self.file_path)
            print("Records saved to: " + self.file_path)
            
            # re-throw the error
            if not no_error:
                print(f'There was an error when running an experiment. Experiment collection: "{self.collection_name}"')
                print(f'However, the partial experiment data was saved')
                experiment_number = self.experiment_keeper.local_data["experiment_number"]
                error_number = self.experiment_keeper.local_data["error_number"]
                import traceback
                print(f'This happend on:\n    dict(experiment_number={experiment_number}, error_number={error_number})')
                print(traceback.format_exc())
                raise error
        
        return Experiment(
            experiment_info_keeper=self.experiment_info_keeper,
            save_experiment=save_experiment
        )
    
    def __len__(self,):
        self.ensure_loaded()
        return len(self._records)
    
    @property
    def records(self):
        self.ensure_loaded()
        return self._records
    
    def add_notes(self, notes, records=None, extension=".pickle"):
        import os
        file_path = os.path.abspath(collection+extension)
        collection_name = os.path.basename(file_path)[0:-len(extension)]
        # default values
        collection_keeper_local_data = {}
        prev_experiment_parent_info = dict(experiment_number=0, error_number=0, had_error=False)
        record_keepers = {}
        records = records or []
        # attempt load
        try: collection_keeper_local_data, prev_experiment_parent_info, record_keepers, records = large_pickle_load(file_path)
        except: print(f'Will creaete new experiment collection: {collection_name}')
        # merge data
        collection_keeper_local_data.update(notes)
        # save updated data
        data = (collection_keeper_local_data, prev_experiment_parent_info, record_keepers, records)
        large_pickle_save(data, file_path)
