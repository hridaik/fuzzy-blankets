function run_pio_lopez_variant(k, N, seed, outpath)
% Extracts the hard-coded v matrix from the k-cell morphopsy variant file
% (sources/morphopsy/DEM_morphogenesis_highexpectation_identity_<k>cell.m)
% via a regexp over its source text (so we use ITS EXACT matrix, not a
% reimplementation), then runs it through dem_setup+spm_ADEM exactly like
% every other config. CODE-BASED perturbation, per PERTURBATIONS.md.
if nargin < 2; N = 32; end
if nargin < 3; seed = 0; end
if nargin < 4; outpath = sprintf('data/oracle_traces/pio_lopez_k%d_N%d_seed%d.mat', k, N, seed); end

fname = sprintf('sources/morphopsy/DEM_morphogenesis_highexpectation_identity_%dcell.m', k);
txt = fileread(fname);

% extract the "v = [ ... ];  % states (identity)" block
tok = regexp(txt, 'v\s*=\s*\[(.*?)\];\s*%\s*states \(identity\)', 'tokens', 'once');
if isempty(tok)
    error('could not find v matrix in %s', fname);
end
v_str = tok{1};
v_override = eval(['[' v_str ']']);

run_and_export(2, N, seed, outpath, v_override);
end
