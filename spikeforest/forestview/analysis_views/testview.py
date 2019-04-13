import vdomr as vd

class TestView(vd.Component):
    def __init__(self, context, opts=None, prepare_result=None):
        vd.Component.__init__(self)
        self._context = context
        self._opts = opts
        self._size = (100, 100)
        self._widget = TestWidget(context)
    @staticmethod
    def prepareView(context, opts):
        # prepare code goes here
        # Or, you can remove this function altogether
        pass
    def setSize(self, size):
        self._size = size
        self._widget.setSize(size)
    def size(self):
        return self._size
    def tabLabel(self):
        return 'Test view'
    def render(self):
        return self._widget

class TestWidget(vd.Component):
    def __init__(self, context):
        vd.Component.__init__(self)
        self._context = context
        self._size = (100, 100)
    def setSize(self, size):
        self._size = size
    def size(self):
        return self._size
    def render(self):
        return vd.div('Test created via snippet.')
