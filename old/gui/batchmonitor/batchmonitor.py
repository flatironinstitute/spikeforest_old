import vdomr as vd
from mountaintools import client as mt
import numpy as np
import json


class JobView(vd.Component):
    def __init__(self, compute_resource_client):
        vd.Component.__init__(self)
        self._compute_resource_client = compute_resource_client
        self._job = None
        self._back_handlers = []

    def setJob(self, job):
        self._job = job
        self._on_refresh()

    def onBack(self, handler):
        self._back_handlers.append(handler)

    def _on_refresh(self):
        self.refresh()

    def _on_back(self):
        for handler in self._back_handlers:
            handler()

    def render(self):
        if self._job is None:
            return vd.div('No job')
        back_button = vd.button('Back to job list', onclick=self._on_back)
        console_out = None
        if 'result' in self._job:
            console_out = mt.loadText(path=self._job['result'].get('console_out', None))
        return vd.div(
            vd.div(back_button),
            vd.div(vd.pre(console_out or '')),
            vd.div(vd.pre(json.dumps(self._job, indent=4)))
        )


class BatchView(vd.Component):
    def __init__(self, compute_resource_client):
        vd.Component.__init__(self)
        self._compute_resource_client = compute_resource_client
        self._batch_id = None
        self._batch = None
        self._jobs = None
        self._job_statuses = None
        self._job_table = vd.div()  # dummy
        self._back_handlers = []
        self._list_mode = True
        self._job_view = JobView(compute_resource_client=self._compute_resource_client)
        self._job_view.onBack(self._go_back_to_joblist_table)

    def setBatchId(self, batch_id):
        self._batch_id = batch_id
        self._on_refresh()

    def onBack(self, handler):
        self._back_handlers.append(handler)

    def _open_job(self, job_index):
        job0 = self._jobs[job_index]
        if 'result' not in job0:
            job_result_key = dict(
                name='compute_resource_batch_job_results',
                batch_id=self._batch_id
            )
            result0 = mt.loadObject(key=job_result_key, subkey=str(job_index))
            if result0:
                job0['result'] = result0
        self._job_view.setJob(job0)
        self._list_mode = False
        self.refresh()

    def _on_refresh(self):
        batch = self._compute_resource_client.getBatch(batch_id=self._batch_id)
        job_statuses = self._compute_resource_client.getBatchJobStatuses(batch_id=self._batch_id)
        self._batch = batch
        self._job_statuses = job_statuses
        if 'jobs' not in batch:
            batch['jobs'] = []

        jobs = batch['jobs']
        self._jobs = jobs
        for ii, job in enumerate(jobs):
            job['status'] = self._job_statuses.get(str(ii), 'Unknown')

        job_results = self._compute_resource_client.getBatchJobResults(batch_id=self._batch_id)
        if job_results:
            for ii, result in enumerate(job_results):
                jobs[ii]['result'] = dict(
                    retcode=result.retcode,
                    runtime_info=result.runtime_info,
                    console_out=result.console_out,
                    outputs=result.outputs
                )

        callbacks = [
            lambda job_index=ii: self._open_job(job_index=job_index)
            for ii in range(len(jobs))
        ]
        job_table_data = [
            dict(
                job_index=dict(text='{}'.format(ii), callback=callbacks[ii]),
                label=dict(text=job.get('label', 'no-label'), callback=callbacks[ii]),
                status=dict(text=job['status'], callback=callbacks[ii]),
                processor_name=dict(text=job['processor_name']),
                processor_version=dict(text=job['processor_version']),
                processor_class_name=dict(text=job['processor_class_name']),
                processor_code=dict(text=job['processor_code']),
                container=dict(text=job['container']),
                # inputs=dict(text=job['inputs']),
                # outputs=dict(text=job['outputs']),
                # parameters=dict(text=job['parameters'])
            )
            for ii, job in enumerate(jobs)
        ]
        print(jobs[0])
        self._job_table = _to_table(job_table_data, ['job_index', 'label', 'status', 'processor_name', 'processor_code', 'container'])
        self.refresh()

    def _go_back_to_joblist_table(self):
        self._list_mode = True
        self.refresh()

    def _on_back(self):
        for handler in self._back_handlers:
            handler()
    # def _on_back_to_list(self):
    #     self._list_mode=True
    #     self.refresh()

    def render(self):
        if self._batch_id is None:
            return vd.div('No batch id')
        if self._list_mode:
            refresh_button = vd.button('Refresh', onclick=self._on_refresh)
            back_button = vd.button('Back to batches', onclick=self._on_back)
            label = self._batch.get('label', 'nolabel')
            return vd.div(
                vd.div(self._batch_id + ' ' + label),
                vd.div(refresh_button, back_button),
                self._job_table
            )
        else:
            # back_button=vd.button('Back to job list',onclick=self._on_back_to_list)
            return vd.div(
                self._job_view,
                style=dict(padding='15px')
            )


