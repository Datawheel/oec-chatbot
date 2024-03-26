from langchain_core.callbacks.base import BaseCallbackHandler
from typing import Any, Dict, List, Union


class logsHandler(BaseCallbackHandler):

    def __init__(self, outFile = [], print_logs = False, print_starts = True, print_ends = True, print_errors = True, **kwargs):
        super()
        self.tracer = {}
        self.outFile = outFile
        self.print_logs = print_logs
        self.start = print_starts
        self.ends = print_ends
        self.errors = print_errors
    
    def log_to_file(self, event):
        self.outFile.append(event)
        with open('./log.txt','a') as log:
            log.write(str(event))

    def parent_tracking(self, node):
        trace = []
        current_node = self.tracer[node]
        while current_node['parent_run_id']:
            trace.append(current_node['name'])
            current_node = self.tracer[current_node['parent_run_id']]
        trace.append(current_node['name'])
        trace.reverse()
        return '>'.join(trace)

    # chain
    def on_chain_start(self, serialized, inputs, run_id, **kwargs):
        #print( 'Entering new chain {}'.format(kwargs.keys()))
        name = str(kwargs['name']) if 'name' in kwargs.keys() else ''

        formatted_response = {
            'type': 'Chain start',
            'names_tags': name +':'+ ','.join(kwargs['tags']),
            'input': inputs
        }
        self.tracer[run_id] = {'parent_run_id': kwargs['parent_run_id'],'name': name}
        _track = self.parent_tracking(run_id)
        _id = name +':'+ ','.join(kwargs['tags'])
        #_serie = serialized['name']
        if self.print_logs and self.start:
            print( f'Entering new chain[{_track}]: {_id} ')
            self.log_to_file(formatted_response)

    
    def on_chain_end(self, outputs, run_id, **kwargs):
        if self.tracer[run_id]['name'] == 'PromptTemplate':
            outputs = 'Template'

        formatted_response = {
            'type': 'Chain end',
            'output': outputs
        }
        _track = self.parent_tracking(run_id)
        if self.print_logs and self.ends: 
            print(f'Finish chain[{_track}]:  {outputs}')
            self.log_to_file(formatted_response)

    
    def on_chain_error(self, error, run_id,**kwargs):
        formatted_response = {
            'type': 'Chain error',
            'error': error,
            'tags': kwargs['tags']
        }
        _track = self.parent_tracking(run_id)
        if self.print_logs and self.errors: 
            print(f'Error chain [{_track}]:  {error} ')
            self.log_to_file(formatted_response)


    # llms
    def on_llm_start(self, serialized, prompts, run_id, **kwargs):  
        formatted_response = {
            'type':'LLM start',
            'name': str(kwargs['name']) + ':' + str(serialized['name']),
            'prompts': prompts
        }
        self.tracer[run_id] = {'parent_run_id': kwargs['parent_run_id'],'name': kwargs['name']}
        _serie = serialized['name']
        _kwargs = kwargs['name']
        if self.print_logs and self.start: 
            print(f'Starting llm:  {_serie} {_kwargs} ')
            self.log_to_file(formatted_response)

    
    def on_llm_end(self, response, **kwargs):
        basis_response = response.generations[0][0]
        formatted_response = {
            'type': 'LLM end',
            'output':basis_response.text,
            'duration':basis_response.generation_info['total_duration']/1e+9,
            'tkn_cnt':basis_response.generation_info['eval_count'],
        }
        metric = (basis_response.generation_info['total_duration'])/1e+9
        out = basis_response.text
        if self.print_logs and self.ends: 
            print(f'Finish llm[t:{metric}]: {out}')
            self.log_to_file(formatted_response)

      
    def on_llm_error(self, error, **kwargs):
        formatted_response = {
            'type': 'LLM error',
            'error': error
        }
        if self.print_logs and self.errors: 
            print(f'Error llm:  {error}')
            self.log_to_file(formatted_response) 
