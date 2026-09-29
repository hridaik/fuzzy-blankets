function g = dem_morphogenesis_Mg(x,v,P)
% Verbatim transcription of local function `Mg` in DEM_morphogenesis.m
% (SPM12 toolbox/DEM), lines 395-410. global t preserved exactly.
global t
if isempty(t);
    s = 0;
else
    s = (1 - exp(-t*2));
end

p    = spm_softmax(v);

g.x  = P.x*p;
g.s  = P.s*p;
g.c  = s*P.c*p;
end
