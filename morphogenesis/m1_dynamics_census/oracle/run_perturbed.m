function run_perturbed(kind, params, N, seed, outpath)
% General perturbation driver -- Part C. `kind`/`params` define the global
% PERTURBATION struct consumed by dem_morphogenesis_Gg_perturbed.m.
% params fields used depend on kind; see PERTURBATIONS_EXECUTED.md.
global PERTURBATION
global t

PERTURBATION = params;
PERTURBATION.kind = kind;
PERTURBATION.n_bins = N;
if ~isfield(PERTURBATION,'ramp_w'); PERTURBATION.ramp_w = 0; end
if ~isfield(PERTURBATION,'ramp_onset_bin'); PERTURBATION.ramp_onset_bin = 1; end
if ~isfield(PERTURBATION,'cells'); PERTURBATION.cells = []; end

v_override = [];
if isfield(params,'v_override'); v_override = params.v_override; end
sp_override = [];
if isfield(params,'sensory_precision'); sp_override = params.sensory_precision; end

DEM = dem_setup_perturbed(2, N, seed, v_override, sp_override, []);

tic;
DEM = spm_ADEM(DEM);
elapsed = toc;

n = size(DEM.M(1).pE.x, 2);
m = size(DEM.M(1).pE.s, 1);

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
perturbation_kind = kind;

save('-v7', outpath, 'positions', 'secretion', 'predicted_sensation', ...
     'v_expect', 'pred_err_1', 'pred_err_2', 'free_energy_J', 'free_energy_F', ...
     't_vals', 'dev_factor', 'target_x', 'target_s', 'target_c', 'n', 'm', ...
     'N', 'seed', 'elapsed', 'perturbation_kind');

fprintf('saved %s (n=%d N=%d elapsed=%.2fs)\n', outpath, n, N, elapsed);

clear global PERTURBATION
end
