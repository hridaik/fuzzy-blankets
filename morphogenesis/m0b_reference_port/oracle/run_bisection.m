function run_bisection(SPLIT, N, seed, outpath)
% Verbatim transcription of DEM_morphogenesis.m's dormant SPLIT block
% (lines 153-190), which is never executed in the shipped script
% (SPLIT=0 hard-coded there). SPLIT=1: top half (descending x) duplicated.
% SPLIT=2: bottom half (ascending x) duplicated. Bisection bin fixed at
% t=8 (source's own hard-coded value, matching the ground rules' "bin 8").
if nargin < 1; SPLIT = 1; end
if nargin < 2; N = 32; end
if nargin < 3; seed = 0; end
if nargin < 4; outpath = sprintf('data/oracle_traces/bisection_split%d_N%d_seed%d.mat', SPLIT, N, seed); end

DEM = dem_setup(2, N, seed);
DEM = spm_ADEM(DEM);

n = size(DEM.M(1).pE.x, 2);
tbin = 8;

v = spm_unvec(DEM.pU.v{1}(:,tbin), DEM.M(1).v);
if SPLIT > 1
    [~, j] = sort(v.x(1,:), 'ascend');
else
    [~, j] = sort(v.x(1,:), 'descend');
end
j = [j(1:floor(n/2)) j(1:floor(n/2))];

v = spm_unvec(DEM.qU.v{2}(:,tbin), DEM.M(2).v);
g = spm_unvec(DEM.qU.v{1}(:,tbin), DEM.M(1).v);
a = spm_unvec(DEM.qU.a{2}(:,tbin), DEM.G(1).pE);

v   = v(:,j);
g.x = g.x(:,j);
g.s = g.s(:,j);
g.c = g.c(:,j);
a.x = a.x(:,j) + randn(size(a.x))/512;
a.s = a.s(:,j) + randn(size(a.s))/512;

DEM.M(1).v = g;
DEM.M(2).v = v;
DEM.G(2).a = spm_vec(a);

tic;
DEM = spm_ADEM(DEM);
elapsed = toc;

positions  = DEM.qU.a{2}(1:2*n, :);
secretion  = DEM.qU.a{2}(2*n+1:2*n+4*n, :);
predicted_sensation = DEM.qU.v{1};
v_expect   = DEM.qU.v{2};
pred_err_1 = DEM.qU.z{1};
pred_err_2 = DEM.qU.z{2};
free_energy_J = DEM.J;
free_energy_F = DEM.F;
t_vals = (1:N) / N;
dev_factor = 1 - exp(-2*t_vals);
target_x = DEM.M(1).pE.x;
target_s = DEM.M(1).pE.s;
target_c = DEM.M(1).pE.c;
duplication_index = j;   % which pre-split cell each post-split cell came from
m = size(DEM.M(1).pE.s,1);

save('-v7', outpath, 'positions', 'secretion', 'predicted_sensation', ...
     'v_expect', 'pred_err_1', 'pred_err_2', 'free_energy_J', 'free_energy_F', ...
     't_vals', 'dev_factor', 'target_x', 'target_s', 'target_c', 'n', 'm', ...
     'N', 'SPLIT', 'tbin', 'seed', 'elapsed', 'duplication_index');

fprintf('saved %s (n=%d, N=%d, elapsed=%.2fs)\n', outpath, n, N, elapsed);
end
