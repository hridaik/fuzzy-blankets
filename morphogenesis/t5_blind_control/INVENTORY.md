# INVENTORY (T5, Part 0)
Smoke test (dev seed 5000, episode 1; code/smoke.py), live client only.
- Levels O1,O2,O3a,O3b,O3c all return frames at t=0; observe is ~free in budget and fast (O1 1 ms, O3c 29 ms).
- Actuators: light labels L1..L5 (effects unknown). Masks: disc / halfplane / all.
- act(L1, disc r=2, amp 0.1, dur 5, ramp 1): dose=6.0 = 0.1*5*12 cells (matches API formula). Counts as 1 action.
- step(10) = 0.17 s wall => ~60 tu/s (single call, incl. overhead). Wall-clock is NOT binding.
- Dev pool: seeds 5000-5399 (400). Held-out pool locked.
- Budgets (status): session 200 episodes, 60000 tu, 400000 dose. Per episode 600 tu, 20000 dose, 20 actions.
- Used so far: 1 episode, 30 tu, dose 6.
- Twin = reset(same seed) with no action; sham = reset(sham_of=episode) (not yet tested).
## Binding constraint: EPISODES (200 total, shared by dev + held-out) and 60000 tu (=300 tu/episode average).
The brief's held-out design (>=30 dishes/direction x 6 arms >= 360 episodes) alone exceeds the session cap.
