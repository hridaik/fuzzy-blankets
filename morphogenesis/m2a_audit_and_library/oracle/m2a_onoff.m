function r = m2a_onoff(bin, onset, off, w)
% On/off raised-cosine switching factor in [0,1] (M1 semantics: ramp up over w bins from `onset`, hold,
% ramp down over w bins from `off`; off = [] or Inf -> never switched off). Absolute bins.
r_on = ramp1(bin, onset, w);
if isempty(off) || isinf(off); r = r_on; return; end
r = min(r_on, 1 - ramp1(bin, off, w));
end
function r = ramp1(bin, onset, w)
if w <= 0; r = 1.0*(bin >= onset); return; end
pr = (bin - onset)/w;
if pr <= 0; r = 0; elseif pr >= 1; r = 1; else; r = 0.5*(1 - cos(pi*pr)); end
end
