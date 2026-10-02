function DEM = dem_setup_from_state(L, N, seed, v0, a_x0, a_s0, perturbed)
% Generalized setup for Part C (kicks) and Part D (ADULT-timing withdrawal):
% like m0b's dem_setup.m / m0c's dem_setup_perturbed.m, but action (a.x,
% a.s) can be set INDEPENDENTLY of v (needed for kicks that displace
% position/secretion without touching the identity belief, or vice versa).
% If a_x0/a_s0 are empty, falls back to a.x=Mg(v).x, a.s=Mg(v).s (the
% standard initialization), matching the original scripts exactly.
% perturbed: if true, binds G(1).g to dem_morphogenesis_Gg_perturbed (M1
% copy, which supports withdrawal on/off -- see that file); else the plain
% dem_morphogenesis_Gg.
if nargin < 1; L = 2; end
if nargin < 2; N = 512; end
if nargin < 3; seed = 0; end
if nargin < 4; v0 = []; end
if nargin < 5; a_x0 = []; end
if nargin < 6; a_s0 = []; end
if nargin < 7; perturbed = false; end

rand('seed', seed); randn('seed', seed);

M(1).E.d = 1; M(1).E.n = 2; M(1).E.s = 1;

if L == 2
    T = [0 0 2 0 0 0 0 0 0 0 0;
         0 0 0 0 1 0 0 0 0 0 0;
         2 0 0 0 0 0 4 0 4 0 3;
         0 0 0 0 1 0 0 0 0 0 0;
         0 0 2 0 0 0 0 0 0 0 0;
         0 0 0 0 0 0 0 0 0 0 0];
else
    error('only L=2 supported in dem_setup_from_state');
end

p(:,:,1) = T > 0; p(:,:,2) = T==2|T==1; p(:,:,3) = T==3|T==1; p(:,:,4) = T==4;
[y,x] = find(p(:,:,1));
P.x = spm_detrend([x(:) y(:)])'/2;
n = size(P.x,2); m = size(p,3);
j = find(p(:,:,1));
for i = 1:m
    s = p(:,:,i); P.s(i,:) = s(j);
end
P.s = double(P.s);
P.c = dem_morphogenesis_field(P.x,P.s);

if isempty(v0); v = randn(n,n)/8; else; v = v0; end
g = dem_morphogenesis_Mg([], v, P);
if isempty(a_x0); a.x = g.x; else; a.x = a_x0; end
if isempty(a_s0); a.s = g.s; else; a.s = a_s0; end

R = spm_cat({kron(eye(n,n),ones(2,2)) []; [] kron(eye(n,n),ones(4,4));
             kron(eye(n,n),ones(4,2)) kron(eye(n,n),ones(4,4))});

if perturbed
    G(1).g = @(x,v,a,P) dem_morphogenesis_Gg_perturbed(x,v,a,P);
    G(1).v = dem_morphogenesis_Gg_perturbed([],[],a,a);
else
    G(1).g = @(x,v,a,P) dem_morphogenesis_Gg(x,v,a,P);
    G(1).v = dem_morphogenesis_Gg([],[],a,a);
end
G(1).V = exp(16);
G(1).U = exp(2);
G(1).R = R;
G(1).pE = a;

G(2).a = spm_vec(a); G(2).v = 0; G(2).V = exp(16);

M(1).g = @(x,v,P) dem_morphogenesis_Mg([],v,P);
M(1).v = g;
M(1).pE = P;
M(1).V = exp(3);

M(2).v = v; M(2).V = exp(-2);

U = zeros(n*n,N); C = zeros(1,N);

DEM.M = M; DEM.G = G; DEM.C = C; DEM.U = U; DEM.db = 0;
end
