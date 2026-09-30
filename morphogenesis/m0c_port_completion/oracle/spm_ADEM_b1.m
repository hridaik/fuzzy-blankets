function [DEM] = spm_ADEM_b1(DEM, dumpfile)
% PATCHED COPY of spm_ADEM.m (SPM12, commit 03ac9473c, sourced via
% morphogenesis/m0b_reference_port/sources/spm12/spm_ADEM.m) for Part B1/B2
% instrumentation ONLY. Diff vs. original: renamed signature +
% dumpfile arg; one added block right after `[pu,dg,df] = spm_ADEM_diff(G,pu);`
% inside the D-step loop, dumping pu.v{1,2,3} for bins 1-3 (both the value
% used as INPUT, captured just before the call, and the value produced as
% OUTPUT, just after). No other line changed. See PORT_DESIGN_UPDATE.md.
if nargin < 2; dumpfile = 'dstep_b1_dump.mat'; end

DEM   = spm_ADEM_set(DEM);
M     = DEM.M;
G     = DEM.G;
C     = DEM.C;
U     = DEM.U;

try, db = DEM.db; catch, db = 1; end
if db, Fdem = spm_figure('GetWin','DEM'); end

G(1).E.n = M(1).E.n;
G(1).E.d = M(1).E.n;

d    = M(1).E.d + 1;
n    = M(1).E.n + 1;
s    = M(1).E.s;

nY   = size(C,2);
nl   = size(M,2);
nv   = sum(spm_vec(M.m));
nx   = sum(spm_vec(M.n));
ny   = M(1).l;
nc   = M(end).l;
nu   = nv*d + nx*n;

gr   = sum(spm_vec(G.l));
ga   = sum(spm_vec(G.k));
gx   = sum(spm_vec(G.n));
gy   = G(1).l;
na   = ga;

try, nE = M(1).E.nE; catch, nE = 16; end
try, nM = M(1).E.nM; catch, nM = 8;  end
try, dt = M(1).E.dt; catch, dt = 1;  end

te = 2;
global t

iV    = spm_DEM_R(n,s);
iG    = spm_DEM_R(n,s);

try
    nG = norm(iG);
    iG = iG*spm_DEM_T(n,-M(1).Ta);
    iG = iG*nG/norm(iG);
end
try
    Ty = spm_DEM_T(n,-M(1).Ty);
    Ty = kron(Ty,speye(ny,ny));
end

Q     = {};
for i = 1:nl
    q0{i,i} = sparse(M(i).l,M(i).l);
    r0{i,i} = sparse(M(i).n,M(i).n);
end
Q0    = kron(iV,spm_cat(q0));
R0    = kron(iV,spm_cat(r0));
for i = 1:nl
    for j = 1:length(M(i).Q)
        q          = q0;
        q{i,i}     = M(i).Q{j};
        Q{end + 1} = blkdiag(kron(iV,spm_cat(q)),R0);
    end
    for j = 1:length(M(i).R)
        q          = r0;
        q{i,i}     = M(i).R{j};
        Q{end + 1} = blkdiag(Q0,kron(iV,spm_cat(q)));
    end
end

Q0    = kron(iV,spm_cat(spm_diag({M.V})));
R0    = kron(iV,spm_cat(spm_diag({M.W})));
Qp    = blkdiag(Q0,R0);
nh    = length(Q);
iR    = [zeros(1,ny),ones(1,nv),ones(1,nx)];
iR    = kron(speye(n,n),diag(iR));

q0{1} = G(1).U;
Q0    = kron(iG,spm_cat(q0));
R0    = kron(iG,spm_cat(r0));
iG    = blkdiag(Q0,R0);

try
    R         = sparse(sum(spm_vec(G.l)),na);
    R(1:ny,:) = G(1).R;
    R         = kron(spm_speye(n,1,0),R);
catch
    R = 1;
end

try
    aP = G(1).aP;
catch
    aP = exp(-2);
end

xP    = spm_cat(spm_diag({M.xP}));
Px    = kron(iV(1:n,1:n),speye(nx,nx)*exp(-8) + xP);
Pv    = kron(iV(1:d,1:d),speye(nv,nv)*exp(-8));
Pa    = spm_speye(na,na)*aP;
Pu    = spm_cat(spm_diag({Px Pv}));

ph.h  = spm_vec({M.hE M.gE});
ph.c  = spm_cat(spm_diag({M.hC M.gC}));
qh.h  = ph.h;
qh.c  = ph.c;
ph.ic = spm_inv(ph.c);

