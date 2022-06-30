
from typing import Sequence, Tuple
from dataclasses import dataclass

@dataclass
class CurvePoint:
    location: Tuple[float, float] = (0.0, 0.0)
    handle_type: str = 'AUTO'
    select: bool = False


@dataclass
class Curve:
    points: Sequence[CurvePoint]
    extend: str = 'HORIZONTAL'


linear = Curve([
    CurvePoint((0.0, 0.0), 'VECTOR'),
    CurvePoint((1.0, 1.0), 'VECTOR'),
    ])

sine_in = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    ])

sine_out = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.9, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    ])

sine_in_out = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.9, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    ])

quad_in = Curve([
    CurvePoint((0.0, 0.0)   , 'AUTO'),
    CurvePoint((0.15, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)   , 'AUTO'),
    ])

quad_out = Curve([
    CurvePoint((0.0, 0.0)   , 'AUTO'),
    CurvePoint((0.85, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)   , 'AUTO'),
    ])

quad_in_out = Curve([
    CurvePoint((0.0, 0.0)   , 'AUTO'),
    CurvePoint((0.15, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((0.85, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)   , 'AUTO'),
    ])

cubic_in = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.2, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    ])

cubic_out = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.8, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    ])

cubic_in_out = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO'),
    CurvePoint((0.2, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.8, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO'),
    ])

quart_in = Curve([
    CurvePoint((0.0, 0.0)  , 'AUTO'),
    CurvePoint((0.25, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)  , 'AUTO'),
    ])

quart_out = Curve([
    CurvePoint((0.0, 0.0)  , 'AUTO'),
    CurvePoint((0.75, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)  , 'AUTO'),
    ])

quart_in_out = Curve([
    CurvePoint((0.0, 0.0)  , 'AUTO'),
    CurvePoint((0.25, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.75, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)  , 'AUTO'),
    ])

quint_in = Curve([
    CurvePoint((0.0, 0.0)    , 'AUTO'),
    CurvePoint((0.275, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)    , 'AUTO'),
    ])

quint_out = Curve([
    CurvePoint((0.0, 0.0)    , 'AUTO'),
    CurvePoint((0.725, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)    , 'AUTO'),
    ])

