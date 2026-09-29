function g = dem_morphogenesis_Gg(x,v,a,P)
% Verbatim transcription of local function `Gg` in DEM_morphogenesis.m
% (SPM12 toolbox/DEM), lines 379-393. global t preserved exactly.
global t
if isempty(t);
    s = 0;
else
    s = (1 - exp(-t*2));
end
a        = spm_unvec(a,P);

g.x(1,:) = a.x(1,:);
g.x(2,:) = a.x(2,:);
g.s      = a.s;
g.c      = s*dem_morphogenesis_field(a.x,a.s);
end
