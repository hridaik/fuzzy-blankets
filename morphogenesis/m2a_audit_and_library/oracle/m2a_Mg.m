function g = m2a_Mg(x,v,P)
% generative model mapping (identical to SPM Mg) with M2A ramp modes.
global t
[s, ~] = m2a_ramp(t);
p = spm_softmax(v);
g.x = P.x*p; g.s = P.s*p; g.c = s*P.c*p;
end
