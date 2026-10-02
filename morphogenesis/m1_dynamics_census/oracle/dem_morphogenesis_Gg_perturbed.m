function g = dem_morphogenesis_Gg_perturbed(x,v,a,P)
% Perturbable copy of m0b's dem_morphogenesis_Gg.m (itself a verbatim
% transcription of DEM_morphogenesis.m's local fn Gg). Configured via the
% global PERTURBATION struct (set by run_perturbed.m before calling
% spm_ADEM) so G(1).g = @(x,v,a,P) dem_morphogenesis_Gg_perturbed(x,v,a,P)
% can be bound once and behave differently per bin (for ramped onset).
%
% PERTURBATION.kind: 'none' | 'kuchling_head' | 'kuchling_tail' |
%   'kuchling_rescue' | 'friston_scale' |
%   'kuchling_rescue_text' | 'kuchling_rescue_caption'  (M1 PART A additions
%   -- see ../../m1_dynamics_census/RESCUE_FIX.md for the implementation-gap
%   this fixes: m0c's 'kuchling_rescue' never paired the sqrt-kernel fix
%   with the anomaly it was meant to rescue)
% PERTURBATION.cells: 1-based cell indices affected (empty = all).
%   NOTE: M0c's docstring said "0-based" but Octave arrays are always
%   1-indexed and M0c's own batch driver passed indices that Octave
%   silently treated as 1-based (cell index 0 errored -- see M0c
%   PERTURBATIONS_EXECUTED.md). This M1 copy documents the TRUE (1-based)
%   convention; callers must pass 1-based cell indices.
% PERTURBATION.ramp_w: raised-cosine ramp width in bins (0 = no ramp, instant)
% PERTURBATION.ramp_onset_bin: bin (1-indexed) at which ramp starts
% PERTURBATION.friston_channel: 'position_all'|'position_row1'|'secretion'|'sig2'|'sig3'
% PERTURBATION.friston_factor: scalar multiplier
% PERTURBATION.rescue_factor: (kuchling_rescue_caption only) sensitivity
%   multiplier applied to the OTHER (non-anomalous) cells' g.c channel
global t
global PERTURBATION

if isempty(t); s = 0; else; s = (1 - exp(-t*2)); end
a = spm_unvec(a,P);

g.x(1,:) = a.x(1,:);
g.x(2,:) = a.x(2,:);
g.s      = a.s;

if isempty(PERTURBATION) || strcmp(PERTURBATION.kind, 'none')
    g.c = s*dem_morphogenesis_field(a.x,a.s);
    return
end

ramp = perturbation_ramp_factor();
n = size(a.x,2);
cells = PERTURBATION.cells;
if isempty(cells); cells = 1:n; end

