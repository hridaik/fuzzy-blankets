function run_and_export(L, N, seed, outpath, v_override)
% Runs the unmodified spm_ADEM (only DEM.db=0 patch) on a dem_setup()
% configuration, exports golden trace + the exact noise draws spm_ADEM used,
% to a .mat file (v7, scipy.io.loadmat-compatible).
if nargin < 1; L = 2; end
if nargin < 2; N = 32; end
if nargin < 3; seed = 0; end
if nargin < 4; outpath = sprintf('../data/oracle_traces/L%d_N%d_seed%d.mat', L, N, seed); end
if nargin < 5; v_override = []; end

DEM = dem_setup(L, N, seed, v_override);

% capture the exact noise draws spm_ADEM will use: same seed, replicate
% spm_ADEM_set's G(1).E fill-in (spm_ADEM.m lines 163-164) then call
% spm_DEM_z once to record z,w, then reset the seed so spm_ADEM's own
% internal call to spm_DEM_z reproduces the identical sequence.
DEM_probe = spm_ADEM_set(DEM);
DEM_probe.G(1).E.n = DEM_probe.M(1).E.n;
DEM_probe.G(1).E.d = DEM_probe.M(1).E.n;
rand('seed', seed); randn('seed', seed);
[z_exported, w_exported] = spm_DEM_z(DEM_probe.G, N);
rand('seed', seed); randn('seed', seed);

tic;
DEM = spm_ADEM(DEM);
elapsed = toc;

n = size(DEM.M(1).pE.x, 2);
m = size(DEM.M(1).pE.s, 1);

% observable-equivalent
% NB (empirically confirmed via Octave introspection, not assumed): action
% lives in DEM.qU.a{2} (48 x N for n=8), because G has nl=2 "levels" and
% only G(2).a is a real action vector -- G(1).a is unset so QU.a{1} is 0-dim.
% QU.v{1}/QU.v{2} are HIERARCHICAL LEVELS (sensory reconstruction / identity
% cause), NOT generalized temporal orders -- a naming collision in SPM's own
% convention that this session resolved empirically rather than by
% assumption. See ORACLE_REPORT.md.
positions  = DEM.qU.a{2}(1:2*n, :);           % a.x, flattened (2n x N)
secretion  = DEM.qU.a{2}(2*n+1:2*n+4*n, :);   % a.s, flattened (4n x N)
predicted_sensation = DEM.qU.v{1};   % (80 x N for n=8) level-1 reconstruction

% hidden-tier
v_expect   = DEM.qU.v{2};      % (n*n x N) identity cause (level 2)
pred_err_1 = DEM.qU.z{1};      % sensory prediction error (level 1)
pred_err_2 = DEM.qU.z{2};      % causal (identity) prediction error (level 2)
free_energy_J = DEM.J;         % per-sample free energy (since nE==1)
free_energy_F = DEM.F;         % per E-step free energy

t_vals = (1:N) / N;
dev_factor = 1 - exp(-2*t_vals);

target_x = DEM.M(1).pE.x;
target_s = DEM.M(1).pE.s;
target_c = DEM.M(1).pE.c;

save('-v7', outpath, 'positions', 'secretion', 'predicted_sensation', ...
     'v_expect', 'pred_err_1', 'pred_err_2', 'free_energy_J', 'free_energy_F', ...
     't_vals', 'dev_factor', 'target_x', 'target_s', 'target_c', 'n', 'm', ...
     'N', 'L', 'seed', 'elapsed', 'z_exported', 'w_exported');

fprintf('saved %s (n=%d, N=%d, elapsed=%.2fs)\n', outpath, n, N, elapsed);
end
