function [s, bin] = m2a_ramp(tt)
% Developmental sensitivity ramp. Default mode reproduces SPM's s = 1-exp(-2t), t = bin/N,
% bit-for-bit. Optional modes (set via global M2A.ramp_mode):
%   'N'     : s = 1-exp(-2*t)                     (default; M1/SPM behaviour)
%   'abs'   : s = 1-exp(-2*(bin_abs)/ramp_ref)    bin_abs = t_off + t*N ; ramp_ref=512
%             (the N=512 ramp schedule in ABSOLUTE bins: continues beyond bin 512 and
%              is preserved across restarts from a stored state)
%   'const' : s = ramp_const                      (frozen ramp, audit control)
global M2A
if isempty(tt); s = 0; bin = 0; return; end
mode = 'N'; if ~isempty(M2A) && isfield(M2A,'ramp_mode'); mode = M2A.ramp_mode; end
Nb = 512; if ~isempty(M2A) && isfield(M2A,'N'); Nb = M2A.N; end
t0 = 0; if ~isempty(M2A) && isfield(M2A,'t_off'); t0 = M2A.t_off; end
bin = round(tt*Nb) + t0;   % ABSOLUTE bin (t_off = bins already elapsed in earlier segments)
switch mode
    case 'N';     s = (1 - exp(-tt*2));
    case 'abs';   s = 1 - exp(-2*bin/M2A.ramp_ref);   % v2 clock: s(b) = 1-exp(-2 b/T_dev), independent of N
    case 'const'; s = M2A.ramp_const;
    otherwise; error('ramp mode');
end
end