quint_in_out = Curve([
    CurvePoint((0.0, 0.0)    , 'AUTO'),
    CurvePoint((0.275, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((0.725, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)    , 'AUTO'),
    ])

falloff_linear = Curve([
    CurvePoint((0.0, 1.0), 'VECTOR'),
    CurvePoint((1.0, 0.0), 'VECTOR'),
    ])

falloff_sine_in = Curve([
    CurvePoint((0.0, 1.0) , 'AUTO'),
    CurvePoint((0.1, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0) , 'AUTO'),
    ])

falloff_sine_out = Curve([
    CurvePoint((0.0, 1.0) , 'AUTO'),
    CurvePoint((0.9, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0) , 'AUTO'),
    ])

falloff_sine_in_out = Curve([
    CurvePoint((0.0, 1.0) , 'AUTO'),
    CurvePoint((0.1, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.9, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0) , 'AUTO'),
    ])

falloff_quad_in = Curve([
    CurvePoint((0.0, 1.0)   , 'AUTO'),
    CurvePoint((0.15, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)   , 'AUTO'),
    ])

falloff_quad_out = Curve([
    CurvePoint((0.0, 1.0)   , 'AUTO'),
    CurvePoint((0.85, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)   , 'AUTO'),
    ])

falloff_quad_in_out = Curve([
    CurvePoint((0.0, 1.0)   , 'AUTO'),
    CurvePoint((0.15, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((0.85, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)   , 'AUTO'),
    ])

falloff_cubic_in = Curve([
    CurvePoint((0.0, 1.0) , 'AUTO'),
    CurvePoint((0.2, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0) , 'AUTO'),
    ])

falloff_cubic_out = Curve([
    CurvePoint((0.0, 1.0) , 'AUTO'),
    CurvePoint((0.8, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0) , 'AUTO'),
    ])

falloff_cubic_in_out = Curve([
    CurvePoint((0.0, 1.0) , 'AUTO'),
    CurvePoint((0.2, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.8, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0) , 'AUTO'),
    ])

falloff_quart_in = Curve([
    CurvePoint((0.0, 1.0)  , 'AUTO'),
    CurvePoint((0.25, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)  , 'AUTO'),
    ])

falloff_quart_out = Curve([
    CurvePoint((0.0, 1.0)  , 'AUTO'),
    CurvePoint((0.75, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)  , 'AUTO'),
    ])

falloff_quart_in_out = Curve([
    CurvePoint((0.0, 1.0)  , 'AUTO'),
    CurvePoint((0.25, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.75, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)  , 'AUTO'),
    ])

falloff_quint_in = Curve([
    CurvePoint((0.0, 1.0)    , 'AUTO'),
    CurvePoint((0.275, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)    , 'AUTO'),
    ])

falloff_quint_out = Curve([
    CurvePoint((0.0, 1.0)    , 'AUTO'),
    CurvePoint((0.725, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)    , 'AUTO'),
    ])

falloff_quint_in_out = Curve([
    CurvePoint((0.0, 1.0)    , 'AUTO'),
    CurvePoint((0.275, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((0.725, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)    , 'AUTO'),
    ])

bell_linear = Curve([
    CurvePoint((0.0, 0.0), 'VECTOR'),
    CurvePoint((0.5, 1.0), 'VECTOR'),
    CurvePoint((1.0, 0.0), 'VECTOR'),
    ])

bell_sine_in = Curve([
    CurvePoint((0.0, 0.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.05, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.95, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)  , 'AUTO_CLAMPED'),
    ])

bell_sine_out = Curve([
    CurvePoint((0.0, 0.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.45, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.55, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)  , 'AUTO_CLAMPED'),
    ])

bell_sine_in_out = Curve([
    CurvePoint((0.0, 0.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.05, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.45, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.55, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.95, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)  , 'AUTO_CLAMPED'),
    ])

bell_quad_in = Curve([
    CurvePoint((0.0, 0.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.075, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.925, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)    , 'AUTO_CLAMPED'),
    ])

bell_quad_out = Curve([
    CurvePoint((0.0, 0.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.425, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.575, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)    , 'AUTO_CLAMPED'),
    ])

bell_quad_in_out = Curve([
    CurvePoint((0.0, 0.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.075, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((0.425, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.575, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((0.925, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)    , 'AUTO_CLAMPED'),
    ])

bell_cubic_in = Curve([
    CurvePoint((0.0, 0.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.9, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)  , 'AUTO_CLAMPED'),
    ])

bell_cubic_out = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.4, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.6, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.0, 0.0) , 'AUTO_CLAMPED'),
    ])

bell_cubic_in_out = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.4, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.6, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.9, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.0, 0.0) , 'AUTO_CLAMPED'),
    ])

bell_quart_in = Curve([
    CurvePoint((0.0, 0.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.125, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.875, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)   , 'AUTO_CLAMPED'),
    ])

bell_quart_out = Curve([
    CurvePoint((0.0, 0.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.375, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.625, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)   , 'AUTO_CLAMPED'),
    ])

bell_quart_in_out = Curve([
    CurvePoint((0.0, 0.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.125, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.375, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.625, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.875, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)   , 'AUTO_CLAMPED'),
    ])

bell_quint_in = Curve([
    CurvePoint((0.0, 0.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.1375, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.8625, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)     , 'AUTO_CLAMPED'),
    ])

bell_quint_out = Curve([
    CurvePoint((0.0, 0.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.3625, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.6375, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)     , 'AUTO_CLAMPED'),
    ])

bell_quint_in_out = Curve([
    CurvePoint((0.0, 0.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.1375, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((0.3625, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.6375, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((0.8625, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)     , 'AUTO_CLAMPED'),
    ])

bell_linear_head = Curve([
    CurvePoint((0.0, 0.0), 'VECTOR'),
    CurvePoint((0.5, 1.0), 'VECTOR'),
    CurvePoint((1.0, 1.0), 'VECTOR'),
    ])

bell_sine_in_head = Curve([
    CurvePoint((0.0, 0.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.05, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)  , 'AUTO_CLAMPED'),
    ])

bell_sine_out_head = Curve([
    CurvePoint((0.0, 0.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.45, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)  , 'AUTO_CLAMPED'),
    ])

bell_sine_in_out_head = Curve([
    CurvePoint((0.0, 0.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.05, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.45, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)  , 'AUTO_CLAMPED'),
    ])

bell_quad_in_head = Curve([
    CurvePoint((0.0, 0.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.075, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)    , 'AUTO_CLAMPED'),
    ])

bell_quad_out_head = Curve([
    CurvePoint((0.0, 0.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.425, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)    , 'AUTO_CLAMPED'),
    ])

bell_quad_in_out_head = Curve([
    CurvePoint((0.0, 0.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.075, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((0.425, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)    , 'AUTO_CLAMPED'),
    ])

bell_cubic_in_head = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO_CLAMPED'),
    ])

bell_cubic_out_head = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.4, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO_CLAMPED'),
    ])

bell_cubic_in_out_head = Curve([
    CurvePoint((0.0, 0.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.1, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.4, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0) , 'AUTO_CLAMPED'),
    ])

bell_quart_in_head = Curve([
    CurvePoint((0.0, 0.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.125, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)   , 'AUTO_CLAMPED'),
    ])

bell_quart_out_head = Curve([
    CurvePoint((0.0, 0.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.375, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)   , 'AUTO_CLAMPED'),
    ])

bell_quart_in_out_head = Curve([
    CurvePoint((0.0, 0.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.125, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((0.375, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)   , 'AUTO_CLAMPED'),
    ])

bell_quint_in_head = Curve([
    CurvePoint((0.0, 0.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.1375, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)     , 'AUTO_CLAMPED'),
    ])

bell_quint_out_head = Curve([
    CurvePoint((0.0, 0.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.3625, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)     , 'AUTO_CLAMPED'),
    ])

bell_quint_in_out_head = Curve([
    CurvePoint((0.0, 0.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.1375, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((0.3625, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((1.0, 1.0)     , 'AUTO_CLAMPED'),
    ])

bell_linear_tail = Curve([
    CurvePoint((0.0, 1.0), 'VECTOR'),
    CurvePoint((0.5, 1.0), 'VECTOR'),
    CurvePoint((1.0, 0.0), 'VECTOR'),
    ])

bell_sine_in_tail = Curve([
    CurvePoint((0.0, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.95, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)  , 'AUTO_CLAMPED'),
    ])

bell_sine_out_tail = Curve([
    CurvePoint((0.0, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.55, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)  , 'AUTO_CLAMPED'),
    ])

bell_sine_in_out_tail = Curve([
    CurvePoint((0.0, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)  , 'AUTO_CLAMPED'),
    CurvePoint((0.55, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.95, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)  , 'AUTO_CLAMPED'),
    ])

bell_quad_in_tail = Curve([
    CurvePoint((0.0, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.925, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)    , 'AUTO_CLAMPED'),
    ])

bell_quad_out_tail = Curve([
    CurvePoint((0.0, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.575, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)    , 'AUTO_CLAMPED'),
    ])

bell_quad_in_out_tail = Curve([
    CurvePoint((0.0, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)    , 'AUTO_CLAMPED'),
    CurvePoint((0.575, 0.955), 'AUTO_CLAMPED'),
    CurvePoint((0.925, 0.045), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)    , 'AUTO_CLAMPED'),
    ])

bell_cubic_in_tail = Curve([
    CurvePoint((0.0, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.9, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0) , 'AUTO_CLAMPED'),
    ])

bell_cubic_out_tail = Curve([
    CurvePoint((0.0, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.6, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0) , 'AUTO_CLAMPED'),
    ])

bell_cubic_in_out_tail = Curve([
    CurvePoint((0.0, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0) , 'AUTO_CLAMPED'),
    CurvePoint((0.6, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.9, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0) , 'AUTO_CLAMPED'),
    ])

bell_quart_in_tail = Curve([
    CurvePoint((0.0, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.875, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)   , 'AUTO_CLAMPED'),
    ])

bell_quart_out_tail = Curve([
    CurvePoint((0.0, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.625, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)   , 'AUTO_CLAMPED'),
    ])

bell_quart_in_out_tail = Curve([
    CurvePoint((0.0, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)   , 'AUTO_CLAMPED'),
    CurvePoint((0.625, 0.97), 'AUTO_CLAMPED'),
    CurvePoint((0.875, 0.03), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)   , 'AUTO_CLAMPED'),
    ])

bell_quint_in_tail = Curve([
    CurvePoint((0.0, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.8625, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)     , 'AUTO_CLAMPED'),
    ])

bell_quint_out_tail = Curve([
    CurvePoint((0.0, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.6375, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)     , 'AUTO_CLAMPED'),
    ])

bell_quint_in_out_tail = Curve([
    CurvePoint((0.0, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.5, 1.0)     , 'AUTO_CLAMPED'),
    CurvePoint((0.6375, 0.975), 'AUTO_CLAMPED'),
    CurvePoint((0.8625, 0.025), 'AUTO_CLAMPED'),
    CurvePoint((1.0, 0.0)     , 'AUTO_CLAMPED'),
    ])