class BatchMonitor(vd.Component):
    def __init__(self, resource_name):
        vd.Component.__init__(self)

        mt_config = mt.getRemoteConfig()

        self._resource_name = resource_name
        self._batch_statuses = dict()

        self._batchlist_table = vd.div()  # dummy
        self._batch_view = BatchView(compute_resource_client=self._compute_resource_client)
        self._list_mode = True

        vd.devel.loadBootstrap()

        self._batch_view.onBack(self._go_back_to_batchlist_table)

        self._update_batchlist_table()

    def _on_update(self):
        self._update_batchlist_table()

    def _open_batch(self, batch_id):
        self._batch_view.setBatchId(batch_id)
        self._list_mode = False
        self.refresh()

    def _go_back_to_batchlist_table(self):
        self._list_mode = True
        self.refresh()

    def _update_batchlist_table(self):
        batch_statuses = self._compute_resource_client.getBatchStatuses()
        if batch_statuses is None:
            print('PROBLEM: unable to load batch statuses for resource: ' + self._resource_name)
            self._batch_statuses = dict()
        else:
            self._batch_statuses = batch_statuses

        batch_ids = list(self._batch_statuses.keys())
        batch_ids.sort(reverse=True)

        batches = dict()
        for ii, batch_id in enumerate(batch_ids):
            if ii < 10:
                print('Loading batch: ' + batch_id)
                batch = self._compute_resource_client.getBatch(batch_id=batch_id)
                if batch is None:
                    batch = dict()
                batches[batch_id] = batch
            else:
                batches[batch_id] = dict()

        batchlist_table_data = [
            dict(
                batch_id=dict(text=batch_id, callback=lambda batch_id=batch_id: self._open_batch(batch_id=batch_id)),
                status=dict(text=self._batch_statuses[batch_id]),
                num_jobs=dict(text='{}'.format(len(batches[batch_id].get('jobs', [])))),
                label=dict(text=batches[batch_id].get('label', 'no label'))
            )
            for batch_id in batch_ids
        ]
        self._batchlist_table = _to_table(batchlist_table_data, ['batch_id', 'label', 'status', 'num_jobs'])

        self.refresh()

    def _on_refresh_list(self):
        self._update_batchlist_table()

    def _on_back_to_list(self):
        self._list_mode = True
        self.refresh()

    def render(self):
        if self._list_mode:
            refresh_list_button = vd.button('Refresh', onclick=self._on_refresh_list)
            return vd.div(
                vd.table(
                    vd.tr(vd.td(refresh_list_button))
                ),
                vd.components.ScrollArea(
                    self._batchlist_table,
                    height=500
                ),
                style=dict(padding='15px')
            )
        else:
            # back_button=vd.button('Back to list',onclick=self._on_back_to_list)
            return vd.div(
                self._batch_view,
                style=dict(padding='15px')
            )


def _to_table(X, column_names):
    rows = []
    rows.append(vd.tr([vd.th(cname) for cname in column_names]))
    for x in X:
        elmts = []
        for cname in column_names:
            tmp = x.get(cname)
            if tmp:
                if 'callback' in tmp:
                    elmt = vd.a(tmp['text'], onclick=tmp['callback'])
                else:
                    elmt = vd.span(str(tmp.get('text')))
            else:
                elmt = vd.span('N/A')
            elmts.append(elmt)
        rows.append(vd.tr([vd.td(elmt) for elmt in elmts]))
    return vd.table(rows, class_='table')
