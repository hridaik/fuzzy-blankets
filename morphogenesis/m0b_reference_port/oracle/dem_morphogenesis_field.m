function c = dem_morphogenesis_field(x,s,y)
% Verbatim transcription of the local function `morphogenesis` in
% DEM_morphogenesis.m (SPM12 toolbox/DEM), lines 350-376.
if nargin < 3; y = x; end
n     = size(y,2);
m     = size(s,1);
k     = 1;
c     = zeros(m,n);
for i = 1:n
    for j = 1:size(x,2)
        d      = y(:,i) - x(:,j);
        d      = sqrt(d'*d);
        c(:,i) = c(:,i) + exp(-k*d).*s(:,j);
    end
end
end
