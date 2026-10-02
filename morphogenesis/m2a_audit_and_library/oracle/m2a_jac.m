function m2a_jac(cfgfile)
% One-bin map and its Jacobian over the full continuation state x = [beliefs v (64); belief velocity (64); action a (48); previous action (48)]
% by central finite differences (two step sizes), around the state in cfg.cont_file. Perturbation events/prec as in m2a_run.
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

cont.qu = cont.qu; cont.pu = cont.pu;
N1 = 1;
DEM.C = zeros(1,N1); DEM.U = zeros(n*n,N1); M2A.N = N1;
if isfield(cfg,'prec') && ~isempty(cfg.prec); DEM.prec = cfg.prec; DEM.prec.t_off = M2A.t_off; end
x0 = [full(cont.qu.v{1}); full(cont.qu.v{2}); full(cont.qu.a{1}); full(cont.Ahist(:,end))];
nx0 = numel(x0); steps = cfg.steps(:)';
f0 = onebin(DEM, cont, x0);
J = zeros(nx0, nx0, numel(steps));
for si = 1:numel(steps)
    h = steps(si);
    for k = 1:nx0
        xp = x0; xm = x0; xp(k) = xp(k) + h; xm(k) = xm(k) - h;
        J(:,k,si) = (onebin(DEM, cont, xp) - onebin(DEM, cont, xm))/(2*h);
    end
end
residual = f0 - x0;
save('-v7', cfg.out, 'J', 'steps', 'x0', 'f0', 'residual');
end
function y = onebin(DEM, cont, x)
c = cont;
c.qu.v{1} = x(1:64); c.qu.v{2} = x(65:128); c.qu.a{1} = x(129:176); c.Ahist = x(177:224);
DEM.cont = c;
DEM = spm_ADEM_m2a(DEM);
o = DEM.cont_out;
y = [full(o.qu.v{1}); full(o.qu.v{2}); full(o.qu.a{1}); full(o.Ahist(:,end))];
end
