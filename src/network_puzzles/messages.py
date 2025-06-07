from . import _

puzzles = {
    "0.3.4": {
        'title': _("Network Loop"),
        'message': _("This puzzle shows you what happens when you create a network loop.  A loop is made when you have your switches connected to themselves or to another one that is connected back to the first one.  Ping from pc0 to pc1 to see what happens.  You do not need to fix the problem, but right-clicking one of the switches and removing one of the offending links would do it."),
    },
    "0.3.5.1": {
        'title': _("Network Loop 2"),
        'message': _("Managed Switches can use Spanning Tree, which intelligently figures out the least distance path to a point.  It is made so you can have network loops and survive.  Try pinging pc1 twice from pc0.  The first time, some packets are lost.  But the second time the packet goes where it should."),
    },
    "0.10.1": {
        'title': _("Bad Power Supply"),
        'message': _("Occasionally a piece of hardware will break, This often happens after long periods of use, though sometimes after just sitting around unused.\n\nThis puzzle makes it look a little worse than it usually would look.  Go ahead and turn on the switch.  After that, right-click and replace it.\n\nThings that have been replaced will need to have their settings put back.  So make sure to give the new switch a good IP and gateway."),
    },
}