switch PERTURBATION.kind
    case {'kuchling_head','kuchling_tail'}
        % Row-1 (long-axis) POSITIONAL SENSATION replaced by +/-(position)^2,
        % ramped: g.x(1,cell) = (1-ramp)*a.x(1,cell) + ramp*sign*(a.x(1,cell))^2
        sgn = 1;
        if strcmp(PERTURBATION.kind, 'kuchling_tail'); sgn = -1; end
        for c = cells
            g.x(1,c) = (1-ramp)*a.x(1,c) + ramp*sgn*(a.x(1,c)^2);
        end
        g.c = s*dem_morphogenesis_field(a.x,a.s);

    case 'kuchling_rescue'
        % DISCLOSED GAP, KEPT FOR REPRODUCIBILITY OF THE M0c RESULT ONLY:
        % this applies the sqrt-distance kernel WITHOUT the accompanying
        % anomaly, so it trivially reproduces baseline. Do not use for new
        % work -- use 'kuchling_rescue_text' or 'kuchling_rescue_caption'.
        g.c = s*dem_field_sqrt_for_cells(a.x,a.s,cells,ramp);

    case 'kuchling_rescue_text'
        % PART A, R-text (Kuchling 2020 eq. 50): the anomalous cell(s) get
        % BOTH the squared-position distortion (sign from
        % PERTURBATION.anomaly_sign, default +1 = "head"-type) AND the
        % sqrt-distance field kernel on their OWN receiving field.
        sgn = 1;
        if isfield(PERTURBATION,'anomaly_sign'); sgn = PERTURBATION.anomaly_sign; end
        for c = cells
            g.x(1,c) = (1-ramp)*a.x(1,c) + ramp*sgn*(a.x(1,c)^2);
        end
        g.c = s*dem_field_sqrt_for_cells(a.x,a.s,cells,ramp);

    case 'kuchling_rescue_caption'
        % PART A, R-caption (Kuchling 2020 Fig. 5C caption): the anomalous
        % cell(s) get ONLY the squared-position distortion (no self-fix);
        % ALL OTHER cells get their extracellular sensitivity (g.c) scaled
        % up by PERTURBATION.rescue_factor (the caption's "increased
        % signalling sensitivity of the other cells").
        sgn = 1;
        if isfield(PERTURBATION,'anomaly_sign'); sgn = PERTURBATION.anomaly_sign; end
        for c = cells
            g.x(1,c) = (1-ramp)*a.x(1,c) + ramp*sgn*(a.x(1,c)^2);
        end
        g.c = s*dem_morphogenesis_field(a.x,a.s);
        rf = 1.0;
        if isfield(PERTURBATION,'rescue_factor'); rf = PERTURBATION.rescue_factor; end
        factor_eff = 1 + ramp*(rf - 1);
        others = setdiff(1:n, cells);
        g.c(:,others) = factor_eff * g.c(:,others);

    case 'friston_scale'
        g.c = s*dem_morphogenesis_field(a.x,a.s);
        factor_eff = 1 + ramp*(PERTURBATION.friston_factor - 1);
        switch PERTURBATION.friston_channel
            case 'position_all'
                g.x(:,cells) = factor_eff * g.x(:,cells);
            case 'position_row1'
                g.x(1,cells) = factor_eff * g.x(1,cells);
            case 'secretion'
                g.s(:,cells) = factor_eff * g.s(:,cells);
            case 'sig2'
                g.c(2,cells) = factor_eff * g.c(2,cells);
            case 'sig3'
                g.c(3,cells) = factor_eff * g.c(3,cells);
        end

    case 'sham'
        % Part E: s_x = x + Delta_sham(x), Delta_sham a random smooth field
        % (random Fourier features -- PERTURBATION.sham_freqs: Kx2 matrix of
        % (fx,fy) frequencies; PERTURBATION.sham_phases_x/_y: K-vectors;
        % PERTURBATION.sham_scale: RMS-matching amplitude, calibrated in
        % Python against that individual's SUSTAINED-DH twin -- see
        % code/run_sham.py / SHAM.md). Applied to BOTH coordinates via two
        % independently-phased draws from the same frequency family.
        for c = cells
            dx = sham_field(a.x(1,c), a.x(2,c), PERTURBATION.sham_freqs, ...
                             PERTURBATION.sham_phases_x, PERTURBATION.sham_scale);
            dy = sham_field(a.x(1,c), a.x(2,c), PERTURBATION.sham_freqs, ...
                             PERTURBATION.sham_phases_y, PERTURBATION.sham_scale);
            g.x(1,c) = (1-ramp)*a.x(1,c) + ramp*(a.x(1,c) + dx);
            g.x(2,c) = (1-ramp)*a.x(2,c) + ramp*(a.x(2,c) + dy);
        end
        g.c = s*dem_morphogenesis_field(a.x,a.s);

    otherwise
        error('unknown PERTURBATION.kind %s', PERTURBATION.kind);
end
end

function d = sham_field(x1, x2, freqs, phases, scale)
K = size(freqs,1);
d = 0;
for k = 1:K
    d = d + cos(2*pi*(freqs(k,1)*x1 + freqs(k,2)*x2) + phases(k));
end
d = scale * d / sqrt(K/2);  % normalize so RMS of the SUM is ~scale (each
                             % cosine term has RMS 1/sqrt(2); sum of K
                             % independent-phase terms has RMS sqrt(K/2))
end

function r = perturbation_ramp_factor()
% M1 addition: supports an OFF bin (withdrawal) via PERTURBATION.off_bin
% (empty/absent = perturbation is sustained, never switched off -- matches
% M0c's behaviour exactly when off_bin is unset, so this is backward
% compatible). Onset and offset each use the same raised-cosine width
% PERTURBATION.ramp_w. If off_bin is set, r ramps 0->1 at onset, holds at
% 1, then ramps 1->0 starting at off_bin over ramp_w bins.
global PERTURBATION
global t
if isempty(t); r = 0; return; end
w = 0;
onset = 1;
if isfield(PERTURBATION,'ramp_w'); w = PERTURBATION.ramp_w; end
if isfield(PERTURBATION,'ramp_onset_bin'); onset = PERTURBATION.ramp_onset_bin; end
if isfield(PERTURBATION,'n_bins'); nb = PERTURBATION.n_bins; else; nb = 32; end
bin = round(t*nb);

r_on = onset_ramp(bin, onset, w);

off_bin = [];
if isfield(PERTURBATION,'off_bin'); off_bin = PERTURBATION.off_bin; end
if isempty(off_bin)
    r = r_on;
    return
end
r_off = 1 - onset_ramp(bin, off_bin, w);  % mirrors onset_ramp, descending
r = min(r_on, r_off);
end

function r = onset_ramp(bin, onset, w)
if w <= 0
    r = 1.0 * (bin >= onset);
    return
end
progress = (bin - onset) / w;
if progress <= 0
    r = 0;
elseif progress >= 1
    r = 1;
else
    r = 0.5 * (1 - cos(pi*progress));  % raised cosine
end
end

function c = dem_field_sqrt_for_cells(x,s,cells,ramp)
n = size(x,2);
m = size(s,1);
k = 1;
c = zeros(m,n);
for i = 1:n
    for j = 1:size(x,2)
        d = x(:,i) - x(:,j);
        d = sqrt(d'*d);
        if any(cells == i)
            d_eff = (1-ramp)*d + ramp*sqrt(d);
        else
            d_eff = d;
        end
        c(:,i) = c(:,i) + exp(-k*d_eff).*s(:,j);
    end
end
end
