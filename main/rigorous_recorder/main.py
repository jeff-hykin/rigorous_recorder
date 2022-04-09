from time import time as now

from super_hash import super_hash
from super_map import Map, LazyDict

# TODO:
    # change the RecordKeeper file_path to an ID, and have the collection use an ID

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
            raise Exception('for AncestorDict(), ancestors needs to be a dict')
        if itself != None and type(self.itself) != dict:
            raise Exception('for AncestorDict(), itself needs to be a pure dict')
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

class RecordKeeper():
    def __init__(self, *args, **kwargs):
        """
        Examples:
            RecordKeeper()
            RecordKeeper({"key_of_data": "value"})
            RecordKeeper(key_of_data="value)
            RecordKeeper({}, parent_record_keeper)
        """
        # properties (each are updated below)
        self.local_data         = LazyDict()
        self.sub_record_keepers = []
        self.local_records      = []
        self.parent             = None
        self.pending_record     = AncestorDict(ancestors=tuple()) 
        
        # load local data
        if len(args) == 1:
            first_arg = args[0]
            if isinstance(first_arg, dict):
                self.local_data = LazyDict(first_arg)
            else:
                raise Exception(f'''\n\ncalled RecordKeeper(data)\nbut data was: {first_arg}\nwhich was not a dict (and this object only works if it is)\n''')
        
        self.local_data.update(kwargs)
        
        # these will be set menually when theyre used
        self.collection = None
        self.file_path  = None
    
    def set_parent(self, parent):
        self.parent = parent
        self.pending_record = AncestorDict(ancestors=self.local_data_lineage, itself=dict(self.pending_record.itself))
        # attach self to parent
        self.parent.sub_record_keepers.append(self)
        self.collection = self.parent.collection
        self.file_path  = self.parent.file_path
        
        return self
    
    def local_data_lineage_generator(self):
        yield self.local_data
        next_keeper = self
        while isinstance(next_keeper.parent, RecordKeeper):
            yield next_keeper.parent.local_data
            next_keeper = next_keeper.parent
    
    @property
    def local_data_lineage(self):
        return tuple(self.local_data_lineage_generator())
    
    @property
    def records(self):
        if self.collection is None:
            return self.local_records
        else:
            # look through all the records, even if they weren't generated in this runtime/session
            def generator():
                for each_record in self.collection.records:
                    # if this record was apart of a record, then report it
                    if self.local_data in each_record.ancestors:
                        yield each_record
            return generator()
    
    def push(self, *args, **kwargs):
        data = {}
        if len(args) > 0:
            data = args[0]
        data.update(kwargs)
        self.commit(additional_info=data)
        return self

    def add(self, *args, **kwargs):
        data = {}
        if len(args) > 0:
            data = args[0]
        data.update(kwargs)
        self.pending_record.update(data)
        return self
    

    def commit(self,*, additional_info=None):
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
    
    def swap_out(self, old_record_keeper, new_record_keeper):
        next_keeper = self
        while isinstance(next_keeper.parent, RecordKeeper):
            if id(next_keeper.parent) == id(old_record_keeper):
                next_keeper.parent = new_record_keeper
                return True
            # TODO: add infinte loop check (like if next_keeper.parent == next_keeper) 
            next_keeper = next_keeper.parent
    
    @property
    def number_of_records(self):
        return len(self)
    
    def SubRecordKeeper(self, **kwargs):
        return RecordKeeper(kwargs).set_parent(self)
    
    def __iter__(self):
        return self.records()
    
    def __len__(self):
        if self.collection is None:
            return len(self.local_records)
        else:
            # apparently this is the fastest way (no idea why converting to tuple is faster than using reduce)
            return len(tuple(self.records()))
    
    def __hash__(self):
        return super_hash({ RecordKeeper: self.local_data })
        
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
        for each_key, each_value in self.parent.items():
            parent_data += f'\n        "{each_key}":' + indent(
                attempt(lambda: json.dumps(each_value, indent=4), default=f"{each_value}")
            )
        parent_data += "\n    }"
        
        return f"""{'{'}\n    number_of_records: {size},\n    records: [ ... ],\n    local_data: {representer},\n    parent_data:{parent_data}\n{'}'}"""
    
    def __getitem__(self, key):
        # numerical acts like array of local records 
        if isinstance(key, (int, slice)):
            return self.local_records[key]
        # all else acts like dict of local data
        else:
            return self.local_data[key]
    
    def __setitem__(self, key, value):
        # numerical acts like array of local records 
        if isinstance(key, (int, slice)):
            self.local_records[key] = value
        # all else acts like dict of local data
        else:
            self.local_data[key] = value
    
    def get(self, key, default=None):
        # numerical acts like array of local records 
        if isinstance(key, (int, slice)):
            try:
                return self.local_records[key]
            except Exception as error:
                return default
        # all else acts like dict of local data
        else:
            if key in self.local_data:
                return self.local_data[key]
            else:
                return default
    
    def items(self, *args, **kwargs):
        return self.local_data.items(*args, **kwargs)
    
    def keys(self, *args, **kwargs):
        return self.local_data.keys(*args, **kwargs)
    
    def values(self, *args, **kwargs):
        return self.local_data.values(*args, **kwargs)
    
    def __getstate__(self):
        return (self.parent, self.local_data, self.file_path, self.sub_record_keepers, self.pending_record, self.local_records)
    
    def __setstate__(self, state):
        self.parent, self.local_data, self.file_path, self.sub_record_keepers, self.pending_record, self.local_records = state
        # collection can't be saved because then each record keeper would have link to all other record keepers, not just sub_record_keepers
        # so its loaded based on the file path
        self.collection = None
        if self.file_path is not None:
            # collection corrisponding to the file path, if it exists
            # this is global var because of python pickling
            # this re-attaches self.collection to the collection (which avoids pickling/unpickling the whole collection)
            self.collection = globals().get("_ExperimentCollection_register",{}).get(self.file_path, None)
            # TODO: there should be a requect for nanyak reconnection  if this fails

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
                model_1_losses.commit()
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
        self.file_path                    = file_path+extension
        self.collection_name              = ""
        self.experiment_info_keeper       = None
        self.experiment_keeper            = None
        self.prev_experiment_local_data   = None
        self._records                     = records or []
        self.collection_keeper            = RecordKeeper({})
        # attache the collection_keeper to the collection (making it kind of special)
        self.collection_keeper.collection = self
        self.collection_keeper.file_path  = self.file_path
        
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
        # NOTE: this could cause problems when moving the collection
        # TODO: look into the "dill" package as a possible alternative, or just create a
        register = globals()["_ExperimentCollection_register"] = globals().get("_ExperimentCollection_register", {})
        register[self.file_path] = self
        
        self.prev_experiment_local_data = self.prev_experiment_local_data or dict(experiment_number=0, error_number=0, had_error=False)
        if not self._records and self.file_path:
            if os.path.isfile(self.file_path):
                self.collection_keeper.local_data, self.prev_experiment_local_data, self._records = large_pickle_load(self.file_path)
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
            
            
            # 
            # save to file
            # 
            # ensure folder exists
            import os;os.makedirs(os.path.dirname(self.file_path), exist_ok=True)
            self.prev_experiment_local_data = self.experiment_keeper.local_data
            data = (self.collection_keeper.local_data, self.experiment_keeper.local_data, self._records)
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
    
