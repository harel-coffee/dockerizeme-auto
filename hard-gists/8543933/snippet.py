# Author : Alex Gramfort
# license BSD (copied for Chaco example data_stream.py)

# to use it:
# Start ./sine2ft in the background (available in fieldtrip repo)
# Start the buffer
# Then run this script in a python terminal

# Major library imports
import sys
import numpy as np

# Enthought imports
from traits.api import (Array, Callable, Enum, HasTraits, Instance, Int, Trait)
from traitsui.api import Group, HGroup, Item, View, spring, Handler
from pyface.timer.api import Timer

# Chaco imports
from chaco.chaco_plot_editor import ChacoPlotItem

import FieldTrip

ftc = FieldTrip.Client()
ftc.connect('localhost', 1972)    # might throw IOError
# ftc.connect('130.229.13.241', 1972)    # might throw IOError
# ftc.connect('130.229.9.194', 1972)    # might throw IOError


def get_data():
    H = ftc.getHeader()
    block_size = 500
    if H is None:
        print 'Failed to retrieve header!'
        sys.exit(1)

    start, stop = H.nSamples - block_size, H.nSamples - 1
    print H.nSamples
    D = ftc.getData([start, stop])
    return D[:, 0]


class Viewer(HasTraits):
    """ This class just contains the two data arrays that will be updated
    by the Controller.  The visualization/editor for this class is a
    Chaco plot.
    """
    index = Array
    data = Array

    plot_type = Enum("line", "scatter")

    view = View(ChacoPlotItem("index", "data",
                              type_trait="plot_type",
                              resizable=True,
                              x_label="Time",
                              y_label="Signal",
                              color="blue",
                              bgcolor="white",
                              border_visible=True,
                              border_width=1,
                              padding_bg_color="lightgray",
                              width=800,
                              height=380,
                              marker_size=2,
                              show_label=False),
                HGroup(spring, Item("plot_type", style='custom'), spring),
                resizable = True,
                buttons = ["OK"],
                width=800, height=500)


class Controller(HasTraits):

    # A reference to the plot viewer object
    viewer = Instance(Viewer)

    # The max number of data points to accumulate and show in the plot
    max_num_points = Int(1000)

    # The number of data points we have received; we need to keep track of
    # this in order to generate the correct x axis data series.
    num_ticks = Int(0)

    # private reference to the random number generator.  this syntax
    # just means that self._generator should be initialized to
    # random.normal, which is a random number function, and in the future
    # it can be set to any callable object.
    _generator = Trait(get_data, Callable)

    view = View(Group('max_num_points',
                      orientation="vertical"),
                      buttons=["OK", "Cancel"])

    def timer_tick(self, *args):
        """
        Callback function that should get called based on a timer tick.  This
        will generate a new random data point and set it on the `.data` array
        of our viewer object.
        """
        # Generate a new number and increment the tick count
        new_val = self._generator()
        self.num_ticks += len(new_val)

        # grab the existing data, truncate it, and append the new point.
        # This isn't the most efficient thing in the world but it works.
        cur_data = self.viewer.data
        # new_data = np.hstack((cur_data[-self.max_num_points+1:], [new_val]))
        new_data = np.r_[cur_data[-self.max_num_points+1:], new_val]
        new_index = np.arange(self.num_ticks - len(new_data) + 1,
                              self.num_ticks + 0.01)

        self.viewer.index = new_index
        self.viewer.data = new_data
        return


class DemoHandler(Handler):

    def closed(self, info, is_ok):
        """ Handles a dialog-based user interface being closed by the user.
        Overridden here to stop the timer once the window is destroyed.
        """
        info.object.timer.Stop()
        return


class Demo(HasTraits):
    controller = Instance(Controller)
    viewer = Instance(Viewer, ())
    timer = Instance(Timer)
    view = View(Item('controller', style='custom', show_label=False),
                Item('viewer', style='custom', show_label=False),
                handler=DemoHandler,
                resizable=True)

    def edit_traits(self, *args, **kws):
        # Start up the timer! We should do this only when the demo actually
        # starts and not when the demo object is created.
        self.timer = Timer(100, self.controller.timer_tick)
        return super(Demo, self).edit_traits(*args, **kws)

    def configure_traits(self, *args, **kws):
        # Start up the timer! We should do this only when the demo actually
        # starts and not when the demo object is created.
        self.timer = Timer(100, self.controller.timer_tick)
        return super(Demo, self).configure_traits(*args, **kws)

    def _controller_default(self):
        return Controller(viewer=self.viewer)


# NOTE: examples/demo/demo.py looks for a 'demo' or 'popup' or 'modal popup'
# keyword when it executes this file, and displays a view for it.
popup = Demo()


if __name__ == "__main__":
    popup.configure_traits()
