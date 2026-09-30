function g = dem_morphogenesis_Gg_perturbed(x,v,a,P)
% Perturbable copy of m0b's dem_morphogenesis_Gg.m (itself a verbatim
% transcription of DEM_morphogenesis.m's local fn Gg). Configured via the
% global PERTURBATION struct (set by run_perturbed.m before calling
% spm_ADEM) so G(1).g = @(x,v,a,P) dem_morphogenesis_Gg_perturbed(x,v,a,P)
% can be bound once and behave differently per bin (for ramped onset).
%
% PERTURBATION.kind: 'none' | 'kuchling_head' | 'kuchling_tail' |
%   'kuchling_rescue' | 'friston_scale'
% PERTURBATION.cells: 0-based cell indices affected (empty = all)
% PERTURBATION.ramp_w: raised-cosine ramp width in bins (0 = no ramp, instant)
% PERTURBATION.ramp_onset_bin: bin (1-indexed) at which ramp starts
% PERTURBATION.friston_channel: 'position_all'|'position_row1'|'secretion'|'sig2'|'sig3'
% PERTURBATION.friston_factor: scalar multiplier
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
        % sqrt-distance field kernel for the affected cell's OWN sensing
        % (attenuates falloff). Only meaningful combined with an anomalous
        % distortion already applied to that cell (see run_perturbed.m).
        g.c = s*dem_field_sqrt_for_cells(a.x,a.s,cells,ramp);

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

    otherwise
        error('unknown PERTURBATION.kind %s', PERTURBATION.kind);
end
end

function r = perturbation_ramp_factor()
global PERTURBATION
global t
if isempty(t); r = 0; return; end
w = 0;
onset = 1;
if isfield(PERTURBATION,'ramp_w'); w = PERTURBATION.ramp_w; end
if isfield(PERTURBATION,'ramp_onset_bin'); onset = PERTURBATION.ramp_onset_bin; end
if isfield(PERTURBATION,'n_bins'); nb = PERTURBATION.n_bins; else; nb = 32; end
bin = round(t*nb);
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
