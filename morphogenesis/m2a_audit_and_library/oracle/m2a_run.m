function m2a_run(cfgfile)
% M2A simulation driver. Engine: spm_ADEM (cfg.engine='spm') or its state-exporting copy spm_ADEM_m2a ('m2a').
% cfg: L, N (bins in THIS segment), seed (initial beliefs draw), v0, ax0, as0,
%   ramp_mode ('N' legacy v1 | 'abs' v2 absolute clock | 'const'), ramp_ref (=T_dev), t_off (bins already elapsed),
%   events (absolute-bin onsets), GV1 (process-noise precision G(1).V, default exp(16) = no noise),
%   noise_seed, noise_horizon (total bins H; noise drawn for the whole horizon so segments share one realisation),
%   cont_file (previous segment output; continue its state), engine, out.
global M2A t
clear global t
S = load(cfgfile); cfg = S.cfg;
% NB: scipy.io.savemat writes Python ints as int64 -> Octave integer arithmetic (silent rounding!). Cast.
for f = fieldnames(cfg)'; if isnumeric(cfg.(f{1})); cfg.(f{1}) = double(cfg.(f{1})); end; end
L = cfg.L; N = cfg.N; seed = cfg.seed;
engine = 'spm'; if isfield(cfg,'engine'); engine = cfg.engine; end
M2A = struct('ramp_mode','N','ramp_const',0.6,'ramp_ref',512,'t_off',0,'N',N,'events',[]);
fn = {'ramp_mode','ramp_const','ramp_ref','t_off'};
for k = 1:numel(fn); if isfield(cfg,fn{k}) && ~isempty(cfg.(fn{k})); M2A.(fn{k}) = cfg.(fn{k}); end; end
if isfield(cfg,'events') && ~isempty(cfg.events); M2A.events = cfg.events; end
cont = [];
if isfield(cfg,'cont_file') && ~isempty(cfg.cont_file)
    C0 = load(cfg.cont_file); cont = C0.cont_out; M2A.t_off = double(C0.b_end);
    if isfield(cfg,'dt') && ~isempty(cfg.dt); M2A.t_off = double(C0.b_end)/cfg.dt; end   % sub-stepped continuation: absolute time in sub-bins
    % ABLATION controls (R0.2 diagnostics only): drop one carried quantity to show it is needed
    if isfield(cfg,'ablate')
        ab = char(cfg.ablate);
        switch ab
            case 'Ahist'; cont.Ahist = zeros(size(cont.Ahist,1),0);
            case 'pu';    for k = 1:numel(cont.pu.v); cont.pu.v{k} = 0*cont.pu.v{k}; cont.pu.x{k} = 0*cont.pu.x{k}; end
            case 'qu_hi'; for k = 2:numel(cont.qu.x); cont.qu.x{k} = 0*cont.qu.x{k}; end; for k = 2:numel(cont.qu.v); cont.qu.v{k} = 0*cont.qu.v{k}; end
            case 'qa';    cont.qu.a{1} = cont.Ahist(:,end);
            case 'qv0';   cont.qu.v{1} = cont.qu.v{1} + 1e-6;
        end
    end
end
% KICK (R3): instantaneous state change applied to the continued state (no ramp reset, no new development)
if isfield(cfg,'kick') && ~isempty(cont)
    kk = cfg.kick; qa = full(cont.qu.a{1}); Ah = full(cont.Ahist);
    switch char(kk.type)
        case 'pos';    d = kk.dpos(:); qa(1:16) = qa(1:16) + d; Ah(1:16,:) = Ah(1:16,:) + d;
        case 'sec';    qa(17:48) = kk.sec(:); Ah(17:48,:) = repmat(kk.sec(:),1,size(Ah,2));
        case 'belief'; cont.qu.v{1} = kk.v(:); for h = 2:numel(cont.qu.v); cont.qu.v{h} = 0*cont.qu.v{h}; end
        otherwise; error('kick type');
    end
    cont.qu.a{1} = qa; cont.Ahist = Ah;
