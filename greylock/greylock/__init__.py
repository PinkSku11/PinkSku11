"""greylock — software for a real (forward) time machine.

A cesium clock on a mountain, compared continuously with GPS time, runs fast by
gΔh/c².  This package is everything around the clock: the drivers that read the
counter, the receiver and the clock's health; a digital twin to develop against
before any hardware exists; an append-only hash-chained ledger; the analysis
that turns a season of pulses into a rate with an error bar; and the readout.
"""
__version__ = "0.2.0"
