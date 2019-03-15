import vdomr as vd
from mountaintools import client as ca
import numpy as np

class BatchView(vd.Component):
    def __init__(self):
        vd.Component.__init__(self)
        self._batch_id=None
        self._batch=None
        self._job_table=vd.div() #dummy
    def setBatchId(self,batch_id):
        self._batch_id=batch_id
        self._on_refresh()
    def _on_refresh(self):
        key=dict(
            name='compute_resource_batch',
            batch_id=self._batch_id
        )
        batch=ca.loadObject(key=key)
        self._batch=batch

        jobs=batch.get('jobs',[])

        job_table_data=[
            dict(
                job_index=dict(text='{}'.format(ii)),
                processor_name=dict(text=job['processor_name']),
                processor_version=dict(text=job['processor_version']),
                processor_class_name=dict(text=job['processor_class_name']),
                processor_code=dict(text=job['processor_code']),
                container=dict(text=job['container']),
                # inputs=dict(text=job['inputs']),
                # outputs=dict(text=job['outputs']),
                # parameters=dict(text=job['parameters'])
            )
            for ii,job in enumerate(jobs)
        ]
        print(jobs[0])
        self._job_table=_to_table(job_table_data,['job_index','processor_name','processor_class_name','processor_code','container'])
        self.refresh()
    def render(self):
        if self._batch_id is None:
            return vd.div('No batch id')
        refresh_button=vd.button('Refresh',onclick=self._on_refresh)
        label=self._batch.get('label','nolabel')
        return vd.div(
            vd.div('Test: '+self._batch_id+' '+label),
            self._job_table
        )

class BatchMonitor(vd.Component):
    def __init__(self, resource_name):
        vd.Component.__init__(self)

        self._resource_name = resource_name
        self._batch_statuses=dict()

        self._batchlist_table = vd.div()  # dummy
        self._batch_view=BatchView()
        self._list_mode=True

        vd.devel.loadBootstrap()

        self._update_batchlist_table()

    def _on_update(self):
        self._update_batchlist_table()

    def _open_batch(self, batch_id):
        self._batch_view.setBatchId(batch_id)
        self._list_mode=False
        self.refresh()

    def _update_batchlist_table(self):
        batch_statuses = ca.getValue(
            key=dict(
                name='compute_resource_batch_statuses',
                resource_name=self._resource_name,
            ),
            subkey='-',
            parse_json=True
        )
        if batch_statuses is None:
            print('PROBLEM: unable to load batch statuses for resource: '+self._resource_name)
            self._batch_statuses=dict()
        else:
            self._batch_statuses=batch_statuses

        batch_ids=list(self._batch_statuses.keys())
        batch_ids.sort(reverse=True)

        batches=dict()
        for ii,batch_id in enumerate(batch_ids):
            if ii<10:
                print('Loading batch: '+batch_id)
                key=dict(
                    name='compute_resource_batch',
                    batch_id=batch_id
                )
                batch=ca.loadObject(
                    key=key
                )
                if batch is None:
                    batch=dict()
                batches[batch_id]=batch
            else:
                batches[batch_id]=dict()

        batchlist_table_data=[
            dict(
                batch_id=dict(text=batch_id, callback=lambda batch_id=batch_id: self._open_batch(batch_id=batch_id)),
                status=dict(text=self._batch_statuses[batch_id]),
                num_jobs=dict(text='{}'.format(len(batches[batch_id].get('jobs',[])))),
                label=dict(text=batches[batch_id].get('label','no label'))
            )
            for batch_id in batch_ids
        ]
        self._batchlist_table=_to_table(batchlist_table_data, ['batch_id', 'label', 'status', 'num_jobs'])

        self.refresh()

    def _on_refresh_list(self):
        self._update_batchlist_table()

    def _on_back_to_list(self):
        self._list_mode=True
        self.refresh()

    def render(self):
        if self._list_mode:
            refresh_list_button=vd.button('Refresh',onclick=self._on_refresh_list)
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
            back_button=vd.button('Back to list',onclick=self._on_back_to_list)
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
                    elmt = vd.span(tmp['text'])
            else:
                elmt = vd.span('N/A')
            elmts.append(elmt)
        rows.append(vd.tr([vd.td(elmt) for elmt in elmts]))
    return vd.table(rows, class_='table')