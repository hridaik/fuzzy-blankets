function [mdp] = active_inference_bird_control(MDP,OPTION,W)

%__________________________________________________________________________
%
% Author: Domenico Maisto
%
%__________________________________________________________________________
    
    
    try T      = MDP(1).T;      catch,  T      = size(MDP(1).V,1); end
    try OP     = OPTION;        catch,  OP     = []; end
    try w = W;                  catch,  w      = zeros(1,T); end
    
    for m = 1:size(MDP,2)
        mMDP = MDP(m);
        for t = 1:T
            mMDP = active_inference_bird_control_t(t,mMDP,OP);
        end
        mdp(m) = mMDP;
    end
end

%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%% AUX. FUN. %%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%
%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%%

function [mdp] = active_inference_bird_control_t(t,MDP,OPTION)

%__________________________________________________________________________
%
% Author: Domenico Maisto
%
%__________________________________________________________________________

% set up and preliminaries
%==========================================================================

% options and precision defaults
%--------------------------------------------------------------------------

try        T             = MDP.T;               catch, T            = size(MDP.V,1); end
try        initialised   = OPTION.initialised;  catch, initialised  = 0;             end 
try        modality      = OPTION.modality;     catch, modality     = 'FE';          end  

% options
%--------------------------------------------------------------------------


if initialised == 0 && t==1
    mdp = initialiseMDP(MDP);
else
    mdp = MDP;
end



% set up figure if necessary
%--------------------------------------------------------------------------
try
if ~isequal(mdp.PLOT,0)
    if ishandle(mdp.PLOT)
        figure(mdp.PLOT); clf
        mdp.PLOT = 2;
    else
        spm_figure('GetWin','MDP'); clf
    end
end
catch
end

wt     = mdp.wt;                          % indices of allowable policies
V      = mdp.V(:,wt);

if t>1
    a = mdp.u(t-1);         % action
end


% solve
%==========================================================================
b      = mdp.alpha/mdp.g;                  % expected rate parameter

vFE = 0;
    
sq = cell(1,mdp.Nf);
for f = 1:mdp.Nf
    sq{f} = mdp.S{f}(:,t);   
end


% expectations of allowable policies (u) and current state (x)
%--------------------------------------------------
for f = 1:mdp.Nf

    v = zeros(mdp.Ns(f),1);

    % marginal likelihood over outcome factors
    %--------------------------------------------------
    for g = 1:mdp.Ng
        Ag = spm_dot(mdp.Au{g},sq,f); 
        v  = v + spm_log(Ag(mdp.o(g,t),:))';        
    end

    if (t > 1)
        % retain allowable policies (that are consistent with last action)
        %------------------------------------------------------------------
        j = ismember(V(t - 1,:),a);
        V = V(:,j);
        wt = wt(j);

        % update policy expectations
        %------------------------------------------------------------------
        mdp.ut(wt,t) = mdp.ut(wt,t - 1)/sum(mdp.ut(wt,t - 1));

        % update current state expectations
        %------------------------------------------------------------------
        mdp.X{f}(:,t) = spm_softmax(v + spm_log(mdp.B{f}(:,:,a)) * mdp.X{f}(:,t-1));

        vFE = vFE + mdp.X{f}(:,t)' * (spm_log(mdp.X{f}(:,t)) - v - spm_log(mdp.B{f}(:,:,a) * mdp.X{f}(:,t-1)));

    else
        % otherwise initialise expectations
        %------------------------------------------------------------------
        mdp.ut(:,t) = ones(mdp.Np,1)/mdp.Np;
        
        mdp.X{f}(:,t) = spm_softmax(v + mdp.lnD{f});

        vFE = vFE + mdp.X{f}(:,t)' * (spm_log(mdp.X{f}(:,t)) - v - mdp.lnD{f});
    end
end

% value of policies (G)
%======================================================================
G     = zeros(size(V,2),1);

