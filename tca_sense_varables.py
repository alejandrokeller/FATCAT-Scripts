#!/usr/bin/env python

X = [255, 255, 255]  # White
O = [0, 0, 0]        # Black
green = [0, 255, 0]  # Green
blue = [0, 0, 255]   # Blue
sense_light = True
tc_symbol = [
O, O, O, O, O, O, O, O,
X, X, X, O, O, X, O, O,
O, X, O, O, X, O, X, O,
O, X, O, O, X, O, O, O,
O, X, O, O, X, O, O, O,
O, X, O, O, X, O, X, O,
O, X, O, O, O, X, O, O,
O, O, O, O, O, O, O, O
]
error_letter = "?"

sense_3 = [
X, X, X, X, X, X, X, X,
X, O, O, O, O, O, O, X,
X, O, O, O, O, O, O, X,
X, O, O, O, O, O, O, X,
X, O, O, O, O, O, O, X,
X, O, O, O, O, O, O, X,
X, O, O, O, O, O, O, X,
X, X, X, X, X, X, X, X
]

sense_2 = [
O, O, O, O, O, O, O, O,
O, X, X, X, X, X, X, O,
O, X, O, O, O, O, X, O,
O, X, O, O, O, O, X, O,
O, X, O, O, O, O, X, O,
O, X, O, O, O, O, X, O,
O, X, X, X, X, X, X, O,
O, O, O, O, O, O, O, O
]

sense_1 = [
O, O, O, O, O, O, O, O,
O, O, O, O, O, O, O, O,
O, O, X, X, X, X, O, O,
O, O, X, O, O, X, O, O,
O, O, X, O, O, X, O, O,
O, O, X, X, X, X, O, O,
O, O, O, O, O, O, O, O,
O, O, O, O, O, O, O, O 
]

sense_0 = [
O, O, O, O, O, O, O, O,
O, O, O, O, O, O, O, O,
O, O, O, O, O, O, O, O,
O, O, O, X, X, O, O, O,
O, O, O, X, X, O, O, O,
O, O, O, O, O, O, O, O,
O, O, O, O, O, O, O, O,
O, O, O, O, O, O, O, O
]

sense_vector = (sense_0, sense_1, sense_2, sense_3)
