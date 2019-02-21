import os
import sys

# def append_to_path(dir0): # A convenience function
#     if dir0 not in sys.path:
#         sys.path.append(dir0)
# append_to_path(os.getcwd()+'/..')
import batcho


def setup_module(module):
    print("setup_module      module:%s" % module.__name__)


def teardown_module(module):
    print("teardown_module   module:%s" % module.__name__)


def setup_function(function):
    print("setup_function    function:%s" % function.__name__)


def teardown_function(function):
    print("teardown_function function:%s" % function.__name__)


def test_batcho_001():
    def cmd1_prepare(job):
        print('preparing job')

    def cmd1_run(job):
        print('testing------------------------------------')
        print(job)
        print('testing------------------------------------')
        return dict(test=3, the_job=job)

    batcho.register_job_command(
        command='cmd1',
        prepare=cmd1_prepare,
        run=cmd1_run
    )

    jobs = [
        dict(command='cmd1', label='job1', name='first_job'),
        dict(command='cmd1', label='job2', name='second_job')
    ]

    batch_name = 'batch1'
    batcho.stop_batch(batch_name=batch_name)
    batcho.set_batch(batch_name=batch_name, jobs=jobs)

    batcho.prepare_batch(batch_name=batch_name, clear_jobs=True)
    batcho.run_batch(batch_name=batch_name)
    batcho.assemble_batch(batch_name=batch_name)

    statuses = batcho.get_batch_job_statuses(batch_name='batch1')

    txt = batcho.get_batch_job_console_output(batch_name='batch1', job_index=0)

    results = batcho.get_batch_results(batch_name='batch1')

    assert len(results['results']) == 2
    assert results['results'][0]['result']['test'] == 3