end
rand('seed',seed); randn('seed',seed);
M(1).E.d = 1; M(1).E.n = 2; M(1).E.s = 1;
if isfield(cfg,'dt') && ~isempty(cfg.dt); M(1).E.dt = cfg.dt; end   % integration/sampling step (D2 sub-stepping; default 1 bin)
T = m2a_templates(L);
p(:,:,1) = T > 0; p(:,:,2) = T == 2 | T == 1; p(:,:,3) = T == 3 | T == 1; p(:,:,4) = T == 4;
[y,x] = find(p(:,:,1));
P.x = spm_detrend([x(:) y(:)])'/2;
n = size(P.x,2); m = size(p,3); j = find(p(:,:,1));
for i = 1:m; s = p(:,:,i); P.s(i,:) = s(j); end
P.s = double(P.s);
P.c = m2a_field(P.x,P.s);
if isfield(cfg,'v0') && ~isempty(cfg.v0); v = cfg.v0; else; v = randn(n,n)/8; end
g = m2a_Mg([],v,P);
a.x = g.x; a.s = g.s;
if isfield(cfg,'ax0') && ~isempty(cfg.ax0); a.x = cfg.ax0; end
if isfield(cfg,'as0') && ~isempty(cfg.as0); a.s = cfg.as0; end
R = spm_cat({kron(eye(n,n),ones(2,2)) []; [] kron(eye(n,n),ones(4,4)); kron(eye(n,n),ones(4,2)) kron(eye(n,n),ones(4,4))});
G(1).g = @(x,v,a,P) m2a_Gg(x,v,a,P);
G(1).v = m2a_Gg([],[],a,a); G(1).V = exp(16); G(1).U = exp(2); G(1).R = R; G(1).pE = a;
if isfield(cfg,'GV1') && ~isempty(cfg.GV1); G(1).V = cfg.GV1; end
G(2).a = spm_vec(a); G(2).v = 0; G(2).V = exp(16);
M(1).g = @(x,v,P) m2a_Mg([],v,P); M(1).v = g; M(1).pE = P;
M(1).V = exp(3); if isfield(cfg,'V1') && ~isempty(cfg.V1); M(1).V = cfg.V1; end   % sensory precision (Pio-Lopez-type manipulation)
M(2).v = v; M(2).V = exp(-2);
DEM.M = M; DEM.G = G; DEM.C = zeros(1,N); DEM.U = zeros(n*n,N); DEM.db = 0;
% process noise: one realisation over the whole horizon, shared by all segments
if isfield(cfg,'noise_horizon') && cfg.noise_horizon > 0
    nz = 0; if isfield(cfg,'noise_seed'); nz = cfg.noise_seed; end
    Dp = spm_ADEM_set(DEM); Dp.G(1).E.n = Dp.M(1).E.n; Dp.G(1).E.d = Dp.M(1).E.n;
    rand('seed',nz); randn('seed',nz);
    [z,w] = spm_DEM_z(Dp.G, cfg.noise_horizon);
    C1 = struct(); C1.Zfull = spm_cat(z(:)); C1.Wfull = spm_cat(w(:)); C1.b0 = M2A.t_off;
    if isempty(cont); cont = C1; else; cont.Zfull = C1.Zfull; cont.Wfull = C1.Wfull; cont.b0 = M2A.t_off; end
    DEM.noise_horizon = cfg.noise_horizon;
end
if ~isempty(cont); DEM.cont = cont; end
if isfield(cfg,'prec') && ~isempty(cfg.prec); DEM.prec = cfg.prec; DEM.prec.t_off = M2A.t_off; end   % sensory-precision schedule (F, onset, off, w; absolute bins)
if isfield(cfg,'seed_noise_reset') && cfg.seed_noise_reset; rand('seed',seed); randn('seed',seed); end
tic;
if strcmp(engine,'m2a'); DEM = spm_ADEM_m2a(DEM); else; DEM = spm_ADEM(DEM); end
elapsed = toc;
positions = DEM.qU.a{2}(1:2*n,:); secretion = DEM.qU.a{2}(2*n+1:6*n,:);
v_expect = DEM.qU.v{2}; pred_err_1 = DEM.qU.z{1}; pred_err_2 = DEM.qU.z{2};
free_energy_J = DEM.J; target_x = P.x; target_s = P.s;
v_initial = v; b_end = M2A.t_off + N;
if isfield(cfg,'dt') && ~isempty(cfg.dt); b_end = b_end*cfg.dt; end   % stored in BIN units (time units of the model)
if strcmp(engine,'m2a')
    cont_out = DEM.cont_out;
    if isfield(DEM,'noise_horizon'); cont_out.Zfull = cont.Zfull; cont_out.Wfull = cont.Wfull; end
    save('-v7', cfg.out, 'positions','secretion','v_expect','pred_err_1','pred_err_2','free_energy_J','target_x','target_s','v_initial','elapsed','N','seed','n','b_end','cont_out');
else
    save('-v7', cfg.out, 'positions','secretion','v_expect','pred_err_1','pred_err_2','free_energy_J','target_x','target_s','v_initial','elapsed','N','seed','n','b_end');
end
end