%test epistemic value
Hm=zeros(size(V,2),2);
%
for k = 1:size(V,2)

    % path integral of expected free energy
    %------------------------------------------------------------------
    x = cell(mdp.Nf,1);
    for f = 1:mdp.Nf
        x{f}    = mdp.X{f}(:,t);
    end
    
    for j = t:T 

         % transition probaility from current state
        %--------------------------------------------------------------
        for f = 1:mdp.Nf   
            x{f} = mdp.B{f}(:,:,V(j,k)) * x{f};
            
            mdp.xt{f}(:,j,k) = x{f};                % hidden state belief expected according to the k-th policy
        end

        % predicted entropy and divergence
        %--------------------------------------------------------------
        for g = 1:mdp.Ng 
            switch modality
                case{'FE'}
                    Hu = sum(mdp.A{g}{V(j,k)} .* mdp.lnA{g}{V(j,k)});
                    H = spm_dot(Hu,x);
                case{'KL'}
                    H = 0;
                otherwise
                    disp(['unkown OPTION modality: ' modality]);
            end
            
            qo   = spm_dot(mdp.A{g}{V(j,k)},x);
            G(k)    = G(k) + H + (mdp.lnC{g} - spm_log(qo))'* qo;       
            
        end
    end
    %
    mdp.G(wt(k),t) = G(k);              
end

    
% Variational iterations (assuming precise inference about past action)
%======================================================================

for i = 1:mdp.N

    % policy (u)
    %------------------------------------------------------------------
    mdp.ut(wt,t) = spm_softmax(mdp.W(t)*G);

    % precision (W)
    %------------------------------------------------------------------
    if isfield(MDP,'w')
        mdp.W(t) = MDP.w;
    else
        b    = mdp.lambda*b + (1 - mdp.lambda)*(mdp.beta - mdp.ut(wt,t)'*G);
        mdp.W(t) = mdp.alpha/b;
    end


    % simulated dopamine responses (precision as each iteration)
    %------------------------------------------------------------------
    mdp.gamma(i,t) = mdp.W(t);

end

% Variational Free Energy
%------------------------------------------------------------------
mdp.vFE = vFE + mdp.ut(:,t)'*(spm_log(mdp.ut(:,t)) -...
                mdp.gamma(mdp.N,t)*G) +...
                b*mdp.gamma(mdp.N,t) + ...
                mdp.alpha*(spm_log(mdp.alpha)-spm_log(mdp.gamma(mdp.N,t))-spm_log(b)-1);


% posterior expectations (control)
%======================================================================
for j = 1:mdp.Nu
    for k = t:T
        mdp.P(j,k) = sum(mdp.ut(wt(ismember(V(k,:),j)),t));
    end
end

% next action (the action that minimises expected free energy)
%------------------------------------------------------------------

try
    a = find(rand < cumsum(mdp.P(:,t)),1);
catch
    error('there are no more allowable policies')
end


% save action
%------------------------------------------------------------------
mdp.U(a,t) = 1;
mdp.u(t)   = a;


% sampling of next state (outcome)
%======================================================================
if t < T

    % next sampled state
    %------------------------------------------------------------------
    st=zeros(mdp.Nf,1);

    for f = 1:mdp.Nf
        try
            st(f) = find(rand < cumsum(mdp.BB{f}(:,mdp.s(f,t),a)),1);
        catch
            st(f) = find(rand < cumsum(mdp.B{f}(:,mdp.s(f,t),a)),1);
        end
        mdp.S{f}(st(f),t + 1) = 1;
        mdp.s(f,t+1) = st(f);
    end

    
    % next obsverved state
    %------------------------------------------------------------------
    ind   = num2cell(st(:));
    ot = zeros(mdp.Ng,1);
    for g = 1:mdp.Ng
        try
            mdp.pO{g}(:,t+1) = mdp.AAu{g}(:,ind{:});
        catch
            mdp.pO{g}(:,t+1) = mdp.Au{g}(:,ind{:});
        end
        ot(g)   = find(rand < cumsum(mdp.pO{g}(:,t+1)),1);
        mdp.O{g}(ot(g),t+1) = 1;
        mdp.o(g,t+1) = ot(g);
    end
end   

% plot
%======================================================================
if mdp.PLOT > 0

    % expected action
    %------------------------------------------------------------------
    subplot(3,1,3)
    %
    colormap('gray');
    imagesc(mdp.gamma);
    %
    title('Expected precision (confidence)','FontSize',14)
    xlabel('Time','FontSize',12)
    ylabel('Precision','FontSize',12)
    spm_axis tight
    drawnow