pp.c  = cell(nl,nl);
qp.p  = cell(nl,1);
for i = 1:(nl - 1)
    qp.u{i}   = spm_svd(M(i).pC);
    M(i).p    = size(qp.u{i},2);
    qp.p{i}   = sparse(M(i).p,1);
    pp.c{i,i} = qp.u{i}'*M(i).pC*qp.u{i};
    try
        qp.e{i} = qp.p{i} + qp.u{i}'*(spm_vec(M(i).P) - spm_vec(M(i).pE));
    catch
        qp.e{i} = qp.p{i};
    end
end
Up    = spm_cat(spm_diag(qp.u));

np    = sum(spm_vec(M.p));
pp.c  = spm_cat(pp.c);
pp.ic = spm_inv(pp.c);

qp.e  = spm_vec(qp.e);
qp.c  = sparse(np,np);

qu.x      = cell(n,1);
qu.v      = cell(n,1);
qu.a      = cell(1,1);
qu.y      = cell(n,1);
qu.u      = cell(n,1);
pu.v      = cell(n,1);
pu.x      = cell(n,1);
pu.z      = cell(n,1);
pu.w      = cell(n,1);

[qu.x{:}] = deal(sparse(nx,1));
[qu.v{:}] = deal(sparse(nv,1));
[qu.a{:}] = deal(sparse(na,1));
[qu.y{:}] = deal(sparse(ny,1));
[qu.u{:}] = deal(sparse(nc,1));
[pu.v{:}] = deal(sparse(gr,1));
[pu.x{:}] = deal(sparse(gx,1));
[pu.z{:}] = deal(sparse(gr,1));
[pu.w{:}] = deal(sparse(gx,1));

qu.x{1}   = spm_vec({M(1:end - 1).x});
qu.v{1}   = spm_vec({M(1 + 1:end).v});
qu.a{1}   = spm_vec({G.a});
pu.x{1}   = spm_vec({G.x});
pu.v{1}   = spm_vec({G.v});

Dx    = kron(spm_speye(n,n,1),spm_speye(nx,nx,0));
Dv    = kron(spm_speye(d,d,1),spm_speye(nv,nv,0));
Dc    = kron(spm_speye(d,d,1),spm_speye(nc,nc,0));
Da    = kron(spm_speye(1,1,1),sparse(na,na));
Du    = spm_cat(spm_diag({Dx,Dv}));
Dq    = spm_cat(spm_diag({Dx,Dv,Dc,Da}));

Dx    = kron(spm_speye(n,n,1),spm_speye(gx,gx,0));
Dv    = kron(spm_speye(n,n,1),spm_speye(gr,gr,0));
Dp    = spm_cat(spm_diag({Dv,Dx,Dv,Dx}));
dfdw  = kron(speye(n,n),speye(gx,gx));
dydv  = kron(speye(n,n),speye(gy,gr));

dVdc  = sparse(d*nc,1);

dWdu  = sparse(nu,1);
dWduu = sparse(nu,nu);

if ~np && ~nh, nE = 1; end

[z,w]  = spm_DEM_z(G,nY);
z{end} = C + z{end};
a      = {G.a};
Z      = spm_cat(z(:));
W      = spm_cat(w(:));
A      = spm_cat(a(:));

DUMP = {};

