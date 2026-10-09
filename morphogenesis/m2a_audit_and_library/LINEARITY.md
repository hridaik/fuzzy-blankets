# LINEARITY.md — linearity of the pulse response (protocol v2, revised library)

**Status: DONE for the declared subset; ESTABLISHED within it.** Subset (declared in LIBRARY.md): roles {0, 3, 5} × 10 channels × {sign reversed, amplitude ×2}, on C0, C1 and D32; 90 positive/negative pairs and 90 positive/doubled pairs. Amplitude 0.03, width 4 bins, 192-bin window. Code `code/p2r_analyze.py`; rows in `data/v2/p2r_results.json` (`linearity`).

Definitions (R(a) = response trajectory, base minus its own twin, over the window):
- **sign error** = ‖R(−a) + R(a)‖ / ‖R(a)‖ (0 for an odd response);
- **×2 error** = ‖R(2a) − 2R(a)‖ / ‖2R(a)‖ (0 for a linear response).
Criterion (pre-declared in the pilot): error < 5 % for every run of a channel.

## Result
| base | n | median sign error | median ×2 error | sign < 5 % | ×2 < 5 % |
|---|---|---|---|---|---|
| C0 | 30 | 1.8 % | 0.93 % | 27/30 (90 %) | 30/30 |
| C1 | 30 | 1.6 % | 0.80 % | 29/30 (97 %) | 30/30 |
| D32 | 30 | 1.8 % | 0.90 % | 28/30 (93 %) | 30/30 |

Per channel (maximum over the three bases and three roles; each cell n = 9):
| channel | max sign error | max ×2 error | meets 5 % |
|---|---|---|---|
| pos x | 2.8 % | 1.4 % | yes |
| pos y | 5.0 % | 2.5 % | marginal (4.97 %) |
| sec 1 | 1.9 % | 1.0 % | yes |
| sec 2 | 2.7 % | 1.4 % | yes |
| sec 3 | 2.4 % | 1.2 % | yes |
| sec 4 | 1.6 % | 0.8 % | yes |
| gain 1 | **7.3 %** | 3.5 % | **no** (sign) |
| gain 2 | 4.9 % | 2.2 % | marginal |
| gain 3 | 1.8 % | 0.8 % | yes |
| gain 4 | **5.5 %** | 2.6 % | **no** (sign) |

## Reading
- **Amplitude scaling holds for every channel** (×2 error ≤ 3.5 %, 90/90). **Sign reversal holds for 7 of 10 channels and fails the 5 % criterion for gain 1 and gain 4**, with pos y and gain 2 within 0.1 of the limit. The asymmetry is in the odd part: the positive and negative responses are not mirror images by 5–7 % of their norm for those channels. These are the two most effective channels (gain 1: largest response norm, LIBRARY.md), so the departure is plausibly the first nonlinear term (quadratic in the pulse) of a strongly coupled channel; this is a reading, not a test.
- Maximum sign error by role: role 0 7.3 %, role 3 5.2 %, role 5 2.8 %. Three roles, so no role-dependence claim is made.
- **Operational statement:** at amplitude 0.03 the response is linear to within 5 % for position and secretion channels and for gain 3; gain channels 1 and 4 are linear in amplitude but not odd to 5 %. Treating the response as linear in a downstream analysis should carry a 7 % error allowance for gain 1.
- **Not tested:** amplitudes other than 0.03 and 0.06 (so no estimate of the linear range), roles outside {0, 3, 5}, other bases, multi-cell pulses, superposition of two pulses. The thresholds in MINIMAL_PERTURBATIONS.md are at amplitudes ≈ 100× larger, where the response is certainly nonlinear (it is a switch); linearity here says nothing about that regime.
