| Case | Do nothing | Simple rule | Search, 10 uses | Agent, no calculator | Agent, calculator |
|---|---|---|---|---|---|
| under extrusion z10 | 95.5% | 100.3% | 97.9% | 95.1% | 97.5% |
| under extrusion z50 | 95.5% | 97.9% | 97.5% | 95.7% | 95.8% |
| under extrusion z80 | 95.5% | 95.5% | 95.9% | 95.5% | 95.6% |
| over extrusion z10 | 107.2% | 100.2% | 101.1% | 107.2% | 100.1% |
| over extrusion z50 | 107.2% | 99.6% | 99.0% | 107.2% | 100.2% |
| over extrusion z80 | 107.2% | 100.5% | 100.5% | 103.5% | 101.5% |
| layer shift z10 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| layer shift z50 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| layer shift z80 | 100.0% | 100.0% | 100.0% | 100.0% | 100.0% |
| warpage z10 | 99.5% | 99.5% | 99.5% | 99.5% | 99.8% |
| warpage z50 | 99.5% | 99.5% | 99.9% | 99.5% | 100.0% |
| warpage z80 | 99.5% | 99.5% | 99.9% | 99.5% | 99.5% |

| Method | Average stiffness error | Average peak-force error |
|---|---|---|
| Do nothing | 3.05% | 2.00% |
| Simple rule | 0.79% | 0.90% |
| Search, 10 uses | 1.01% | 0.82% |
| Search, 200 uses | 0.41% | 0.60% |
| Agent, no calculator | 2.76% | 1.84% |
| Agent, calculator | 1.17% | 0.96% |

Agent with calculator, case by case (tie = within 0.5 points):
- vs simple rule: {'wins': 0, 'ties': 9, 'losses': 3}
- vs search, 10 uses: {'wins': 2, 'ties': 8, 'losses': 2}
- vs agent without calculator: {'wins': 4, 'ties': 8, 'losses': 0}
- calculator uses per run: 4.8 overall, 7.5 on under/over-extrusion, 2.0 on layer shift/warpage
