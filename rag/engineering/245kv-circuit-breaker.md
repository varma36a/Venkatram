# Engineering Guidelines — 245 kV Circuit Breakers (AIS)

Typical outdoor AIS circuit breaker envelope guidance for modeling (company reference, not a substitute for OEM datasheet).

## Typical ranges
- Height: 2800–4000 mm
- Width: 1500–2500 mm
- Depth: 1000–2000 mm
- Terminals: commonly 3-phase top/side exits

## Modeling notes
- Model interrupter poles as part of envelope in Coarse/Medium.
- Place three electrical connectors when `terminal_count = 3`.
- Mounting: steel structure / foundation frame — represent as base plate thickness ≤ 50 mm if shown on CAD.

## Validation tolerances
- Linear dimensions: ±5 mm vs accepted spec
- Weight: ±1% or ±5 kg (whichever larger)
- Connector count must equal `terminal_count`
