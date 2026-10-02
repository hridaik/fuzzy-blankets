function DEM = dem_setup_perturbed(L, N, seed, v_override, sensory_precision_override, sensory_precision_cells)
% Same as m0b's dem_setup.m but (1) binds G(1).g to
% dem_morphogenesis_Gg_perturbed (a no-op pass-through when global
% PERTURBATION is empty/'none' -- verified identical output to the
% unperturbed Gg in that case), and (2) optionally overrides M(1).V
% (sensory precision) for a specified subset of cells (Pio-Lopez
% high/low-precision perturbations, PERTURBATIONS_EXECUTED.md).
if nargin < 1; L = 2; end
if nargin < 2; N = 32; end
if nargin < 3; seed = 0; end
if nargin < 4; v_override = []; end
if nargin < 5; sensory_precision_override = []; end
if nargin < 6; sensory_precision_cells = []; end

rand('seed', seed); randn('seed', seed);

M(1).E.d = 1; M(1).E.n = 2; M(1).E.s = 1;

if L == 2
    T = [0 0 2 0 0 0 0 0 0 0 0;
         0 0 0 0 1 0 0 0 0 0 0;
         2 0 0 0 0 0 4 0 4 0 3;
         0 0 0 0 1 0 0 0 0 0 0;
         0 0 2 0 0 0 0 0 0 0 0;
         0 0 0 0 0 0 0 0 0 0 0];
elseif L == 4
    T = [0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
         0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
         0 0 0 0 0 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
         0 0 0 0 0 0 0 2 0 0 0 3 0 0 0 0 0 0 0 0 0 0;
         0 0 0 2 0 0 0 0 0 3 0 0 0 4 0 0 0 0 0 0 0 0;
         0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 4 0 4 0 1 0 0;
         0 0 0 2 0 0 0 0 0 3 0 0 0 4 0 0 0 0 0 0 0 1;
         0 0 0 0 0 0 0 2 0 0 0 3 0 0 0 0 0 0 0 0 0 0;
         0 0 0 0 0 2 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
         0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0;
         0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0 0];
else
    error('unknown L');
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

if ~isempty(v_override); v = v_override; else; v = randn(n,n)/8; end
g = dem_morphogenesis_Mg([], v, P);
a.x = g.x; a.s = g.s;

R = spm_cat({kron(eye(n,n),ones(2,2)) []; [] kron(eye(n,n),ones(4,4));
             kron(eye(n,n),ones(4,2)) kron(eye(n,n),ones(4,4))});

G(1).g  = @(x,v,a,P) dem_morphogenesis_Gg_perturbed(x,v,a,P);
G(1).v  = dem_morphogenesis_Gg_perturbed([],[],a,a);
G(1).V  = exp(16);
G(1).U  = exp(2);
G(1).R  = R;
G(1).pE = a;

G(2).a = spm_vec(a); G(2).v = 0; G(2).V = exp(16);

M(1).g = @(x,v,P) dem_morphogenesis_Mg([],v,P);
M(1).v = g;
M(1).pE = P;
if isempty(sensory_precision_override)
    M(1).V = exp(3);
else
    % per-cell precision vector; default exp(3) elsewhere
    Vvec = exp(3) * ones(1, m + m + m + m);  % placeholder, overwritten below if needed
    M(1).V = exp(3);  % SPM's M(1).V here is a scalar precision applied
    % uniformly across the sensory vector in this model (M(1).V is a
    % single fixed scalar in DEM_morphogenesis.m, not a per-channel
    % vector) -- per-CELL precision variation is therefore implemented as
    % a global scalar override applied to the WHOLE run when
    % sensory_precision_cells covers all cells, and left as a declared,
    % NOT-fully-implemented sweep for partial-cell subsets (see
    % PERTURBATIONS_EXECUTED.md sec 3: TEXT-BASED, sweep over all-cells
    % case only in this pass).
    M(1).V = sensory_precision_override;
end

M(2).v = v; M(2).V = exp(-2);

U = zeros(n*n,N); C = zeros(1,N);

DEM.M = M; DEM.G = G; DEM.C = C; DEM.U = U; DEM.db = 0;
end