end  

% deconvolve to simulate dopamine responses
%--------------------------------------------------------------------------
K      = tril(toeplitz(exp(-((1:length(mdp.gamma(:,t))) - 1)'/mdp.N)));
da     = pinv(K)*mdp.gamma(:,t);
da(1)  = da(2);

% assemble results and place in NDP structure
%--------------------------------------------------------------------------

mdp.da = da;             % simulated dopamine responses (deconvolved)
mdp.wt = wt;

mdp.Hm = Hm;


end


% Auxiliary Functions
%==========================================================================

function A = spm_norm(A)
% normalisation of a probability transition matrix (columns)
% N.B.: it works just on matrices with positive elements and of size less than 6.
% of 5 factors

    for i = 1:size(A,2)
        for j = 1:size(A,3)
            for k = 1:size(A,4)
                for l = 1:size(A,5)
                    S = sum(A(:,i,j,k,l),1);
                    if S > 0
                        A(:,i,j,k,l) = A(:,i,j,k,l)/S;
                    else
                        A(:,i,j,k,l) = 1/size(A,1);
                    end
                end
            end
        end
    end
end


%--------------------------------------------------------------------------


function [X] = spm_dot(X,x,i)
% Multidimensional dot (inner) product
% FORMAT [Y] = spm_dot(X,x,[DIM])
%
% X   - numeric array
% x   - cell array of numeric vectors
% DIM - dimensions to omit (asumes ndims(X) = numel(x))
%
% Y  - inner product obtained by summing the products of X and x along DIM
%
% If DIM is not specified the leading dimensions of X are omitted.
% If x is a vector the inner product is over the leading dimension of X
%
% See also: spm_cross
%__________________________________________________________________________
% Copyright (C) 2015 Wellcome Trust Centre for Neuroimaging

% Karl Friston
% $Id: spm_dot.m 7314 2018-05-19 10:13:25Z karl $

% initialise dimensions
%--------------------------------------------------------------------------
if iscell(x)
    DIM = (1:numel(x)) + ndims(X) - numel(x);
else
    DIM = 1;
    x   = {x};
end

% omit dimensions specified
%--------------------------------------------------------------------------
if nargin > 2
    DIM(i) = [];
    x(i)   = [];
end

% inner product using recursive summation (and bsxfun)
%--------------------------------------------------------------------------
for d = 1:numel(x)
    s         = ones(1,ndims(X));
    s(DIM(d)) = numel(x{d});
    X         = bsxfun(@times,X,reshape(full(x{d}),s));
    X         = sum(X,DIM(d));
end

% eliminate singleton dimensions
%--------------------------------------------------------------------------
X = squeeze(X);

return

% NB: alternative scheme using outer product
%==========================================================================

% outer product and sum
%--------------------------------------------------------------------------
% x      = spm_cross(x);
% s      = ones(1,ndims(X));
% S      = size(X);
% s(DIM) = S(DIM);
% x      = reshape(full(x),s);
% X      = bsxfun(@times,X,x);
% for d  = 1:numel(DIM)
%     X  = sum(X,DIM(d));
% end
% X      = squeeze(X);
end

%--------------------------------------------------------------------------

function [Y] = spm_cross(X,x,varargin)
% Multidimensional cross (outer) product
% FORMAT [Y] = spm_cross(X,x)
% FORMAT [Y] = spm_cross(X)
%
% X  - numeric array
% x  - numeric array
%
% Y  - outer product
%
% See also: spm_dot
%__________________________________________________________________________
% Copyright (C) 2015 Wellcome Trust Centre for Neuroimaging

% Karl Friston
% $Id: spm_cross.m 7527 2019-02-06 19:12:56Z karl $

% handle single inputs
%--------------------------------------------------------------------------
if nargin < 2
    if isnumeric(X)
        Y = X;
    else
        Y = spm_cross(X{:});
    end
    return
end

% handle cell arrays
%--------------------------------------------------------------------------
if iscell(X), X = spm_cross(X{:}); end
if iscell(x), x = spm_cross(x{:}); end

% outer product of first pair of arguments (using bsxfun)
%--------------------------------------------------------------------------
A = reshape(full(X),[size(X) ones(1,ndims(x))]);
B = reshape(full(x),[ones(1,ndims(X)) size(x)]);
Y = squeeze(bsxfun(@times,A,B));

% and handle remaining arguments
%--------------------------------------------------------------------------
for i = 1:numel(varargin)
    Y = spm_cross(Y,varargin{i});
end

end
%--------------------------------------------------------------------------

function [y] = spm_softmax(x,k)
% softmax (e.g., neural transfer) function over columns
% FORMAT [y] = spm_softmax(x,k)
%
% x - numeric array array
% k - precision, sensitivity or inverse temperature (default k = 1)
%
% y  = exp(k*x)/sum(exp(k*x))
%
% NB: If supplied with a matrix this rotine will return the softmax
% function over colums - so that spm_softmax([x1,x2,..]) = [1,1,...]
 
%__________________________________________________________________________
% Copyright (C) 2008 Wellcome Trust Centre for Neuroimaging
 
% Karl Friston
% $Id: spm_softmax.m 7306 2018-05-07 13:42:02Z karl $
 
% apply
%--------------------------------------------------------------------------
if nargin > 1, x = k*x; end

x  = exp(bsxfun(@minus,x,max(x)));
y  = bsxfun(@rdivide,x,sum(x));
end


%--------------------------------------------------------------------------

function A = spm_log(A)
% log of numeric array plus a small constant
A  = log(A + 1e-16);
end

%--------------------------------------------------------------------------

function mdp = initialiseMDP(MDP)


% options and precision defaults
%--------------------------------------------------------------------------
try  mdp.PLOT   = MDP.PLOT;   catch, mdp.PLOT   = 0;             end
try  mdp.alpha  = MDP.alpha;  catch, mdp.alpha  = 8;             end
try  mdp.beta   = MDP.beta;   catch, mdp.beta   = 4;             end
try  mdp.eta    = MDP.eta;    catch, mdp.eta    = 1;             end
try  mdp.g      = MDP.g;      catch, mdp.g      = 1;             end
try  mdp.lambda = MDP.lambda; catch, mdp.lambda = 0;             end
try  mdp.N      = MDP.N;      catch, mdp.N      = 4;             end
try  T          = MDP.T;
     mdp.T      = T;          catch, try T      = size(MDP.V,1); 
                                         mdp.T  = T; catch, T=2; mdp.T = T; end
end  
try mdp.label   = MDP.label;  catch, mdp.label = [];             end

%%% used by flock_murmuration_N_escaping
try  mdp.t_post   = MDP.t_post;   catch, mdp.t_post   = [];             end
%%%




%%%%%
%
% generative model and initial states
%-----------------------------------------------
mdp.Ng = numel(MDP.A);            % number of outcome factors
mdp.Nf = numel(MDP.B);            % number of hidden-states factors
try                               % number of hidden controls; instruction depends on how B was defined
    MDP.B{1}{1};
    mdp.Nu = numel(MDP.B{1});         
catch
    mdp.Nu = size(MDP.B{1},3);         
end

try
    mdp.V  = MDP.V; 
catch
    % allowable (moving) policies using all allowable actions
    %------------------------------------------------------------------    
    %%%
    u = 1:mdp.Nu;
    % Create all possible permutations (with repetition) of actions u
    U = cell(T,1);                 % Preallocate a cell array
    [U{:}] = ndgrid(u);            % Create Nu grids of values
    V = cellfun(@(u){u(:)},U);     % Convert grids to column vectors
    mdp.V = [V{:}]';
end


mdp.Np = size(mdp.V,2);           % number of allowable policies


p0    = exp(-16);                 % smallest probability


% intial beliefs
%--------------------------------------------
for f = 1:mdp.Nf
    try
        mdp.d{f}    = MDP.d{f};
        mdp.D{f}    = spm_norm(MDP.d{f} + p0);
    catch
        try
            mdp.D{f} = spm_norm(MDP.D{f} + p0);
        catch
            mdp.D{f} = ones(mdp.Ns(f),1)/mdp.Ns(f);
        end
    end
    mdp.Ns(f) = numel(mdp.D{f});
    mdp.lnD{f} = spm_log(mdp.D{f});
end


% real state in the world
%------------------------------------------------

for f = 1:mdp.Nf
    try
        MDP.S{f};
        if size(MDP.S{f},1) ~= mdp.Ns(f)
            error('S and D are not consistent');
        end
    catch
        try 
            MDP.s;
        catch
            error('S vector not correctly specified');
        end
    end
end

% transition probabilities 
%-------------------------------------------------
try
    for f = 1:mdp.Nf  
        for u = 1:mdp.Nu
            try
                try
                    mdp.b{f}(:,:,u)   = MDP.b{f}{u};
                    mdp.B{f}(:,:,u)   = spm_norm(MDP.b{f}{u} + p0);         % normalise
                    try
                        mdp.BB{f}(:,:,u)   = spm_norm(MDP.B{f}{u} + p0);
                    catch
                        error('B needs to be defined when b is defined');
                    end
                catch
                    mdp.B{f}(:,:,u)   = spm_norm(MDP.B{f}{u} + p0); 
                end
            catch
                try
                    mdp.b{f}(:,:,u)   = MDP.b{f}(:,:,u);
                    mdp.B{f}(:,:,u)   = spm_norm(MDP.b{f}(:,:,u) + p0);
                    try
                        mdp.BB{f}(:,:,u)   = spm_norm(MDP.B{f}(:,:,u) + p0);
                    catch
                        error('B needs to be defined when b is defined');
                    end
                catch
                    mdp.B{f}(:,:,u)   = spm_norm(MDP.B{f}(:,:,u) + p0);
                end
            end
        end
    end
catch
    error('B or b matrix not correctly specified');
end


% likelihood model (for a partially observed MDP implicit in G)
%--------------------------------------------------------------------------
try
    for g = 1:mdp.Ng
        if iscell(MDP.A{g})   
            Au = zeros(size(MDP.A{g}{1},1),size(MDP.A{g}{1},2));
            try
                AAu = zeros(size(MDP.a{g}{1},1),size(MDP.a{g}{1},2));
            catch
            end
            for u = 1:mdp.Nu
                if size(MDP.C{g},1)>size(MDP.A{g}{u},1) || ...
                            size(MDP.C{g},1)<size(MDP.A{g}{u},1)
                    error('A and C are not consistent');
                end
                for f = 1 : mdp.Nf
                    if size(MDP.A{g}{u},f+1) ~= mdp.Ns(f)
                        error('A and D are not consistent');
                    end
                end 
                try
                    mdp.a{g}{u} = MDP.a{g}{u};
                    mdp.A{g}{u} = spm_norm(MDP.a{g}{u} + p0);
                    Au = Au + MDP.a{g}{u};
                    try
                        mdp.AA{g}{u} = spm_norm(MDP.A{g}{u} + p0);
                        AAu          = AAu + MDP.A{g}{u};  
                    catch
                        error('A needs to be defined when a is defined');
                    end
                catch
                    mdp.A{g}{u} = spm_norm(MDP.A{g}{u} + p0);
                    Au          = Au + MDP.A{g}{u};  
                end
                mdp.lnA{g}{u} = spm_log(mdp.A{g}{u});                
            end
            mdp.Au{g} = spm_norm(Au + p0);
            mdp.No(g) = size(mdp.A{g}{1},1);                          
            try
                mdp.AAu{g} = spm_norm(AAu{g} + p0);
            catch
                %mdp.AAu{g} = mdp.Au{g};
            end

        else                                            
            Au = zeros(size(MDP.A{g},1),size(MDP.A{g},2));
            try
                AAu = zeros(size(MDP.a{g},1),size(MDP.a{g},2));
            catch
            end
            for u = 1:mdp.Nu              
                try
                    mdp.a{g}{u} = MDP.a{g};
                    mdp.A{g}{u} = spm_norm(MDP.a{g} + p0); 
                    Au          = Au + MDP.a{g};
                    try
                        mdp.AA{g}{u} = spm_norm(MDP.A{g} + p0);
                        AAu          = AAu + MDP.A{g}; 
                    catch
                        error('A needs to be defined when a is defined');
                    end
                catch
                    mdp.A{g}{u} = spm_norm(MDP.A{g} + p0);
                    Au          = Au + MDP.A{g};
                end
                mdp.lnA{g}{u} = spm_log(mdp.A{g}{u});
            end

            mdp.Au{g} = spm_norm(Au + p0);
            mdp.No(g) = size(mdp.A{g}{1},1);
            try
                mdp.AAu{g} = spm_norm(AAu + p0);
            catch
                %mdp.AAu{g} = spm_norm(mdp.Nu*mdp.A{g}{1});
            end
        end
    end
catch
    error('A or a matrix not correctly specified');
end



% future outcomes probabilities (priors)
%--------------------------------------------------------------------------
try
    for g = 1:mdp.Ng
        if size(MDP.C{g},1) ~= size(mdp.A{g}{u},1)
            error('A and C are not consistent');
        end
        try 
            mdp.c{g}     = MDP.c{g};
            mdp.C{g}     = spm_norm(MDP.c{g} + p0);
        catch
            mdp.C{g}     = spm_norm(MDP.C{g} + p0);
        end
        mdp.lnC{g}   = spm_log(mdp.C{g});
    end
catch
    error('C or c vector not correctly specified');
end
%
% sanity check for A and C
for g = 1:mdp.Ng
    for u = 1:mdp.Nu
        try           
            if size(mdp.A{g}{u},1) ~= size(mdp.C{g},1)
                error('A and C (a and c) are not consinstently defined')
            end            
        catch
            error('A and C (a and c) not consinstently defined')               
        end                
    end
end


% initial states and outcomes 
%------------------------------------------------

try
    mdp.s = MDP.s;
    s = cell(1,mdp.Nf);
    for f = 1:mdp.Nf
        mdp.S{f}  = sparse(MDP.s(f,1),1,1,mdp.Ns(f),T); 
        s{f} = mdp.s(f,1);
        mdp.X{f}  = zeros(mdp.Ns(f),T);                       
        mdp.xt{f}  = zeros(mdp.Ns(f),T,mdp.Np);
    end
catch
    s = cell(1,mdp.Nf);
    mdp.s = zeros(mdp.Nf,T);
    for f = 1:mdp.Nf
        mdp.S{f}  = sparse(find(MDP.S{f}(:,1)),1,1,mdp.Ns(f),T);   % states sampled
        s{f}      = find(MDP.S{f}(:,1));
        mdp.s(f,1)= s{f};
        mdp.X{f}  = zeros(mdp.Ns(f),T);      % expectations of hidden states
        mdp.xt{f}  = zeros(mdp.Ns(f),T,mdp.Np);
    end
end

try 
    mdp.o = MDP.o;
    for g = 1:mdp.Ng 
        mdp.O{g}  = sparse(MDP.o(g,1),1,1,mdp.No(g),T);    % states observed (1 in K vector)
        mdp.pO{g} = mdp.O{g};
    end
catch    
    mdp.o = zeros(mdp.Ng,T);
    for g = 1:mdp.Ng 
        mdp.pO{g} = zeros(mdp.No(g),T);                       
        mdp.pO{g}(:,1) = mdp.Au{g}(:,s{:});                   % outcome initial distribution
        [~,q]  = max(mdp.pO{g}(:,1));                         % index observation with max probability     
        mdp.O{g}  = sparse(q,1,1,mdp.No(g),T);                % states observed (1 in K vector)
        mdp.o(g,1)= q;
    end
end

mdp.U      = zeros(mdp.Nu,T);                             % action selected (1 in K vector) 
mdp.u      = zeros(1,T);
mdp.P      = zeros(mdp.Nu,T);                             % posterior beliefs about control
mdp.W      = zeros(1,T);                                  % posterior precision
mdp.gamma  = zeros(mdp.N,mdp.T); 
mdp.ut     = zeros(mdp.Np,T);                             % expectations of hidden states
mdp.wt     = 1:mdp.Np;

mdp.G      = zeros(mdp.Np,T);                             % (negative) expected free energy 
                                                          % per policy and for each time.
                                                          


end



%==========================================================================
%EOF


