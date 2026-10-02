function direct_morph(L, N, seed, v0file, outpath)
% PART 0.2 independent cross-check: hand-written, minimal. Re-types the
% setup of SPM12 toolbox/DEM/DEM_morphogenesis.m (template, generative
% process/model) and calls spm_ADEM DIRECTLY. Uses NONE of m0b/m0c/m1
% oracle code (no dem_setup, no run_and_export, no fallback engine).
% v0file: '' -> draw v = randn(n,n)/8 after rand/randn('seed',seed)
%         else .mat with variable v0 (n x n).
% Noise: seeds reset to `seed` immediately before spm_ADEM (so the noise
% sequence is independent of how v0 was obtained).
global t
clear global t
rand('seed',seed); randn('seed',seed);
M(1).E.d = 1; M(1).E.n = 2; M(1).E.s = 1;
if L == 2
  T = [0 0 2 0 0 0 0 0 0 0 0; 0 0 0 0 1 0 0 0 0 0 0; 2 0 0 0 0 0 4 0 4 0 3;
       0 0 0 0 1 0 0 0 0 0 0; 0 0 2 0 0 0 0 0 0 0 0; 0 0 0 0 0 0 0 0 0 0 0];
  % NB: row 5 above is written independently; verified against SPM source in tests
else
  error('L=2 only');
end
p(:,:,1) = T > 0; p(:,:,2) = T == 2 | T == 1; p(:,:,3) = T == 3 | T == 1; p(:,:,4) = T == 4;
[y,x] = find(p(:,:,1));
P.x = spm_detrend([x(:) y(:)])'/2;
n = size(P.x,2); m = size(p,3); j = find(p(:,:,1));
for i = 1:m; s = p(:,:,i); P.s(i,:) = s(j); end
P.s = double(P.s);
P.c = dm_field(P.x,P.s);
if isempty(v0file); v = randn(n,n)/8; else; S = load(v0file); v = S.v0; end
g = dm_Mg([],v,P); a.x = g.x; a.s = g.s;
R = spm_cat({kron(eye(n,n),ones(2,2)) []; [] kron(eye(n,n),ones(4,4)); kron(eye(n,n),ones(4,2)) kron(eye(n,n),ones(4,4))});
G(1).g = @(x,v,a,P) dm_Gg(x,v,a,P);
G(1).v = dm_Gg([],[],a,a); G(1).V = exp(16); G(1).U = exp(2); G(1).R = R; G(1).pE = a;
G(2).a = spm_vec(a); G(2).v = 0; G(2).V = exp(16);
M(1).g = @(x,v,P) dm_Mg([],v,P); M(1).v = g; M(1).V = exp(3); M(1).pE = P;
M(2).v = v; M(2).V = exp(-2);
DEM.M = M; DEM.G = G; DEM.C = zeros(1,N); DEM.U = zeros(n*n,N); DEM.db = 0;
rand('seed',seed); randn('seed',seed);
tic; DEM = spm_ADEM(DEM); elapsed = toc;
positions = DEM.qU.a{2}(1:2*n,:); secretion = DEM.qU.a{2}(2*n+1:6*n,:);
v_expect = DEM.qU.v{2}; v_initial = v;
save('-v7', outpath, 'positions','secretion','v_expect','v_initial','elapsed','N','seed');
end
function c = dm_field(x,s,y)
if nargin < 3; y = x; end
n = size(y,2); m = size(s,1); c = zeros(m,n);
for i = 1:n; for j = 1:size(x,2)
  d = y(:,i) - x(:,j); d = sqrt(d'*d); c(:,i) = c(:,i) + exp(-d).*s(:,j);
end; end
end
function g = dm_Gg(x,v,a,P)
global t
if isempty(t); s = 0; else; s = (1 - exp(-t*2)); end
a = spm_unvec(a,P);
g.x(1,:) = a.x(1,:); g.x(2,:) = a.x(2,:); g.s = a.s; g.c = s*dm_field(a.x,a.s);
end
function g = dm_Mg(x,v,P)
global t
if isempty(t); s = 0; else; s = (1 - exp(-t*2)); end
p = spm_softmax(v); g.x = P.x*p; g.s = P.s*p; g.c = s*P.c*p;
end
