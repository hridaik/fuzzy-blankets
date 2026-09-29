function DEM = dem_setup_vanilla8(N, seed)
% Headless re-implementation of DEM_morphogenesis.m's SETUP portion only
% (preliminaries through "solve" -- lines 1-150 of the SPM12 source), with
% all graphics code removed. This is a disclosed, minimal, non-numeric
% patch: verbatim transcription of the setup, no equations changed.
% See ORACLE_REPORT.md for the diff against the original.
if nargin < 1; N = 32; end
if nargin < 2; seed = 0; end

clear global
rand('seed', seed);
randn('seed', seed);

M(1).E.d = 1;
M(1).E.n = 2;
M(1).E.s = 1;

L = 2;
T = [0 0 2 0 0 0 0 0 0 0 0;
     0 0 0 0 1 0 0 0 0 0 0;
     2 0 0 0 0 0 4 0 4 0 3;
     0 0 0 0 1 0 0 0 0 0 0;
     0 0 2 0 0 0 0 0 0 0 0;
     0 0 0 0 0 0 0 0 0 0 0];

p(:,:,1) = T > 0;
p(:,:,2) = T == 2 | T == 1;
p(:,:,3) = T == 3 | T == 1;
p(:,:,4) = T == 4;

[y,x] = find(p(:,:,1));
P.x   = spm_detrend([x(:) y(:)])'/2;

n     = size(P.x,2);
m     = size(p,3);
j     = find(p(:,:,1));
for i = 1:m
    s        = p(:,:,i);
    P.s(i,:) = s(j);
end
P.s   = double(P.s);
P.c   = dem_morphogenesis_field(P.x,P.s);

v     = randn(n,n)/8;
g     = dem_morphogenesis_Mg([],v,P);
a.x   = g.x;
a.s   = g.s;

R     = spm_cat({kron(eye(n,n),ones(2,2)) []; [] kron(eye(n,n),ones(4,4));
                 kron(eye(n,n),ones(4,2)) kron(eye(n,n),ones(4,4))});

G(1).g  = @(x,v,a,P) dem_morphogenesis_Gg(x,v,a,P);
G(1).v  = dem_morphogenesis_Gg([],[],a,a);
G(1).V  = exp(16);
G(1).U  = exp(2);
G(1).R  = R;
G(1).pE = a;

G(2).a  = spm_vec(a);
G(2).v  = 0;
G(2).V  = exp(16);

M(1).g  = @(x,v,P) dem_morphogenesis_Mg([],v,P);
M(1).v  = g;
M(1).V  = exp(3);
M(1).pE = P;

M(2).v  = v;
M(2).V  = exp(-2);

U     = zeros(n*n,N);
C     = zeros(1,N);

DEM.M = M;
DEM.G = G;
DEM.C = C;
DEM.U = U;
end