F      = -Inf;
for iE = 1:nE

    tic; clear spm_DEM_eval

    dFdp  = zeros(np,1);
    dFdpp = zeros(np,np);
    EE    = sparse(0);
    ECE   = sparse(0);
    EiSE  = sparse(0);
    qp.ic = sparse(0);
    Hqu.c = sparse(0);

    iS    = Qp;
    for i = 1:nh
       iS = iS + Q{i}*exp(qh.h(i));
    end

    iP    = iR*iS*iR;

    try
        qu = qU(1);
        pu = pU(1);
    end

    for iY = 1:nY

        t      = iY/nY;

        try, A = spm_cat({qU.a qu.a}); end

        pu.z = spm_DEM_embed(Z,n,iY);
        pu.w = spm_DEM_embed(W,n,iY);
        pu.a = spm_DEM_embed(A,n,iY);
        qu.u = spm_DEM_embed(U,n,iY);

        % DUMP: capture pu.v BEFORE the recursion runs, for bins 1-3
        %==================================================================
        if iY <= 3
            rec.iY = iY;
            rec.pu_v_in = cellfun(@full, pu.v, 'UniformOutput', false);
            rec.pu_a_in = cellfun(@full, pu.a, 'UniformOutput', false);
            rec.pu_z_in = cellfun(@full, pu.z, 'UniformOutput', false);
        end

        [pu,dg,df] = spm_ADEM_diff(G,pu);

        if iY <= 3
            rec.pu_v_out = cellfun(@full, pu.v, 'UniformOutput', false);
            rec.dg_dv = full(dg.dv);
            rec.dg_da = full(dg.da);
            rec.dg_dx = full(dg.dx);
            DUMP{end+1} = rec;
        end

        for i = 1:n
            y       = spm_unvec(pu.v{i},{G.v});
            qu.y{i} = y{1};
        end

        try, qu.y = spm_unvec(Ty*spm_vec(qu.y),qu.y); end

        [E,dE] = spm_DEM_eval(M,qu,qp);

        qu.c   = spm_inv(dE.du'*iS*dE.du + Pu);
        pu.c   = spm_inv(dE.du'*iP*dE.du + Pu);
        Hqu.c  = Hqu.c + spm_logdet(qu.c);

        qE{iY} = E;
        qC{iY} = qu.c;
        pC{iY} = pu.c;
        qU(iY) = qu;
        pU(iY) = pu;

        if nh
            ECEu  = dE.du*qu.c*dE.du';
            ECEp  = dE.dp*qp.c*dE.dp';
        end

        if np
            for i = 1:nu
                CJp(:,i)   = spm_vec(qp.c*dE.dpu{i}'*iS);
                dEdpu(:,i) = spm_vec(dE.dpu{i}');
            end
            dWdu  = CJp'*spm_vec(dE.dp');
            dWduu = CJp'*dEdpu;
        end

        Dgda  = kron(spm_speye(n,1,1),dg.da);
        Dgdv  = kron(spm_speye(n,n,1),dg.dv);
        Dgdx  = kron(spm_speye(n,n,1),dg.dx);
        dfda  = kron(spm_speye(n,1,0),df.da);
        dfdv  = kron(spm_speye(n,n,0),df.dv);
        dfdx  = kron(spm_speye(n,n,0),df.dx);

        dgda  = kron(spm_speye(n,1,0),dg.da);
        dgdx  = kron(spm_speye(n,n,0),dg.dx);

        Dfdx  = 0;
        for i = 1:n
            Dfdx = Dfdx + kron(spm_speye(n,n,-i),df.dx^(i - 1));
        end

        dE.dv = dE.dy*dydv;
        dE.da = dE.dv*((dgda + dgdx*Dfdx*dfda).*R);

        dVdu  = -dE.du'*iS*E - Pu*spm_vec({qu.x{1:n} qu.v{1:d}}) - dWdu/2;
        dVda  = -dE.da'*iG*E - Pa*spm_vec( qu.a{1:1});

        dVduu = -dE.du'*iS*dE.du - Pu - dWduu/2 ;
        dVdaa = -dE.da'*iG*dE.da - Pa;
        dVduv = -dE.du'*iS*dE.dv;
        dVduc = -dE.du'*iS*dE.dc;
        dVdua = -dE.du'*iS*dE.da;
        dVdav = -dE.da'*iG*dE.dv;
        dVdau = -dE.da'*iG*dE.du;
        dVdac = -dE.da'*iG*dE.dc;

        p     = {pu.v{1:n} pu.x{1:n} pu.z{1:n} pu.w{1:n}};
        q     = {qu.x{1:n} qu.v{1:d} qu.u{1:d} qu.a{1:1}};
        u     = [p q];

        dFdu  = [                              Dp*spm_vec(p);
                 spm_vec({dVdu; dVdc; dVda}) + Dq*spm_vec(q)];

        dFduu = spm_cat(...
                {Dgdv  Dgdx Dv   []   []       []    Dgda;
                 dfdv  dfdx []   dfdw []       []    dfda;
                 []    []   Dv   []   []       []    [];
                 []    []   []   Dx   []       []    [];
                 dVduv []   []   []   Du+dVduu dVduc dVdua;
                 []    []   []   []   []       Dc    []
                 dVdav []   []   []   dVdau    dVdac dVdaa});

        du    = spm_dx(dFduu,dFdu,dt);
        u     = spm_unvec(spm_vec(u) + du,u);

        pu.v(1:n) = u((1:n));
        pu.x(1:n) = u((1:n) + n);
        qu.x(1:n) = u((1:n) + n + n + n + n);
        qu.v(1:d) = u((1:d) + n + n + n + n + n);
        qu.a(1:1) = u((1:1) + n + n + n + n + n + d + d);

        if iY <= 3
            DUMP{end}.pu_v_after_dx = cellfun(@full, pu.v, 'UniformOutput', false);
            DUMP{end}.qu_v_after_dx = cellfun(@full, qu.v, 'UniformOutput', false);
            DUMP{end}.qu_a_after_dx = cellfun(@full, qu.a, 'UniformOutput', false);
        end

        if nE == 1
            J(iY) = - trace(E'*iS*E)/2  ...
                    + spm_logdet(qu.c)  ...
                    + spm_logdet(iS)/2;
        end

    end

    break  % B1/B2 only needs bins 1-3; stop after first full pass
end

save('-v7', dumpfile, 'DUMP');
fprintf('saved %s (%d dump records)\n', dumpfile, numel(DUMP));
DEM.DUMP_ONLY = true;
end
