from matplotlib import pyplot as plt
import numpy as np
from matplotlib.ticker import MaxNLocator

def plot_timeseries(*, recording, sorting=None, channels=None, trange=None, width=None, height=None):
    W = TimeseriesWidget(
        recording=recording,
        sorting=sorting,
        channels=channels,
        trange=trange,
        width=width,
        height=height
    )
    W.plot()


def view_timeseries(*, recording, sorting=None, channels=None, trange=None, width=None, height=None):
    W = TimeseriesWidget(
        recording=recording,
        sorting=sorting,
        channels=channels,
        trange=trange,
        width=width,
        height=height
    )
    W.display()


class TimeseriesWidget:
    def __init__(self, *, recording, sorting=None, channels=None, trange=None, width=None, height=None):
        self._recording = recording
        self._sorting = sorting
        self._samplerate = recording.getSamplingFrequency()
        self._width = width
        self._height = height
        self._visible_channels = channels
        if self._width is None:
            self._width = 12
        if self._height is None:
            self._height = 6
        if self._visible_channels is None:
            self._visible_channels = recording.getChannelIds()
        self._visible_trange = trange
        if self._visible_trange is None:
            self._visible_trange = [0, np.minimum(10000, recording.getNumFrames())]
        self._initialize_stats()
        self._vspacing = self._mean_channel_std * 15
        self._visible_trange = self._fix_trange(self._visible_trange)
        # self._update_plot()

    def _init_widgets(self):
        import ipywidgets as widgets
        self._widget = widgets.Output()
        self._control_panel = self._create_control_panel()
        self._main_widget = widgets.VBox([self._control_panel, self._widget])

    def plot(self):
        self._do_plot()

    def display(self):
        self._init_widgets()
        self._update_plot()
        display(self._main_widget)

    def widget(self):
        return self._widget

    def figure(self):
        return self._figure

    def _update_plot(self):
        self._widget.clear_output(wait=True)
        with self._widget:
            self._do_plot()

    def _do_plot(self):
        chunk0 = self._recording.getTraces(
            channel_ids=self._visible_channels,
            start_frame=self._visible_trange[0],
            end_frame=self._visible_trange[1]
        )
        plt.xlim(self._visible_trange[0] / self._samplerate, self._visible_trange[1] / self._samplerate)
        plt.ylim(-self._vspacing, self._vspacing * len(self._visible_channels))
        plt.gcf().set_size_inches(self._width, self._height)
        plt.gca().get_xaxis().set_major_locator(MaxNLocator(prune='both'))
        plt.gca().get_yaxis().set_ticks([])
        plt.xlabel('Time (sec)')

        self._plots = {}
        self._plot_offsets = {}
        offset0 = self._vspacing * (len(self._visible_channels) - 1)
        tt = np.arange(self._visible_trange[0], self._visible_trange[1]) / self._samplerate
        for im, m in enumerate(self._visible_channels):
            self._plot_offsets[m] = offset0
            self._plots[m] = plt.plot(tt, self._plot_offsets[m] + chunk0[im, :])
            offset0 = offset0 - self._vspacing
        self._figure = plt.gcf()
        # plt.show()

    def _pan_left(self):
        self._pan(-0.1)

    def _pan_right(self):
        self._pan(0.1)

    def _pan(self, factor):
        span = self._visible_trange[1] - self._visible_trange[0]
        delta = int(span * factor)
        new_trange = [self._visible_trange[0] + delta, self._visible_trange[1] + delta]
        new_trange = self._fix_trange(new_trange)
        self._visible_trange = new_trange
        self._update_plot()

    def _fix_trange(self, trange):
        N = self._recording.getNumFrames()
        if trange[1] > N:
            trange[0] += N - trange[1]
            trange[1] += N - trange[1]
        if trange[0] < 0:
            trange[1] += -trange[0]
            trange[0] = 0
        trange[0] = np.maximum(0, trange[0])
        trange[1] = np.minimum(N, trange[1])
        return trange

    def _scale_up(self):
        self._scale(1.2)

    def _scale_down(self):
        self._scale(1 / 1.2)

    def _scale(self, factor):
        self._vspacing /= factor
        self._update_plot()

    def _zoom_in(self):
        self._zoom(1.2)

    def _zoom_out(self):
        self._zoom(1 / 1.2)

    def _zoom(self, factor):
        span = self._visible_trange[1] - self._visible_trange[0]
        new_span = int(np.maximum(30, span / factor))
        tcenter = int((self._visible_trange[0] + self._visible_trange[1]) / 2)
        new_trange = [int(tcenter - new_span / 2), int(tcenter - new_span / 2 + new_span - 1)]
        new_trange = self._fix_trange(new_trange)
        self._visible_trange = new_trange
        self._update_plot()

    def _initialize_stats(self):
        self._channel_stats = {}
        # M=self._reader.numChannels()
        # N=self._reader.numTimepoints()
        chunk0 = self._recording.getTraces(
            channel_ids=self._visible_channels,
            start_frame=self._visible_trange[0],
            end_frame=self._visible_trange[1]
        )
        # chunk0=self._reader.getChunk(channels=self._visible_channels,trange=self._visible_trange)
        M0 = chunk0.shape[0]
        N0 = chunk0.shape[1]
        for ii in range(M0):
            self._channel_stats[self._visible_channels[ii]] = self._compute_channel_stats_from_data(chunk0[ii, :])
        self._mean_channel_std = np.mean([self._channel_stats[m]['std'] for m in self._visible_channels])

    def _compute_channel_stats_from_data(self, X):
        return dict(
            mean=np.mean(X),
            std=np.std(X)
        )

    def _create_control_panel(self):
        def on_zoom_in(b):
            self._zoom_in()

        def on_zoom_out(b):
            self._zoom_out()

        def on_pan_left(b):
            self._pan_left()

        def on_pan_right(b):
            self._pan_right()

        def on_scale_up(b):
            self._scale_up()

        def on_scale_down(b):
            self._scale_down()

        zoom_in = widgets.Button(icon='plus-square', tooltip="Zoom In", layout=dict(width='40px'))
        zoom_in.on_click(on_zoom_in)
        zoom_out = widgets.Button(icon='minus-square', tooltip="Zoom Out", layout=dict(width='40px'))
        zoom_out.on_click(on_zoom_out)
        pan_left = widgets.Button(icon='arrow-left', tooltip="Pan left", layout=dict(width='40px'))
        pan_left.on_click(on_pan_left)
        pan_right = widgets.Button(icon='arrow-right', tooltip="Pan right", layout=dict(width='40px'))
        pan_right.on_click(on_pan_right)
        scale_up = widgets.Button(icon='arrow-up', tooltip="Scale up", layout=dict(width='40px'))
        scale_up.on_click(on_scale_up)
        scale_down = widgets.Button(icon='arrow-down', tooltip="Scale down", layout=dict(width='40px'))
        scale_down.on_click(on_scale_down)
        self._debug = widgets.Output()
        return widgets.HBox([zoom_in, zoom_out, pan_left, pan_right, scale_up, scale_down, self._debug])
