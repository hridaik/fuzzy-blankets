function run_sensitivity_pair(eps_mag, N, seed, outdir)
% A4: runs vanilla-8 baseline and a twin with initial v perturbed by a
% fixed-direction eps_mag magnitude (same perturbation DIRECTION reused
% across eps_mag values for comparability), saves both traces for
% deviation-growth analysis in Python.
if nargin < 1; eps_mag = 1e-10; end
if nargin < 2; N = 32; end
if nargin < 3; seed = 0; end
if nargin < 4; outdir = 'data/oracle_traces'; end

addpath('../m0b_reference_port/sources/spm12');
addpath('../m0b_reference_port/sources/spm12/toolbox/DEM');
addpath('../m0b_reference_port/oracle');

% baseline initial v (same construction as dem_setup/DEM_morphogenesis.m)
rand('seed', seed); randn('seed', seed);
n = 8;
v0 = randn(n,n)/8;

% fixed perturbation direction (unit-norm random matrix, seeded separately
% so it does not consume/alter the baseline's own RNG stream)
rand('seed', 999); randn('seed', 999);
direction = randn(n,n);
direction = direction / norm(direction(:));

v_perturbed = v0 + eps_mag * direction;

base_out = sprintf('%s/sens_base_N%d_seed%d.mat', outdir, N, seed);
pert_out = sprintf('%s/sens_pert_eps%.0e_N%d_seed%d.mat', outdir, eps_mag, N, seed);

run_and_export(2, N, seed, base_out, v0);
run_and_export(2, N, seed, pert_out, v_perturbed);

fprintf('done eps=%.0e\n', eps_mag);
end
